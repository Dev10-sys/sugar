# Copyright (C) 2008, OLPC
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
from gi.repository import GObject

from sugar4.graphics import style
from sugar4.graphics.icon import Icon


class InlineAlert(Gtk.Box):
    """UI interface for Inline alerts

    Inline alerts are different from the other alerts beause they are
    no dialogs, they only inform about a current event.

    Properties:
        'msg': the message of the alert,
        'icon': the icon that appears at the far left
    See __gproperties__
    """

    __gtype_name__ = 'SugarInlineAlert'

    __gproperties__ = {
        'msg': (str, None, None, None, GObject.ParamFlags.READWRITE),
        'icon': (object, None, None, GObject.ParamFlags.WRITABLE),
    }

    def __init__(self, **kwargs):
        self._msg = None
        self._msg_color = None
        self._icon = Icon(icon_name='emblem-warning',
                          fill_color=style.COLOR_SELECTION_GREY.get_svg(),
                          stroke_color=style.COLOR_WHITE.get_svg())

        self._msg_label = Gtk.Label()
        self._msg_label.set_max_width_chars(150)
        self._msg_label.set_ellipsize(style.ELLIPSIZE_MODE_DEFAULT)
        # Gtk.Alignment removed, use halign on Label
        self._msg_label.set_halign(Gtk.Align.START)
        self._msg_label.set_valign(Gtk.Align.CENTER)
        
        # CSS to replace modify_fg
        css_provider = Gtk.CssProvider()
        css = "* { color: %s; }" % style.COLOR_SELECTION_GREY.get_html()
        css_provider.load_from_data(css.encode())
        context = self._msg_label.get_style_context()
        context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL, **kwargs)

        self.set_spacing(style.DEFAULT_SPACING)
        
        css_provider_bg = Gtk.CssProvider()
        css_bg = "* { background-color: %s; }" % style.COLOR_WHITE.get_html()
        css_provider_bg.load_from_data(css_bg.encode())
        context_bg = self.get_style_context()
        context_bg.add_provider(css_provider_bg, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.append(self._icon)
        self.append(self._msg_label)
        self._msg_label.set_visible(True)
        self._icon.set_visible(True)

    def do_set_property(self, pspec, value):
        if pspec.name == 'msg':
            if self._msg != value:
                self._msg = value
                self._msg_label.set_markup(self._msg)
        elif pspec.name == 'icon':
            if self._icon != value:
                self._icon = value

    def do_get_property(self, pspec):
        if pspec.name == 'msg':
            return self._msg
