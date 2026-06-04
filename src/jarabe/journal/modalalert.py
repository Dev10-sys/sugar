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

        offset = style.GRID_CELL_SIZE
        self.set_default_size(800, 600)
        
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_modal(True)

        self._main_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # Apply black background CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"box.modal-bg { background-color: black; color: white; }")
        context = self._main_view.get_style_context()
        context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        context.add_class('modal-bg')

        self._vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._vbox.set_spacing(style.DEFAULT_SPACING)
        self._vbox.set_margin_top(style.GRID_CELL_SIZE * 2)
        self._vbox.set_margin_bottom(style.GRID_CELL_SIZE * 2)
        self._vbox.set_margin_start(style.GRID_CELL_SIZE * 2)
        self._vbox.set_margin_end(style.GRID_CELL_SIZE * 2)

        self._main_view.append(self._vbox)
        self._vbox.set_visible(True)

        color = profile.get_color()

        icon = Icon(icon_name='activity-journal',
                    pixel_size=style.XLARGE_ICON_SIZE,
                    xo_color=color)
        self._vbox.append(icon)
        icon.set_visible(True)

        self._title = Gtk.Label()
        self._title.set_markup('<b>%s</b>' % _('Your Journal is full'))
        self._vbox.append(self._title)
        self._title.set_visible(True)

        self._message = Gtk.Label(
            label=_('Please delete some old Journal'
                    ' entries to make space for new ones.'))
        self._vbox.append(self._message)
        self._message.set_visible(True)

        # Alignment can be replaced by Box with hexpand/vexpand
        alignment = Gtk.Box()
        alignment.set_hexpand(True)
        alignment.set_vexpand(True)
        alignment.set_halign(Gtk.Align.CENTER)
        alignment.set_valign(Gtk.Align.CENTER)
        self._vbox.append(alignment)
        alignment.set_visible(True)

        self._show_journal = Gtk.Button()
        self._show_journal.set_label(_('Show Journal'))
        alignment.append(self._show_journal)
        self._show_journal.set_visible(True)
        self._show_journal.connect('clicked', self.__show_journal_cb)

        self.set_child(self._main_view)
        self._main_view.set_visible(True)

        self.connect('realize', self.__realize_cb)

    def __realize_cb(self, widget):
        self.set_focusable(True)

    def __show_journal_cb(self, button):
        """The opener will listen on the destroy signal"""
        self.destroy()
