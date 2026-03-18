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

import math

from gi.repository import Gtk
from gi.repository import Gdk

from sugar3.graphics import style


_BASE_DISTANCE = style.zoom(25)
_CHILDREN_FACTOR = style.zoom(3)


class SnowflakeLayout(Gtk.Widget):
    __gtype_name__ = 'SugarSnowflakeLayout'

    def __init__(self):
        Gtk.Widget.__init__(self)
        self._nflakes = 0
        self._children = {}

    def add_icon(self, child, center=False):
        if not center:
            self._nflakes += 1

        self._children[child] = center
        child.set_parent(self)

    def remove(self, child):
        if child not in self._children:
            return

        if not self._children[child]:  # not centered
            self._nflakes -= 1

        del self._children[child]
        child.unparent()

    def do_measure(self, orientation, for_size):
        size = self._calculate_size()
        return (size, size, -1, -1)

    def do_size_allocate(self, width, height, baseline):
        r = self._get_radius()
        index = 0

        for child, centered in list(self._children.items()):
            _, child_width, _, _ = child.measure(Gtk.Orientation.HORIZONTAL, -1)
            _, child_height, _, _ = child.measure(Gtk.Orientation.VERTICAL, -1)
            
            rect = Gdk.Rectangle()
            rect.x = 0
            rect.y = 0
            rect.width = child_width
            rect.height = child_height

            x_off = width - child_width
            y_off = height - child_height
            if centered:
                rect.x = x_off / 2
                rect.y = y_off / 2
            else:
                angle = 2 * math.pi * index / self._nflakes

                if self._nflakes != 2:
                    angle -= math.pi / 2

                dx = math.cos(angle) * r
                dy = math.sin(angle) * r

                rect.x = int(x_off / 2 + dx)
                rect.y = int(y_off / 2 + dy)

                index += 1

            child.size_allocate(rect, -1)

    def do_snapshot(self, snapshot):
        for child in self._children:
            self.snapshot_child(child, snapshot)

    def _get_radius(self):
        radius = int(_BASE_DISTANCE + _CHILDREN_FACTOR * self._nflakes)
        for child, centered in list(self._children.items()):
            if centered:
                _, w, _, _ = child.measure(Gtk.Orientation.HORIZONTAL, -1)
                _, h, _, _ = child.measure(Gtk.Orientation.VERTICAL, -1)
                radius += max(w, h) / 2

        return radius

    def _calculate_size(self):
        thickness = 0
        for child in list(self._children.keys()):
            _, w, _, _ = child.measure(Gtk.Orientation.HORIZONTAL, -1)
            _, h, _, _ = child.measure(Gtk.Orientation.VERTICAL, -1)
            thickness = max(thickness, max(w, h))

        return self._get_radius() * 2 + thickness
