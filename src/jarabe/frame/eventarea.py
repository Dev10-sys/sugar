# Copyright (C) 2007, Red Hat, Inc.
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

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GLib

from sugar3.graphics import style


_MAX_DELAY = 1000

_CORNERS = ['nw', 'ne', 'se', 'sw']
_EDGES = ['n', 'e', 's', 'w']
_BOXES = _CORNERS + _EDGES


class EventArea(GObject.GObject):
    __gsignals__ = {
        'enter': (GObject.SignalFlags.RUN_FIRST, None, ([])),
        'leave': (GObject.SignalFlags.RUN_FIRST, None, ([])),
    }

    def __init__(self, settings):
        GObject.GObject.__init__(self)

        self._hover = False
        self._sids = {}

        self._boxes = {}
        self._tags = {}
        for tag in _BOXES:
            box = self._box(tag)
            self._tags[box] = tag
            self._boxes[tag] = box

        settings.connect('changed', self._settings_changed_cb)
        self._settings_changed_cb(settings, None)

    def _box(self, tag):
        box = Gtk.Window()
        box.set_decorated(False)
        box.set_default_size(1, 1)
        
        motion_controller = Gtk.EventControllerMotion()
        motion_controller.connect('enter', self._enter_cb)
        motion_controller.connect('leave', self._leave_cb)
        box.add_controller(motion_controller)
        
        drop_target = Gtk.DropTarget.new(Gdk.ContentProvider, Gdk.DragAction.COPY)
        drop_target.connect('motion', self._drag_motion_cb)
        drop_target.connect('leave', self._drag_leave_cb)
        box.add_controller(drop_target)
        
        box.present()
        return box

    def _settings_changed_cb(self, settings, key):
        self._edge_delay = min(settings.get_int('edge-delay'), _MAX_DELAY)
        self._corner_delay = min(settings.get_int('corner-delay'), _MAX_DELAY)
        ts = min(settings.get_int('trigger-size'), style.GRID_CELL_SIZE)
        
        display = Gdk.Display.get_default()
        if display:
            monitor = display.get_monitors().get_item(0)
            geometry = monitor.get_geometry()
            sw = geometry.width
            sh = geometry.height
        else:
            sw = 1200
            sh = 900

        if self._edge_delay == _MAX_DELAY:
            self._hide(_EDGES)
        else:
            self._move('n', ts, -1, sw - ts * 2, ts + 1)
            self._move('e', -1, ts, ts + 1, sh - ts * 2)
            self._move('s', ts, sh - ts, sw - ts * 2, ts + 1)
            self._move('w', sw - ts, ts, ts + 1, sh - ts * 2)

        if self._corner_delay == _MAX_DELAY:
            self._hide(_CORNERS)
        else:
            self._move('nw', -1, -1, ts + 1, ts + 1)
            self._move('ne', sw - ts, -1, ts + 1, ts + 1)
            self._move('se', sw - ts, sh - ts, ts + 1, ts + 1)
            self._move('sw', -1, sh - ts, ts + 1, ts + 1)

    def _hide(self, tags):
        for tag in tags:
            self._move(tag, -20, -20, 1, 1)

    def _move(self, tag, x, y, width, height):
        box = self._boxes[tag]
        box.set_default_size(width, height)
        # GTK4: set_position and move are not supported on Wayland.
        # This will need compositor-specific implementation (e.g. layer-shell).
        pass

    def _notify_enter(self):
        if not self._hover:
            self._hover = True
            self.emit('enter')

    def _notify_leave(self):
        if self._hover:
            self._hover = False
            self.emit('leave')

    def _enter_cb(self, controller, x, y):
        widget = controller.get_widget()
        if widget in self._sids:
            GLib.source_remove(self._sids[widget])
            del self._sids[widget]

        delay = None
        if self._tags[widget] in _CORNERS:
            delay = self._corner_delay
        if self._tags[widget] in _EDGES:
            delay = self._edge_delay

        if delay is not None:
            self._sids[widget] = GLib.timeout_add(delay,
                                                  self.__delay_cb,
                                                  widget)

    def __delay_cb(self, widget):
        del self._sids[widget]
        self._notify_enter()
        return False

    def _leave_cb(self, controller):
        widget = controller.get_widget()
        if widget in self._sids:
            GLib.source_remove(self._sids[widget])
            del self._sids[widget]
        self._notify_leave()

    def _drag_motion_cb(self, drop_target, x, y):
        self._notify_enter()
        return Gdk.DragAction.COPY

    def _drag_leave_cb(self, drop_target):
        self._notify_leave()

    def show(self):
        for box in list(self._boxes.values()):
            box.present()

    def hide(self):
        for box in list(self._boxes.values()):
            box.set_visible(False)

    def _window_stacking_changed_cb(self, screen):
        pass # Wnck removed
