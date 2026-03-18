# Copyright (C) 2011-2012 One Laptop Per Child
# Copyright (C) 2010 Tomeu Vizoso
# Copyright (C) 2011 Walter Bender
# Copyright (C) 2011 Raul Gutierrez Segales
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
from gi.repository import Gsk


class ViewContainer(Gtk.Widget):
    __gtype_name__ = 'SugarViewContainer'

    def __init__(self, layout, owner_icon, activity_icon=None, **kwargs):
        # GTK4: Gtk.Container → Gtk.Widget with manual child management
        Gtk.Widget.__init__(self, **kwargs)
        self.set_can_focus(True)

        self._activity_icon = None
        self._owner_icon = None
        self._layout = None

        self._children = []
        self.set_layout(layout)

        if owner_icon:
            self._owner_icon = owner_icon
            self._add_child(self._owner_icon)
            self._owner_icon.set_visible(True)

        if activity_icon:
            self._activity_icon = activity_icon
            self._add_child(self._activity_icon)
            self._activity_icon.set_visible(True)

    def _add_child(self, child):
        """Add a child widget (GTK4 replacement for do_add)"""
        if child != self._owner_icon and child != self._activity_icon:
            self._children.append(child)
        child.set_parent(self)

    def add(self, child):
        """Public add method"""
        self._add_child(child)

    def remove(self, child):
        """Remove a child widget (GTK4 replacement for do_remove)"""
        was_visible = child.get_visible()
        if child in self._children:
            self._children.remove(child)
            if self._layout:
                self._layout.remove(child)
        child.unparent()
        if was_visible and self.get_visible():
            self.queue_resize()

    def do_size_allocate(self, width, height, baseline):
        """GTK4: Updated signature (width, height, baseline)"""
        if self._owner_icon:
            alloc = type('Allocation', (), {
                'x': 0, 'y': 0, 'width': width, 'height': height
            })()
            self._layout.setup(alloc, self._owner_icon,
                               self._activity_icon)
            self._layout.allocate_children(alloc, self._children)

    def do_measure(self, orientation, for_size):
        """GTK4: Replace do_get_preferred_width/height"""
        if orientation == Gtk.Orientation.HORIZONTAL:
            return (0, for_size if for_size > 0 else 100, -1, -1)
        else:
            return (0, for_size if for_size > 0 else 100, -1, -1)

    def do_snapshot(self, snapshot):
        """GTK4: Snapshot children"""
        for child in self._children:
            self.snapshot_child(child, snapshot)
        if self._owner_icon:
            self.snapshot_child(self._owner_icon, snapshot)
        if self._activity_icon:
            self.snapshot_child(self._activity_icon, snapshot)

    def get_children(self):
        """Return list of children for compatibility"""
        result = list(self._children)
        if self._owner_icon:
            result.append(self._owner_icon)
        if self._activity_icon:
            result.append(self._activity_icon)
        return result

    def set_layout(self, layout):
        for child in list(self._children):
            self.remove(child)
        self._layout = layout
