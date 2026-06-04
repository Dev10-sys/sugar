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

from gi.repository import GObject
import logging

class EventArea(GObject.GObject):
    __gsignals__ = {
        'enter': (GObject.SignalFlags.RUN_FIRST, None, ([])),
        'leave': (GObject.SignalFlags.RUN_FIRST, None, ([])),
    }

    def __init__(self, settings):
        GObject.GObject.__init__(self)
        self._hover = False
        self._sids = {}
        logging.warning("EventArea (hot corners) is disabled in GTK4/Wayland port.")

    def show(self):
        pass

    def hide(self):
        pass

    def set_visible(self, visible):
        pass
