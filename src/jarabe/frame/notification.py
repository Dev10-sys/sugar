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

import logging
import textwrap
from gettext import gettext as _

from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Graphene

from sugar3 import profile
from sugar3.graphics import style
from sugar3.graphics.xocolor import XoColor
from sugar3.graphics.icon import Icon
from sugar3.graphics.icon import get_surface
from sugar3.graphics.palette import Palette
from sugar3.graphics.palettemenu import PaletteMenuItem
from sugar3.graphics.palettemenu import PaletteMenuItemSeparator
from sugar3.graphics.toolbutton import ToolButton

from jarabe.model import notifications
from jarabe.view.pulsingicon import PulsingIcon
from jarabe.frame.frameinvoker import FrameWidgetInvoker


class NotificationBox(Gtk.Box):

    LINES = 3
    MAX_ENTRIES = 3
    ELLIPSIS_AND_BREAKS = 6

    def __init__(self, name):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self._name = name

        self._notifications_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL)
        self._notifications_box.set_visible(True)

        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_child(self._notifications_box)
        self._scrolled_window.set_policy(Gtk.PolicyType.NEVER,
                                         Gtk.PolicyType.AUTOMATIC)
        self._scrolled_window.set_visible(True)

        separator = PaletteMenuItemSeparator()
        separator.set_visible(True)

        clear_item = PaletteMenuItem(_('Clear notifications'), 'dialog-cancel')
        clear_item.connect('activate', self.__clear_cb)
        clear_item.set_visible(True)

        self.append(self._scrolled_window)
        self.append(separator)
        self.append(clear_item)

        self._service = notifications.get_service()
        entries = self._service.retrieve_by_name(self._name)

        if entries:
            for entry in entries:
                self._add(entry['summary'], entry['body'])

        self._service.notification_received.connect(
            self.__notification_received_cb)

        self.connect('destroy', self.__destroy_cb)

    def _update_scrolled_size(self):
        # GTK4: iterate children manually
        children = []
        child = self._notifications_box.get_first_child()
        while child is not None:
            children.append(child)
            child = child.get_next_sibling()

        height = 0
        for entry in children[:self.MAX_ENTRIES]:
            _min_size, natural_size = entry.get_preferred_size()
            height += natural_size.height

        self._scrolled_window.set_size_request(-1, height)

    def _add(self, summary, body):
        icon = Icon()
        icon.props.icon_name = 'emblem-notification'
        icon.props.pixel_size = style.SMALL_ICON_SIZE
        icon.props.xo_color = \
            XoColor('%s,%s' % (style.COLOR_WHITE.get_svg(),
                               style.COLOR_BLACK.get_svg()))
        icon.set_visible(True)

        summary_label = Gtk.Label()
        summary_label.set_max_width_chars(style.MENU_WIDTH_CHARS)
        summary_label.set_ellipsize(style.ELLIPSIZE_MODE_DEFAULT)
        summary_label.set_xalign(0)
        summary_label.set_yalign(0.5)
        summary_label.set_markup('<b>%s</b>' % summary)
        summary_label.set_visible(True)

        body_label = Gtk.Label()
        body_label.set_xalign(0)
        body_label.set_yalign(0.5)

        if hasattr(body_label, 'set_lines'):
            body_label.set_max_width_chars(style.MENU_WIDTH_CHARS)
            body_label.set_wrap(True)
            body_label.set_ellipsize(style.ELLIPSIZE_MODE_DEFAULT)
            body_label.set_lines(self.LINES)
            body_label.set_justify(Gtk.Justification.FILL)
        else:
            body_width = self.LINES * style.MENU_WIDTH_CHARS
            body_width -= self.ELLIPSIS_AND_BREAKS
            body = body.replace('\n', ' ')
            if len(body) > body_width:
                body = ' '.join(body[:body_width].split(' ')[:-1]) + '...'
            body = textwrap.fill(body, width=style.MENU_WIDTH_CHARS)

        body_label.set_text(body)
        body_label.set_visible(True)

        grid = Gtk.Grid()
        grid.set_margin_start(style.DEFAULT_SPACING)
        grid.set_margin_end(style.DEFAULT_SPACING)
        grid.set_margin_top(style.DEFAULT_SPACING)
        grid.set_margin_bottom(style.DEFAULT_SPACING)
        grid.set_column_spacing(style.DEFAULT_SPACING)
        grid.set_row_spacing(0)
        grid.attach(icon, 0, 0, 1, 2)
        grid.attach(summary_label, 1, 0, 1, 1)
        grid.attach(body_label, 1, 1, 1, 1)
        grid.set_visible(True)

        self._notifications_box.append(grid)
        self._update_scrolled_size()
        self.set_visible(True)

    def __clear_cb(self, clear_item):
        logging.debug('NotificationBox.__clear_cb')
        # GTK4: remove children by iterating
        child = self._notifications_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self._notifications_box.remove(child)
            child = next_child
        self._service.clear_by_name(self._name)
        self.set_visible(False)

    def __notification_received_cb(self, **kwargs):
        logging.debug('NotificationBox.__notification_received_cb')
        if kwargs.get('app_name', '') == self._name:
            self._add(kwargs.get('summary', ''), kwargs.get('body', ''))

    def __destroy_cb(self, box):
        logging.debug('NotificationBox.__destroy_cb')
        service = notifications.get_service()
        service.notification_received.disconnect(
            self. __notification_received_cb)


class NotificationButton(ToolButton):

    def __init__(self, name):
        ToolButton.__init__(self)
        self._name = name
        self._icon = None
        self.set_palette_invoker(FrameWidgetInvoker(self))
        self.palette_invoker.cache_palette = False
        self.connect('clicked', self.__clicked_cb)

    def set_icon(self, icon):
        self._icon = icon
        self._icon.set_visible(True)
        self.set_icon_widget(self._icon)

    def show_badge(self):
        if self._icon:
            self._icon.show_badge()

    def hide_badge(self):
        if self._icon:
            self._icon.hide_badge()

    def create_palette(self):
        notification_box = NotificationBox(self._name)
        palette = Palette(self._name)
        palette.set_group_id('frame')
        palette.set_content(notification_box)
        self.set_palette(palette)

    def __clicked_cb(self, button):
        self.create_palette()
        self.palette.popup(immediate=True)


class NotificationPulsingIcon(PulsingIcon):

    def __init__(self, filename=None, name=None, colors=None):
        PulsingIcon.__init__(self, pixel_size=style.STANDARD_ICON_SIZE)
        self._badge = None

        if filename:
            self.props.file = filename
        elif name:
            self.props.icon_name = name
        else:
            self.props.icon_name = 'application-octet-stream'

        if not colors:
            colors = profile.get_color()
        self.props.base_color = colors
        self.props.pulse_color = \
            XoColor('%s,%s' % (style.COLOR_BUTTON_GREY.get_svg(),
                               style.COLOR_TOOLBAR_GREY.get_svg()))

    def show_badge(self):
        self._badge = get_surface(icon_name='emblem-notification',
                                  stroke_color=style.COLOR_WHITE.get_svg(),
                                  fill_color=style.COLOR_BLACK.get_svg(),
                                  width=self.get_badge_size(),
                                  height=self.get_badge_size())

    def hide_badge(self):
        self._badge = None

    def do_snapshot(self, snapshot):
        # GTK4: Use snapshot API instead of cairo draw
        PulsingIcon.do_snapshot(self, snapshot)
        if self._badge:
            width = self.get_width()
            height = self.get_height()

            # XXX assume icon is centered in its container
            offset = int(self.props.pixel_size / 2) - self.get_badge_size()
            x = int(width / 2) + offset
            y = int(height / 2) + offset

            badge_size = self.get_badge_size()
            rect = Graphene.Rect.alloc()
            rect.init(x, y, badge_size, badge_size)
            # Paint the badge texture via snapshot
            snapshot.append_texture(self._badge, rect)


class NotificationIcon(Gtk.Box):
    __gtype_name__ = 'SugarNotificationIcon'

    __gproperties__ = {
        'xo-color': (object, None, None, GObject.ParamFlags.READWRITE),
        'icon-name': (str, None, None, None, GObject.ParamFlags.READWRITE),
        'icon-filename': (str, None, None, None, GObject.ParamFlags.READWRITE),
    }

    _PULSE_TIMEOUT = 3

    def __init__(self, **kwargs):
        self._icon = NotificationPulsingIcon()
        self._icon.props.pixel_size = style.STANDARD_ICON_SIZE

        Gtk.Box.__init__(self, **kwargs)

        self._icon.props.pulse_color = \
            XoColor('%s,%s' % (style.COLOR_BUTTON_GREY.get_svg(),
                               style.COLOR_TRANSPARENT.get_svg()))
        self._icon.props.pulsing = True
        self.append(self._icon)
        self._icon.set_visible(True)

        GLib.timeout_add_seconds(self._PULSE_TIMEOUT,
                                 self.__stop_pulsing_cb)

        self.set_size_request(style.GRID_CELL_SIZE, style.GRID_CELL_SIZE)

        # GTK4: Add click controller for button-release-event replacement
        click_controller = Gtk.GestureClick()
        click_controller.connect('released', self.__click_released_cb)
        self.add_controller(click_controller)

    def __click_released_cb(self, gesture, n_press, x, y):
        # This replaces 'button-release-event' signal
        # Subclasses/users can connect to this via the gesture
        pass

    def __stop_pulsing_cb(self):
        self._icon.props.pulsing = False
        return False

    def do_set_property(self, pspec, value):
        if pspec.name == 'xo-color':
            if self._icon.props.base_color != value:
                self._icon.props.base_color = value
        elif pspec.name == 'icon-name':
            if self._icon.props.icon_name != value:
                self._icon.props.icon_name = value
        elif pspec.name == 'icon-filename':
            if self._icon.props.file != value:
                self._icon.props.file = value

    def do_get_property(self, pspec):
        if pspec.name == 'xo-color':
            return self._icon.props.base_color
        if pspec.name == 'icon-name':
            return self._icon.props.icon_name
        if pspec.name == 'icon-filename':
            return self._icon.props.file

    def _set_palette(self, palette):
        self._icon.palette = palette

    def _get_palette(self):
        return self._icon.palette

    palette = property(_get_palette, _set_palette)

    def show_badge(self):
        self._icon.show_badge()

    def hide_badge(self):
        self._icon.hide_badge()


class NotificationWindow(Gtk.Window):
    __gtype_name__ = 'SugarNotificationWindow'

    def __init__(self, **kwargs):

        Gtk.Window.__init__(self, **kwargs)

        self.set_decorated(False)
        self.set_resizable(False)

        # GTK4: Use CSS for background color instead of modify_bg
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(
            b"window { background-color: %s; }" %
            style.COLOR_TOOLBAR_GREY.get_html().encode())
        self.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
