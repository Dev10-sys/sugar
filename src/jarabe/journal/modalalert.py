# Copyright (C) 2008 One Laptop Per Child
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
from gettext import gettext as _

from sugar4.graphics.icon import Icon
from sugar4.graphics import style
from sugar4 import profile


class ModalAlert(Gtk.Window):

    __gtype_name__ = 'SugarModalAlert'

    def __init__(self):
        Gtk.Window.__init__(self)

        self.set_margin_start(style.LINE_WIDTH)
        self.set_margin_end(style.LINE_WIDTH)
        self.set_margin_top(style.LINE_WIDTH)
        self.set_margin_bottom(style.LINE_WIDTH)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_modal(True)

        self._main_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._vbox = self._main_view
        self._vbox.set_spacing(style.DEFAULT_SPACING)
        self._vbox.set_margin_start(style.GRID_CELL_SIZE * 2)
        self._vbox.set_margin_end(style.GRID_CELL_SIZE * 2)
        self._vbox.set_margin_top(style.GRID_CELL_SIZE * 2)
        self._vbox.set_margin_bottom(style.GRID_CELL_SIZE * 2)

        color = profile.get_color()

        icon = Icon(icon_name='activity-journal',
                    pixel_size=style.XLARGE_ICON_SIZE,
                    xo_color=color)
        self._vbox.append(icon)

        self._title = Gtk.Label()
        self._title.set_markup('<b>%s</b>' % _('Your Journal is full'))
        self._vbox.append(self._title)

        self._message = Gtk.Label(
            label=_('Please delete some old Journal'
                    ' entries to make space for new ones.'))
        self._vbox.append(self._message)

        self._show_journal = Gtk.Button()
        self._show_journal.set_label(_('Show Journal'))
        self._show_journal.set_halign(Gtk.Align.CENTER)
        self._show_journal.connect('clicked', self.__show_journal_cb)
        self._vbox.append(self._show_journal)

        self.set_child(self._main_view)

        self.connect('realize', self.__realize_cb)

    def __realize_cb(self, widget):
        # self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        pass

    def __show_journal_cb(self, button):
        """The opener will listen on the destroy signal"""
        self.destroy()
