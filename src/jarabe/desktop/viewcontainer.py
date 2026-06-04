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


# We subclass Gtk.Widget and manage children manually using
# set_parent() / unparent() and a custom LayoutManager.
class ViewContainer(Gtk.Widget):
    __gtype_name__ = 'SugarViewContainer'

    def __init__(self, layout, owner_icon, activity_icon=None, **kwargs):
        super().__init__(**kwargs)
        self.set_can_focus(True)
        self.set_focusable(True)

        self._activity_icon = None
        self._owner_icon = None
        self._layout = None

        self._children = []
        self.set_layout(layout)

        if owner_icon:
            self._owner_icon = owner_icon
            self._owner_icon.set_parent(self)

        if activity_icon:
            self._activity_icon = activity_icon
            self._activity_icon.set_parent(self)

    def add(self, child):
        """Add a child widget to this container."""
        if child != self._owner_icon and child != self._activity_icon:
            self._children.append(child)
        child.set_parent(self)

    def remove(self, child):
        """Remove a child widget from this container."""
        was_visible = child.get_visible()
        if child in self._children:
            self._children.remove(child)
            child.unparent()
            self._layout.remove(child)
            if was_visible and self.get_visible():
                self.queue_resize()

    def do_size_allocate(self, width, height, baseline):
        """GTK4 size_allocate signature: (width, height, baseline)."""
        allocation = self.get_allocation()
        if self._owner_icon:
            self._layout.setup(allocation, self._owner_icon,
                               self._activity_icon)

        self._layout.allocate_children(allocation, self._children)

    def get_children(self):
        """Return list of all children (replacement for removed do_forall)."""
        all_children = list(self._children)
        if self._owner_icon:
            all_children.append(self._owner_icon)
        if self._activity_icon:
            all_children.append(self._activity_icon)
        return all_children

    def set_layout(self, layout):
        """Set the layout manager, removing all current children."""
        for child in self.get_children():
            self.remove(child)
        self._layout = layout

    def do_dispose(self):
        """GTK4: Clean up children in dispose."""
        while self._children:
            child = self._children.pop()
            child.unparent()
        if self._owner_icon:
            self._owner_icon.unparent()
            self._owner_icon = None
        if self._activity_icon:
            self._activity_icon.unparent()
            self._activity_icon = None
        Gtk.Widget.do_dispose(self)
