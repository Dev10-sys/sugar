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

from sugar3.graphics.icon import Icon
from sugar3.graphics import style
from sugar3 import profile


class ModalAlert(Gtk.Window):

    __gtype_name__ = 'SugarModalAlert'

    def __init__(self):
        Gtk.Window.__init__(self)

        # GTK4: set_border_width → margins
        self.set_margin_start(style.LINE_WIDTH)
        self.set_margin_end(style.LINE_WIDTH)
        self.set_margin_top(style.LINE_WIDTH)
        self.set_margin_bottom(style.LINE_WIDTH)

        # GTK4: Gdk.Screen → Display/Monitor
        display = Gdk.Display.get_default()
        monitor = display.get_monitors().get_item(0)
        geometry = monitor.get_geometry()
        offset = style.GRID_CELL_SIZE
        width = geometry.width - offset * 2
        height = geometry.height - offset * 2
        self.set_size_request(width, height)

        self.set_decorated(False)
        self.set_resizable(False)
        self.set_modal(True)

        # GTK4: Gtk.EventBox → Gtk.Box with CSS
        self._main_view = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(
            b"box { background-color: %s; }" %
            style.COLOR_BLACK.get_html().encode())
        self._main_view.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # GTK4: Gtk.VBox → Gtk.Box(VERTICAL)
        self._vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._vbox.set_spacing(style.DEFAULT_SPACING)
        self._vbox.set_margin_start(style.GRID_CELL_SIZE * 2)
        self._vbox.set_margin_end(style.GRID_CELL_SIZE * 2)
        self._vbox.set_margin_top(style.GRID_CELL_SIZE * 2)
        self._vbox.set_margin_bottom(style.GRID_CELL_SIZE * 2)
        self._main_view.append(self._vbox)
        self._vbox.set_visible(True)

        color = profile.get_color()

        icon = Icon(icon_name='activity-journal',
                    pixel_size=style.XLARGE_ICON_SIZE,
                    xo_color=color)
        self._vbox.append(icon)
        icon.set_visible(True)

        self._title = Gtk.Label()
        # GTK4: modify_fg → CSS
        title_css = Gtk.CssProvider()
        title_css.load_from_data(
            b"label { color: %s; }" %
            style.COLOR_WHITE.get_html().encode())
        self._title.get_style_context().add_provider(
            title_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self._title.set_markup('<b>%s</b>' % _('Your Journal is full'))
        self._vbox.append(self._title)
        self._title.set_visible(True)

        self._message = Gtk.Label(
            label=_('Please delete some old Journal'
                    ' entries to make space for new ones.'))
        msg_css = Gtk.CssProvider()
        msg_css.load_from_data(
            b"label { color: %s; }" %
            style.COLOR_WHITE.get_html().encode())
        self._message.get_style_context().add_provider(
            msg_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self._vbox.append(self._message)
        self._message.set_visible(True)

        # GTK4: Gtk.Alignment → Gtk.Box with alignment
        btn_box = Gtk.Box()
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_valign(Gtk.Align.CENTER)
        self._vbox.append(btn_box)
        btn_box.set_visible(True)

        self._show_journal = Gtk.Button()
        self._show_journal.set_label(_('Show Journal'))
        btn_box.append(self._show_journal)
        self._show_journal.set_visible(True)
        self._show_journal.connect('clicked', self.__show_journal_cb)

        # GTK4: container.add → set_child
        self.set_child(self._main_view)
        self._main_view.set_visible(True)

        self.connect('realize', self.__realize_cb)

    def __realize_cb(self, widget):
        surface = self.get_surface()
        if surface:
            surface.set_accept_focus(True)

    def __show_journal_cb(self, button):
        """The opener will listen on the destroy signal"""
        self.destroy()
