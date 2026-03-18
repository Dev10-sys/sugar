# Copyright (C) 2006, Red Hat, Inc.
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

from sugar3.graphics.icon import Icon
from sugar3.graphics import style
from sugar3 import profile


class KeepIcon(Gtk.ToggleButton):
    __gtype_name__ = 'SugarKeepIcon'

    def __init__(self):
        Gtk.ToggleButton.__init__(self)
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_focus_on_click(False)

        self._icon = Icon(icon_name='emblem-favorite',
                          pixel_size=style.SMALL_ICON_SIZE)
        self.set_child(self._icon)
        self.connect('toggled', self.__toggled_cb)

        # GTK4: button-press/release-event → GestureClick
        click = Gtk.GestureClick()
        click.connect('pressed', self.__button_press_cb)
        click.connect('released', self.__button_release_cb)
        self.add_controller(click)

        self._xo_color = profile.get_color()

    def do_get_preferred_width(self):
        return 0, style.GRID_CELL_SIZE

    def do_get_preferred_height(self):
        return 0, style.GRID_CELL_SIZE

    def __button_press_cb(self, gesture, n_press, x, y):
        style_context = self.get_style_context()
        style_context.add_class('toggle-press')

    def __button_release_cb(self, gesture, n_press, x, y):
        style_context = self.get_style_context()
        style_context.remove_class('toggle-press')

    def __toggled_cb(self, widget):
        if self.get_active():
            self._icon.props.xo_color = self._xo_color
        else:
            self._icon.props.stroke_color = style.COLOR_BUTTON_GREY.get_svg()
            self._icon.props.fill_color = style.COLOR_TRANSPARENT.get_svg()


if hasattr(KeepIcon, 'set_css_name'):
    KeepIcon.set_css_name('canvasicon')
