# Copyright (C) 2008, Red Hat, Inc.
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

import logging
from gettext import gettext as _

from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import Gdk

from gi.repository import SugarExt
from sugar3.graphics import style

from jarabe.model import shell
from jarabe.view.pulsingicon import PulsingIcon


_INTERVAL = 100


class LaunchWindow(Gtk.Window):

    def __init__(self, activity_id, icon_path, icon_color):
        Gtk.Window.__init__(self)

        self.props.type_hint = Gdk.WindowTypeHint.SPLASHSCREEN

        canvas = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(canvas)

        display = Gdk.Display.get_default()
        if display:
            monitor = display.get_monitors().get_item(0)
            geometry = monitor.get_geometry()
            bar_size = geometry.height / 5 * 2
            box_width = geometry.width / 5
        else:
            bar_size = 360
            box_width = 240

        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header.set_size_request(-1, bar_size)
        canvas.append(header)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_size_request(box_width, -1)
        box.set_hexpand(True)
        box.set_vexpand(True)
        canvas.append(box)

        self._activity_id = activity_id

        self._activity_icon = PulsingIcon(file=icon_path,
                                          pixel_size=style.XLARGE_ICON_SIZE,
                                          interval=_INTERVAL)
        self._activity_icon.set_base_color(icon_color)
        self._activity_icon.set_zooming(style.SMALL_ICON_SIZE,
                                        style.XLARGE_ICON_SIZE, 10)
        self._activity_icon.set_pulsing(True)
        box.append(self._activity_icon)

        footer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=style.DEFAULT_SPACING)
        footer.set_size_request(-1, bar_size)
        canvas.append(footer)

        self.error_text = Gtk.Label()
        self.error_text.props.use_markup = True
        footer.append(self.error_text)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.CENTER)
        footer.append(button_box)
        
        self.cancel_button = Gtk.Button(label=_('Stop'))
        button_box.append(self.cancel_button)

        self.connect('realize', self.__realize_cb)

        display = Gdk.Display.get_default()
        if display:
            monitor = display.get_monitors().get_item(0)
            monitor.connect('notify::geometry', self.__monitor_changed_cb)

        self._home = shell.get_model()
        self._home.connect('active-activity-changed',
                           self.__active_activity_changed_cb)

        self.connect('destroy', self.__destroy_cb)

        self._update_size()

    def show(self):
        self.present()

    def _update_size(self):
        display = Gdk.Display.get_default()
        if display:
            monitor = display.get_monitors().get_item(0)
            geometry = monitor.get_geometry()
            self.set_default_size(geometry.width, geometry.height)

    def __realize_cb(self, widget):
        surface = widget.get_surface()
        if surface and hasattr(SugarExt, 'wm_set_activity_id'):
            # GTK4 doesn't expose XID directly, skip for Wayland
            pass

    def __monitor_changed_cb(self, monitor, pspec):
        self._update_size()

    def __active_activity_changed_cb(self, model, activity):
        if activity.get_activity_id() == self._activity_id:
            self._activity_icon.props.paused = False
        else:
            self._activity_icon.props.paused = True

    def __destroy_cb(self, box):
        self._activity_icon.props.pulsing = False
        self._home.disconnect_by_func(self.__active_activity_changed_cb)


def setup():
    global _INTERVAL

    settings = Gio.Settings.new('org.sugarlabs.desktop')
    _INTERVAL = settings.get_int('launcher-interval')

    model = shell.get_model()
    model.connect('launch-started', __launch_started_cb)
    model.connect('launch-failed', __launch_failed_cb)
    model.connect('launch-completed', __launch_completed_cb)


def add_launcher(activity_id, icon_path, icon_color):
    model = shell.get_model()

    if model.get_launcher(activity_id) is not None:
        return

    launch_window = LaunchWindow(activity_id, icon_path, icon_color)
    launch_window.show()

    model.register_launcher(activity_id, launch_window)


def __launch_started_cb(home_model, home_activity):
    add_launcher(home_activity.get_activity_id(),
                 home_activity.get_icon_path(), home_activity.get_icon_color())


def __launch_failed_cb(home_model, home_activity):
    activity_id = home_activity.get_activity_id()
    launcher = shell.get_model().get_launcher(activity_id)

    if launcher is None:
        logging.error('Launcher for %s is missing', activity_id)
    else:
        launcher.error_text.props.label = _('<b>%s</b> failed to start.') % \
            home_activity.get_activity_name()
        launcher.error_text.show()

        launcher.cancel_button.connect('clicked',
                                       __cancel_button_clicked_cb,
                                       home_activity)
        launcher.cancel_button.show()


def __cancel_button_clicked_cb(button, home_activity):
    _destroy_launcher(home_activity)


def __launch_completed_cb(home_model, home_activity):
    _destroy_launcher(home_activity)


def _destroy_launcher(home_activity):
    activity_id = home_activity.get_activity_id()

    launcher = shell.get_model().get_launcher(activity_id)
    if launcher is None:
        if not home_activity.is_journal():
            logging.error('Launcher was not registered for %s', activity_id)
        return

    shell.get_model().unregister_launcher(activity_id)
    launcher.destroy()
