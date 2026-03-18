# Copyright (C) 2007, One Laptop Per Child
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
from gettext import gettext as _

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk

from sugar3.graphics import style
from sugar3.graphics.icon import Icon

from jarabe.journal.expandedentry import ExpandedEntry
from jarabe.journal import model


class DetailView(Gtk.Box):
    __gtype_name__ = 'DetailView'

    __gsignals__ = {
        'go-back-clicked': (GObject.SignalFlags.RUN_FIRST, None, ([])),
    }

    def __init__(self, journalactivity, **kwargs):
        self._journalactivity = journalactivity
        self._metadata = None
        self._expanded_entry = None

        # GTK4: Gtk.VBox → Gtk.Box(VERTICAL)
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        back_bar = BackBar()
        # GTK4: button-release-event → GestureClick
        click = Gtk.GestureClick()
        click.connect('released', self.__back_bar_release_cb)
        back_bar.add_controller(click)
        self.append(back_bar)

        # GTK4: show_all → set_visible
        self.set_visible(True)

    def _fav_icon_activated_cb(self, fav_icon):
        keep = not self._expanded_entry.get_keep()
        self._expanded_entry.set_keep(keep)
        fav_icon.props.keep = keep

    def __back_bar_release_cb(self, gesture, n_press, x, y):
        self.emit('go-back-clicked')

    def _update_view(self):
        if self._expanded_entry is None:
            self._expanded_entry = ExpandedEntry(self._journalactivity)
            self._expanded_entry.set_hexpand(True)
            self._expanded_entry.set_vexpand(True)
            self.append(self._expanded_entry)
        self._expanded_entry.set_metadata(self._metadata)
        self.set_visible(True)

    def refresh(self):
        logging.debug('DetailView.refresh')
        self._metadata = model.get(self._metadata['uid'])
        self._update_view()

    def get_metadata(self):
        return self._metadata

    def set_metadata(self, metadata):
        self._metadata = metadata
        self._update_view()

    metadata = GObject.Property(
        type=object, getter=get_metadata, setter=set_metadata)


class BackBar(Gtk.Box):

    def __init__(self):
        # GTK4: Gtk.EventBox → Gtk.Box
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)

        # GTK4: modify_bg → CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(
            b"box { background-color: %s; }" %
            style.COLOR_PANEL_GREY.get_html().encode())
        self.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self._css_provider = css_provider

        self.set_spacing(style.DEFAULT_PADDING)
        # GTK4: set_border_width → margins
        self.set_margin_start(style.DEFAULT_PADDING)
        self.set_margin_end(style.DEFAULT_PADDING)
        self.set_margin_top(style.DEFAULT_PADDING)
        self.set_margin_bottom(style.DEFAULT_PADDING)

        icon = Icon(icon_name='go-previous', pixel_size=style.SMALL_ICON_SIZE,
                    fill_color=style.COLOR_TOOLBAR_GREY.get_svg())
        self.append(icon)

        label = Gtk.Label()
        label.set_text(_('Back'))
        label.set_halign(Gtk.Align.START)
        label.set_valign(Gtk.Align.CENTER)
        label.set_hexpand(True)
        self.append(label)

        if Gtk.Widget.get_default_direction() == Gtk.TextDirection.RTL:
            # GTK4: reorder_child not available, use prepend pattern
            # Simply re-add in reverse - icon already first, label already second
            # In RTL, we want label first, icon second
            self.remove(icon)
            self.append(icon)

        # GTK4: enter/leave-notify-event → EventControllerMotion
        motion = Gtk.EventControllerMotion()
        motion.connect('enter', self.__enter_cb)
        motion.connect('leave', self.__leave_cb)
        self.add_controller(motion)

    def __enter_cb(self, controller, x, y):
        self._css_provider.load_from_data(
            b"box { background-color: %s; }" %
            style.COLOR_SELECTION_GREY.get_html().encode())

    def __leave_cb(self, controller):
        self._css_provider.load_from_data(
            b"box { background-color: %s; }" %
            style.COLOR_PANEL_GREY.get_html().encode())
