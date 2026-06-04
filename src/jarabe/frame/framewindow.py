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

from sugar4.graphics import style

def _get_screen_size():
    display = Gdk.Display.get_default()
    if display:
        monitors = display.get_monitors()
        if monitors and monitors.get_n_items() > 0:
            geometry = monitors.get_item(0).get_geometry()
            return geometry.width, geometry.height
    return 1024, 768


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
            self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        else:
            self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._box.set_parent(self)

    def do_dispose(self):
        if self._box:
            self._box.unparent()
            self._box = None
        Gtk.Widget.do_dispose(self)

    def get_child_box(self):
        return self._box

    def is_vertical(self):
        return self._position in (Gtk.PositionType.LEFT,
                                  Gtk.PositionType.RIGHT)

    def do_snapshot(self, snapshot):
        # Draw the inner border as a rectangle
        color = Gdk.RGBA()
        # Parse CSS color if it's available, otherwise fallback
        color.parse(style.COLOR_BUTTON_GREY.get_svg())

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

        rect = Graphene.Rect()
        rect.init(x, y, rect_width, rect_height)
        snapshot.append_color(color, rect)

        # Snapshot child
        if self._box:
            self.snapshot_child(self._box, snapshot)

    def do_measure(self, orientation, for_size):
        sw, sh = _get_screen_size()
        if self.is_vertical():
            if orientation == Gtk.Orientation.VERTICAL:
                return sh, sh, -1, -1
            else:
                w = style.GRID_CELL_SIZE + style.LINE_WIDTH
                return w, w, -1, -1
        else:
            if orientation == Gtk.Orientation.HORIZONTAL:
                return sw, sw, -1, -1
            else:
                h = style.GRID_CELL_SIZE + style.LINE_WIDTH
                return h, h, -1, -1

    def do_size_allocate(self, width, height, baseline):
        # exclude grid squares at two ends of the frame
        # allocate remaining space to child box, minus the space needed for
        # drawing the border
        allocation = Gdk.Rectangle()
        if self.is_vertical():
            allocation.x = 0 if self._position == Gtk.PositionType.LEFT \
                else style.LINE_WIDTH
            allocation.y = style.GRID_CELL_SIZE
            allocation.width = width - style.LINE_WIDTH
            allocation.height = height - (style.GRID_CELL_SIZE * 2)
        else:
            allocation.x = style.GRID_CELL_SIZE
            allocation.y = 0 if self._position == Gtk.PositionType.TOP \
                else style.LINE_WIDTH
            allocation.width = width - (style.GRID_CELL_SIZE * 2)
            allocation.height = height - style.LINE_WIDTH

        if self._box:
            self._box.size_allocate(allocation, baseline)


class FrameWindow(Gtk.Window):
    __gtype_name__ = 'SugarFrameWindow'

    def __init__(self, position):
        Gtk.Window.__init__(self)
        self.hover = False
        self.size = style.GRID_CELL_SIZE + style.LINE_WIDTH

        # Removed sugar_accel_group reference for now.

        self._position = position

        self.set_decorated(False)
        self.set_focus_on_map(False)

        controller = Gtk.EventControllerMotion.new()
        controller.connect('enter', self._enter_notify_cb)
        controller.connect('leave', self._leave_notify_cb)
        self.add_controller(controller)

        self._container = FrameContainer(position)
        self.set_child(self._container)
        self._update_size()

        display = Gdk.Display.get_default()
        if display:
            monitors = display.get_monitors()
            if monitors:
                monitors.connect('items-changed', self._size_changed_cb)

    def append(self, child, expand=True, fill=True):
        if expand:
            if self._container.is_vertical():
                child.set_vexpand(True)
            else:
                child.set_hexpand(True)
        self._container.get_child_box().append(child)

    def _update_size(self):
        sw, sh = _get_screen_size()
        if self._position == Gtk.PositionType.TOP \
                or self._position == Gtk.PositionType.BOTTOM:
            self.set_default_size(sw, self.size)
        else:
            self.set_default_size(self.size, sh)

    def _enter_notify_cb(self, controller, x, y):
        self.hover = True

    def _leave_notify_cb(self, controller):
        self.hover = False

    def _size_changed_cb(self, monitors, position, removed, added):
        self._update_size()


if hasattr(FrameWindow, 'set_css_name'):
    FrameWindow.set_css_name('framewindow')
