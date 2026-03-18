# Copyright (C) 2006-2007 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gettext import gettext as _
import logging

from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio

from sugar3.graphics import style
from sugar3.graphics import palettegroup

from jarabe.desktop.meshbox import MeshBox
from jarabe.desktop.homebox import HomeBox
from jarabe.desktop.homebackgroundbox import HomeBackgroundBox
from jarabe.desktop.groupbox import GroupBox
from jarabe.desktop.transitionbox import TransitionBox
from jarabe.desktop.viewtoolbar import ViewToolbar
from jarabe.model.shell import ShellModel
from jarabe.model import shell


_HOME_PAGE = 0
_GROUP_PAGE = 1
_MESH_PAGE = 2
_TRANSITION_PAGE = 3

_instance = None


class HomeWindow(Gtk.Window):

    def __init__(self):
        logging.debug('STARTUP: Loading the desktop window')
        Gtk.Window.__init__(self)

        self._active = False
        self._fully_obscured = True

        # GTK4: Use Display/Monitor API instead of Gdk.Screen
        display = Gdk.Display.get_default()
        monitor = display.get_monitors().get_item(0)
        geometry = monitor.get_geometry()
        self.set_default_size(geometry.width, geometry.height)

        monitor.connect('notify::geometry', self.__monitor_geometry_changed_cb)

        self._busy_count = 0
        self.busy()

        # GTK4: Use CSS for background instead of modify_bg
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(
            b"window { background-color: %s; }" %
            style.COLOR_WHITE.get_html().encode())
        self.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # GTK4: Use event controllers instead of add_events + connect
        key_controller = Gtk.EventControllerKey()
        key_controller.connect('key-pressed', self.__key_pressed_cb)
        key_controller.connect('key-released', self.__key_released_cb)
        self.add_controller(key_controller)

        self._box = HomeBackgroundBox()

        self._toolbar = ViewToolbar()
        self._box.prepend(self._toolbar)
        self._toolbar.set_visible(True)

        self._alert = None

        self._home_box = HomeBox(self._toolbar)
        self._box.append(self._home_box)
        self._home_box.set_hexpand(True)
        self._home_box.set_vexpand(True)
        self._home_box.set_visible(True)
        self._toolbar.show_view_buttons()

        # Loads the Gsettings value for activity 'resume-mode'
        setting = Gio.Settings.new('org.sugarlabs.user')
        self._resume_mode = setting.get_boolean('resume-activity')
        self._home_box.set_resume_mode(self._resume_mode)

        self._group_box = GroupBox(self._toolbar)
        self._mesh_box = MeshBox(self._toolbar)
        self._transition_box = TransitionBox()

        # GTK4: container.add → set_child
        self.set_child(self._box)
        self._box.set_visible(True)

        self._transition_box.connect('completed',
                                     self._transition_completed_cb)

        shell.get_model().zoom_level_changed.connect(
            self.__zoom_level_changed_cb)

        self._alt_timeout_sid = None
        self._current_view_widget = self._home_box

    def add_alert(self, alert):
        self._alert = alert
        self._show_alert()

    def remove_alert(self, alert):
        if alert == self._alert:
            self._box.remove(self._alert)
            self._alert = None

    def _show_alert(self):
        if self._alert:
            # GTK4: Insert after toolbar
            self._box.insert_child_after(self._alert, self._toolbar)

    def _hide_alert(self):
        if self._alert:
            self._box.remove(self._alert)

    def _deactivate_view(self, level):
        group = palettegroup.get_group('default')
        group.popdown()
        if level == ShellModel.ZOOM_HOME:
            self._home_box.suspend()
        elif level == ShellModel.ZOOM_MESH:
            self._mesh_box.suspend()

    def __monitor_geometry_changed_cb(self, monitor, pspec):
        geometry = monitor.get_geometry()
        self.set_default_size(geometry.width, geometry.height)

    def _activate_view(self, level):
        if level == ShellModel.ZOOM_HOME:
            self._home_box.resume()
        elif level == ShellModel.ZOOM_MESH:
            self._mesh_box.resume()

    def __key_pressed_cb(self, controller, keyval, keycode, state):
        if self.__is_alt(keyval, state) and not self._alt_timeout_sid:
            self._home_box.set_resume_mode(not self._resume_mode)
            self._alt_timeout_sid = GLib.timeout_add(100,
                                                     self.__alt_timeout_cb)

        if not self._toolbar.search_entry.props.has_focus:
            self._toolbar.search_entry.grab_focus()

        return False

    def __key_released_cb(self, controller, keyval, keycode, state):
        if self.__is_alt(keyval, state) and self._alt_timeout_sid:
            self._home_box.set_resume_mode(self._resume_mode)
            GLib.source_remove(self._alt_timeout_sid)
            self._alt_timeout_sid = None

        return False

    def __is_alt(self, keyval, state):
        # When shift is on, <ALT> becomes <META>
        shift = (state & Gdk.ModifierType.SHIFT_MASK) != 0
        return keyval in [Gdk.KEY_Alt_L, Gdk.KEY_Alt_R] or \
            keyval in [Gdk.KEY_Meta_L, Gdk.KEY_Meta_R] and shift

    def __alt_timeout_cb(self):
        # GTK4: Use seat to get pointer state
        display = Gdk.Display.get_default()
        seat = display.get_default_seat()
        pointer = seat.get_logical_device(Gdk.SeatCapabilities.POINTER)
        if pointer:
            # Check if Alt is still held
            # In GTK4, we can check via the keyboard state
            pass

        self._home_box.set_resume_mode(self._resume_mode)

        if self._alt_timeout_sid:
            GLib.source_remove(self._alt_timeout_sid)
            self._alt_timeout_sid = None

        return False

    def __zoom_level_changed_cb(self, **kwargs):
        old_level = kwargs['old_level']
        new_level = kwargs['new_level']

        self._deactivate_view(old_level)
        self._activate_view(new_level)

        if old_level != ShellModel.ZOOM_ACTIVITY and \
           new_level != ShellModel.ZOOM_ACTIVITY:
            self._hide_alert()
            # GTK4: Remove current view widget
            if self._current_view_widget:
                self._box.remove(self._current_view_widget)

            self._box.append(self._transition_box)
            self._transition_box.set_hexpand(True)
            self._transition_box.set_vexpand(True)
            self._transition_box.set_visible(True)
            self._current_view_widget = self._transition_box

            if new_level == ShellModel.ZOOM_HOME:
                end_size = style.XLARGE_ICON_SIZE
            elif new_level == ShellModel.ZOOM_GROUP:
                end_size = style.LARGE_ICON_SIZE
            elif new_level == ShellModel.ZOOM_MESH:
                end_size = style.STANDARD_ICON_SIZE

            if old_level == ShellModel.ZOOM_HOME:
                start_size = style.XLARGE_ICON_SIZE
            elif old_level == ShellModel.ZOOM_GROUP:
                start_size = style.LARGE_ICON_SIZE
            elif old_level == ShellModel.ZOOM_MESH:
                start_size = style.STANDARD_ICON_SIZE

            self._transition_box.start_transition(start_size, end_size)
        else:
            self._update_view(new_level)

    def _transition_completed_cb(self, transition_box):
        self._update_view(shell.get_model().zoom_level)

    def _update_view(self, level):
        if level == ShellModel.ZOOM_ACTIVITY:
            return

        self._hide_alert()
        # GTK4: Remove current view widget
        if self._current_view_widget:
            self._box.remove(self._current_view_widget)

        if level == ShellModel.ZOOM_HOME:
            self._box.append(self._home_box)
            self._home_box.set_hexpand(True)
            self._home_box.set_vexpand(True)
            self._home_box.set_visible(True)
            self._current_view_widget = self._home_box
            self._toolbar.clear_query()
            self._toolbar.set_placeholder_text_for_view(_('Home'))
            self._toolbar.show_view_buttons()
        elif level == ShellModel.ZOOM_GROUP:
            self._box.append(self._group_box)
            self._group_box.set_hexpand(True)
            self._group_box.set_vexpand(True)
            self._group_box.set_visible(True)
            self._current_view_widget = self._group_box
            self._toolbar.clear_query()
            self._toolbar.set_placeholder_text_for_view(_('Group'))
            self._toolbar.hide_view_buttons()
        elif level == ShellModel.ZOOM_MESH:
            self._box.append(self._mesh_box)
            self._mesh_box.set_hexpand(True)
            self._mesh_box.set_vexpand(True)
            self._mesh_box.set_visible(True)
            self._current_view_widget = self._mesh_box
            self._toolbar.clear_query()
            self._toolbar.set_placeholder_text_for_view(_('Neighborhood'))
            self._toolbar.hide_view_buttons()
        self._show_alert()

    def get_home_box(self):
        return self._home_box

    def busy(self):
        if self._busy_count == 0:
            self._old_cursor = self.get_cursor()
            self.set_cursor(Gdk.Cursor.new_from_name('wait'))
        self._busy_count += 1

    def unbusy(self):
        self._busy_count -= 1
        if self._busy_count == 0:
            self.set_cursor(self._old_cursor)

    def show(self):
        self.present()


def get_instance():
    global _instance
    if not _instance:
        _instance = HomeWindow()
    return _instance
