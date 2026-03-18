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

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Graphene

from sugar3.graphics import style


class FrameContainer(Gtk.Widget):
    """A container class for frame panel rendering. Hosts a child 'box' where
    frame elements can be added. Excludes grid-sized squares at each end
    of the frame panel, and a space alongside the inside of the screen where
    a border is drawn."""

    __gtype_name__ = 'SugarFrameContainer'

    def __init__(self, position):
        Gtk.Widget.__init__(self)
        self._position = position

        if self.is_vertical():
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        else:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_parent(self)
        self._child = box

    def get_child(self):
        return self._child

    def is_vertical(self):
        return self._position in (Gtk.PositionType.LEFT,
                                  Gtk.PositionType.RIGHT)

    def do_snapshot(self, snapshot):
        r, g, b, a = style.COLOR_BUTTON_GREY.get_rgba()
        color = Gdk.RGBA()
        color.red, color.green, color.blue, color.alpha = r, g, b, a

        width = self.get_width()
        height = self.get_height()

        if self.is_vertical():
            x = style.GRID_CELL_SIZE \
                if self._position == Gtk.PositionType.LEFT else 0
            y = style.GRID_CELL_SIZE
            rect_width = style.LINE_WIDTH
            rect_height = height - (style.GRID_CELL_SIZE * 2)
        else:
            x = style.GRID_CELL_SIZE
            y = style.GRID_CELL_SIZE \
                if self._position == Gtk.PositionType.TOP else 0
            rect_height = style.LINE_WIDTH
            rect_width = width - (style.GRID_CELL_SIZE * 2)

        rect = Graphene.Rect.alloc()
        rect.init(float(x), float(y), float(rect_width), float(rect_height))
        snapshot.append_color(color, rect)

        self.snapshot_child(self._child, snapshot)

    def do_measure(self, orientation, for_size):
        display = Gdk.Display.get_default()
        if display is None:
            return 0, 0, -1, -1

        monitor = display.get_monitors().get_item(0)
        geometry = monitor.get_geometry()

        if self.is_vertical():
            if orientation == Gtk.Orientation.VERTICAL:
                natural = geometry.height
            else:
                natural = style.GRID_CELL_SIZE + style.LINE_WIDTH
        else:
            if orientation == Gtk.Orientation.HORIZONTAL:
                natural = geometry.width
            else:
                natural = style.GRID_CELL_SIZE + style.LINE_WIDTH

        return natural, natural, -1, -1

    def do_size_allocate(self, width, height, baseline):
        if self.is_vertical():
            x = 0 if self._position == Gtk.PositionType.LEFT \
                else style.LINE_WIDTH
            y = style.GRID_CELL_SIZE
            child_width = width - style.LINE_WIDTH
            child_height = height - (style.GRID_CELL_SIZE * 2)
        else:
            x = style.GRID_CELL_SIZE
            y = 0 if self._position == Gtk.PositionType.TOP \
                else style.LINE_WIDTH
            child_width = width - (style.GRID_CELL_SIZE * 2)
            child_height = height - style.LINE_WIDTH

        transform = Gdk.Transform.new()
        transform = transform.translate((x, y))
        self._child.allocate(child_width, child_height, baseline, transform)

    def do_dispose(self):
        if self._child:
            self._child.unparent()
            self._child = None
        Gtk.Widget.do_dispose(self)


class FrameWindow(Gtk.Window):
    __gtype_name__ = 'SugarFrameWindow'

    def __init__(self, position):
        Gtk.Window.__init__(self)
        self.hover = False
        self.size = style.GRID_CELL_SIZE + style.LINE_WIDTH

        self._position = position

        self.set_decorated(False)
        self.connect('realize', self._realize_cb)

        motion_controller = Gtk.EventControllerMotion()
        motion_controller.connect('enter', self._enter_cb)
        motion_controller.connect('leave', self._leave_cb)
        self.add_controller(motion_controller)

        self._container = FrameContainer(position)
        self.set_child(self._container)
        self._update_size()

        display = Gdk.Display.get_default()
        if display:
            monitor = display.get_monitors().get_item(0)
            monitor.connect('notify::geometry', self._monitor_changed_cb)

    def append(self, child, expand=True, fill=True):
        box = self._container.get_child()
        if expand:
            box.append(child)
            child.set_hexpand(True)
            child.set_vexpand(True)
        else:
            box.append(child)

    def _update_size(self):
        display = Gdk.Display.get_default()
        if display is None:
            return

        monitor = display.get_monitors().get_item(0)
        geometry = monitor.get_geometry()

        if self._position == Gtk.PositionType.TOP \
                or self._position == Gtk.PositionType.BOTTOM:
            self.set_default_size(geometry.width, self.size)
        else:
            self.set_default_size(self.size, geometry.height)

    def _realize_cb(self, widget):
        surface = self.get_surface()
        if surface:
            surface.set_accept_focus(False)

    def _enter_cb(self, controller, x, y):
        self.hover = True

    def _leave_cb(self, controller):
        self.hover = False

    def _monitor_changed_cb(self, monitor, pspec):
        self._update_size()


if hasattr(FrameWindow, 'set_css_name'):
    FrameWindow.set_css_name('framewindow')
