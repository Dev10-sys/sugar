# Copyright (C) 2012 One Laptop Per Child
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

from gi.repository import Gdk

from gi.repository import SugarExt
try:
    from gi.repository import SugarGestures
except ImportError:
    SugarGestures = None

from sugar4.graphics import style

_instance = None


class GestureHandler(object):
    '''Handling gestures to show/hide the frame

    We use SugarExt.GestureGrabber to listen for
    gestures on the root window. We use a toggle
    gesture to either hide or show the frame: Swiping
    from the frame area at the top towards the center
    does reveal the Frame or hide it.
    '''

    def __init__(self, frame):
        self._frame = frame

        #self._gesture_grabber = SugarExt.GestureGrabber()
        self._controller = []

        display = Gdk.Display.get_default()
        if display:
            # Using display monitors-changed instead.
            monitors = display.get_monitors()
            monitors.connect('items-changed', self.__size_changed_cb)

        self._add_controller()

    def __size_changed_cb(self, list_model, position, removed, added):
        self._add_controller()

    def _add_controller(self):
        # We need SugarGestures to track gestures.
        if SugarGestures is None:
            return

        for controller in self._controller:
            #self._gesture_grabber.remove(controller)
            pass

        width = 1024
        display = Gdk.Display.get_default()
        if display:
            monitors = display.get_monitors()
            if monitors and monitors.get_n_items() > 0:
                width = monitors.get_item(0).get_geometry().width

        self._track_gesture_for_area(SugarGestures.SwipeDirectionFlags.DOWN,
                                     0, 0, width,
                                     style.GRID_CELL_SIZE)

    def _track_gesture_for_area(self, directions, x, y, width, height):
        rectangle = Gdk.Rectangle()
        rectangle.x = x
        rectangle.y = y
        rectangle.width = width
        rectangle.height = height
        swipe = SugarGestures.SwipeController(directions=directions)
        swipe.connect('swipe-ended', self.__swipe_ended_cb)
        
        if hasattr(self, '_gesture_grabber') and self._gesture_grabber:
            self._gesture_grabber.add(swipe, rectangle)
            self._controller.append(swipe)

    def __swipe_ended_cb(self, controller, event_direction):
        self._frame.toggle()


def setup(frame):
    global _instance
    _instance = GestureHandler(frame)
