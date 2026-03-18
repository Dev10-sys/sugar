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

import logging

from gi.repository import Gtk

from sugar3.graphics.tray import VTray, TrayIcon
from sugar3.graphics import style
from sugar3.graphics.palette import Palette
from sugar3.graphics.icon import Icon

from jarabe.view.buddymenu import BuddyMenu
from jarabe.model import shell
from jarabe.frame.frameinvoker import FrameWidgetInvoker


class FriendIcon(TrayIcon):

    def __init__(self, buddy):
        TrayIcon.__init__(self, icon_name='computer-xo',
                          xo_color=buddy.get_color())
        self._buddy = buddy
        self.set_palette_invoker(FrameWidgetInvoker(self))

    def create_palette(self):
        palette = BuddyMenu(self._buddy)
        palette.set_group_id('frame')
        return palette


class FriendsTray(VTray):

    def __init__(self):
        VTray.__init__(self)

        self._shared_activity = None
        self._buddies = {}

        shell_model = shell.get_model()
        shell_model.connect('active-activity-changed',
                            self.__active_activity_changed_cb)

        active_activity = shell_model.get_active_activity()
        self._set_activity(active_activity)

    def _set_activity(self, home_activity):
        if home_activity is None:
            return

        new_activity = home_activity.get_shared_activity()
        if self._shared_activity == new_activity:
            return

        self._remove_all_buddies()

        self._shared_activity = new_activity
        if self._shared_activity is not None:
            for buddy in self._shared_activity.get_joined_buddies():
                self._add_buddy(buddy)

            self._shared_activity.connect('buddy-joined',
                                          self.__buddy_joined_cb)
            self._shared_activity.connect('buddy-left',
                                          self.__buddy_left_cb)

    def __active_activity_changed_cb(self, model, home_activity):
        self._set_activity(home_activity)

    def _add_buddy(self, buddy):
        if buddy.props.key in self._buddies:
            return

        icon = FriendIcon(buddy)
        self.add_item(icon)
        icon.set_visible(True)
        self._buddies[buddy.props.key] = icon

    def _remove_buddy(self, buddy):
        if buddy.props.key not in self._buddies:
            return

        icon = self._buddies[buddy.props.key]
        self.remove_item(icon)
        del self._buddies[buddy.props.key]

    def _remove_all_buddies(self):
        for key in list(self._buddies.keys()):
            icon = self._buddies[key]
            self.remove_item(icon)
        self._buddies = {}

    def __buddy_joined_cb(self, activity, buddy):
        self._add_buddy(buddy)

    def __buddy_left_cb(self, activity, buddy):
        self._remove_buddy(buddy)
