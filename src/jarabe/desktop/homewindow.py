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
import os
import logging

from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio

from sugar4.graphics import style
from sugar4.graphics import palettegroup

from jarabe.desktop.meshbox import MeshBox
from jarabe.desktop.homebox import HomeBox
from jarabe.desktop.homebackgroundbox import HomeBackgroundBox
from jarabe.desktop.groupbox import GroupBox
from jarabe.desktop.transitionbox import TransitionBox
from jarabe.desktop.viewtoolbar import ViewToolbar
from jarabe.model.shell import ShellModel
from jarabe.model import shell
from jarabe import config


_HOME_PAGE = 0
_GROUP_PAGE = 1
_MESH_PAGE = 2
_TRANSITION_PAGE = 3

_instance = None


def _get_children(box):
    """Helper to iterate children of a Gtk.Box in GTK4."""
    children = []
    child = box.get_first_child()
    while child:
        children.append(child)
        child = child.get_next_sibling()
    return children


class HomeWindow(Gtk.ApplicationWindow):

    def __init__(self):
        logging.debug('STARTUP: Loading the desktop window')
        Gtk.ApplicationWindow.__init__(self)


        self._active = False
        self._fully_obscured = True

        display = Gdk.Display.get_default()
        monitors = display.get_monitors()
        if monitors.get_n_items() > 0:
            monitor = monitors.get_item(0)
            geom = monitor.get_geometry()
            self.set_default_size(geom.width, geom.height)

        icons_path = os.path.join(config.data_path, 'icons')
        icon_theme = Gtk.IconTheme.get_for_display(display)
        icon_theme.add_search_path(icons_path)

        self._busy_count = 0

        # Key events
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect('key-pressed', self.__key_pressed_cb)
        key_controller.connect('key-released', self.__key_released_cb)
        self.add_controller(key_controller)

        self.connect('map', self.__map_event_cb)

        self._box = HomeBackgroundBox()

        self._toolbar = ViewToolbar()
        self._box.append(self._toolbar)

        self._alert = None

        self._home_box = HomeBox(self._toolbar)
        self._home_box.set_vexpand(True)
        self._box.append(self._home_box)
        self._toolbar.show_view_buttons()

        # Loads the Gsettings value for activity 'resume-mode'
        setting = Gio.Settings.new('org.sugarlabs.user')
        self._resume_mode = setting.get_boolean('resume-activity')
        self._home_box.set_resume_mode(self._resume_mode)

        self._group_box = GroupBox(self._toolbar)
        self._mesh_box = MeshBox(self._toolbar)
        self._transition_box = TransitionBox()

        self.set_child(self._box)

        self._transition_box.connect('completed',
                                     self._transition_completed_cb)

        shell.get_model().zoom_level_changed.connect(
            self.__zoom_level_changed_cb)

        self._alt_timeout_sid = None

    def add_alert(self, alert):
        self._alert = alert
        self._show_alert()

    def remove_alert(self, alert):
        if alert == self._alert:
            self._box.remove(self._alert)
            self._alert = None

    def _show_alert(self):
        if self._alert:
            self._box.append(self._alert)
            # Place alert after toolbar (index 1)
            self._box.reorder_child_after(self._alert, self._toolbar)

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

    def __screen_size_changed_cb(self, *args):
        display = Gdk.Display.get_default()
        monitors = display.get_monitors()
        if monitors.get_n_items() > 0:
            monitor = monitors.get_item(0)
            geom = monitor.get_geometry()
            self.set_default_size(geom.width, geom.height)

    def _activate_view(self, level):
        if level == ShellModel.ZOOM_HOME:
            self._home_box.resume()
        elif level == ShellModel.ZOOM_MESH:
            self._mesh_box.resume()

    # We no longer track obscured state this way.

    def __is_alt(self, keyval, state):
        """Check if the key event is an Alt key press."""
        # When shift is on, <ALT> becomes <META>
        shift = (state & Gdk.ModifierType.SHIFT_MASK) != 0
        return keyval in [Gdk.KEY_Alt_L, Gdk.KEY_Alt_R] or \
            keyval in [Gdk.KEY_Meta_L, Gdk.KEY_Meta_R] and shift

    def __key_pressed_cb(self, controller, keyval, keycode, state):
        """GTK4 EventControllerKey 'key-pressed' callback."""
        if self.__is_alt(keyval, state) and not self._alt_timeout_sid:
            self._home_box.set_resume_mode(not self._resume_mode)
            self._alt_timeout_sid = GLib.timeout_add(100,
                                                     self.__alt_timeout_cb)

        if not self._toolbar.search_entry.props.has_focus:
            self._toolbar.search_entry.grab_focus()

        return False

    def __key_released_cb(self, controller, keyval, keycode, state):
        """GTK4 EventControllerKey 'key-released' callback."""
        if self.__is_alt(keyval, state) and self._alt_timeout_sid:
            self._home_box.set_resume_mode(self._resume_mode)
            GLib.source_remove(self._alt_timeout_sid)
            self._alt_timeout_sid = None

        return False

    def __alt_timeout_cb(self):
        # Check modifier state via seat/device if needed.
        # For now, just reset the mode.
        self._home_box.set_resume_mode(self._resume_mode)

        if self._alt_timeout_sid:
            GLib.source_remove(self._alt_timeout_sid)
            self._alt_timeout_sid = None

        return False

    def __map_event_cb(self, widget):
        """GTK4: 'map' signal has no event parameter."""
        self.grab_focus()

    def __zoom_level_changed_cb(self, **kwargs):
        old_level = kwargs['old_level']
        new_level = kwargs['new_level']

        self._deactivate_view(old_level)
        self._activate_view(new_level)

        if old_level != ShellModel.ZOOM_ACTIVITY and \
           new_level != ShellModel.ZOOM_ACTIVITY:
            self._hide_alert()
            children = _get_children(self._box)
            if len(children) >= 2:
                self._box.remove(children[1])
            self._transition_box.set_vexpand(True)
            self._box.append(self._transition_box)

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
        children = _get_children(self._box)
        if len(children) >= 2:
            self._box.remove(children[1])

        if level == ShellModel.ZOOM_HOME:
            self._home_box.set_vexpand(True)
            self._box.append(self._home_box)
            self._toolbar.clear_query()
            self._toolbar.set_placeholder_text_for_view(_('Home'))
            self._toolbar.show_view_buttons()
        elif level == ShellModel.ZOOM_GROUP:
            self._group_box.set_vexpand(True)
            self._box.append(self._group_box)
            self._toolbar.clear_query()
            self._toolbar.set_placeholder_text_for_view(_('Group'))
            self._toolbar.hide_view_buttons()
        elif level == ShellModel.ZOOM_MESH:
            self._mesh_box.set_vexpand(True)
            self._box.append(self._mesh_box)
            self._toolbar.clear_query()
            self._toolbar.set_placeholder_text_for_view(_('Neighborhood'))
            self._toolbar.hide_view_buttons()
        self._show_alert()

    def get_home_box(self):
        return self._home_box

    def busy(self):
        if self._busy_count == 0:
            self._old_cursor = self.get_cursor()
            self._set_cursor(Gdk.Cursor.new_from_name('wait', None))
        self._busy_count += 1

    def unbusy(self):
        self._busy_count -= 1
        if self._busy_count == 0:
            self._set_cursor(self._old_cursor)

    def _set_cursor(self, cursor):
        self.set_cursor(cursor)


def get_instance():
    global _instance
    if not _instance:
        _instance = HomeWindow()
    return _instance
