# Copyright (C) 2007, Red Hat, Inc.
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

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

from sugar3.graphics.radiotoolbutton import RadioToolButton
from sugar3.graphics.icon import Icon
from sugar3.graphics.xocolor import XoColor
from sugar3.graphics import style
from sugar3 import profile

from jarabe.frame import clipboard
from jarabe.frame.clipboardmenu import ClipboardMenu
from jarabe.frame.frameinvoker import FrameWidgetInvoker
from jarabe.frame.notification import NotificationIcon
import jarabe.frame


class ClipboardIcon(RadioToolButton):
    __gtype_name__ = 'SugarClipboardIcon'

    def __init__(self, cb_object, group):
        RadioToolButton.__init__(self, group=group)

        self.props.palette_invoker = FrameWidgetInvoker(self)
        self.palette_invoker.props.toggle_palette = True

        self._cb_object = cb_object
        self.owns_clipboard = False
        self.props.sensitive = False
        self.props.active = False
        self._notif_icon = None
        self._current_percent = 0

        self._icon = Icon()
        color = profile.get_color()
        self._icon.props.xo_color = color
        self.set_icon_widget(self._icon)
        self._icon.set_visible(True)

        cb_service = clipboard.get_instance()
        cb_service.connect('object-state-changed',
                           self._object_state_changed_cb)
        cb_service.connect('object-selected', self._object_selected_cb)

        child = self.get_child()
        # GTK4: Use DragSource instead of legacy drag_source_set
        self._drag_source = Gtk.DragSource()
        self._drag_source.connect('prepare', self._drag_prepare_cb)
        self._drag_source.connect('drag-begin', self._drag_begin_handler)
        if child:
            child.add_controller(self._drag_source)
        self.connect('notify::active', self._notify_active_cb)

    def create_palette(self):
        palette = ClipboardMenu(self._cb_object)
        palette.set_group_id('frame')
        return palette

    def get_object_id(self):
        return self._cb_object.get_id()

    def _drag_prepare_cb(self, drag_source, x, y):
        """GTK4: Prepare drag data"""
        formats = self._cb_object.get_formats()
        if not formats:
            return None
        # Get the first available format's data
        for format_type, format_obj in formats.items():
            data = format_obj.get_data()
            if data:
                content = Gdk.ContentProvider.new_for_bytes(
                    format_type, GLib.Bytes.new(data))
                return content
        return None

    def _put_in_clipboard(self):
        logging.debug('ClipboardIcon._put_in_clipboard')

        if self._cb_object.get_percent() < 100:
            raise ValueError('Object is not complete, cannot be put into the'
                             ' clipboard.')

        # GTK4: Use Display clipboard API
        display = Gdk.Display.get_default()
        x_clipboard = display.get_clipboard()

        formats = self._cb_object.get_formats()
        if formats:
            # Get the most significant format and set its data
            for format_type, format_obj in formats.items():
                data = format_obj.get_data()
                if data:
                    if isinstance(data, str):
                        x_clipboard.set_text(data)
                    else:
                        content = Gdk.ContentProvider.new_for_bytes(
                            format_type, GLib.Bytes.new(data))
                        x_clipboard.set_content(content)
                    self.owns_clipboard = True
                    break

    def _clipboard_clear_cb(self):
        logging.debug('ClipboardIcon._clipboard_clear_cb')
        self.owns_clipboard = False

    def _object_state_changed_cb(self, cb_service, cb_object):
        if cb_object != self._cb_object:
            return

        if cb_object.get_icon():
            self._icon.props.icon_name = cb_object.get_icon()
            if self._notif_icon:
                self._notif_icon.props.icon_name = self._icon.props.icon_name
        else:
            self._icon.props.icon_name = 'application-octet-stream'

        # GTK4: DragSource is already set up in __init__

        if cb_object.get_percent() == 100:
            self.props.sensitive = True

        # Clipboard object became complete. Make it the active one.
        percent = cb_object.get_percent()
        if self._current_percent < 100 and percent == 100:
            self.props.active = True
            self.show_notification()

        self._current_percent = percent

    def _object_selected_cb(self, cb_service, object_id):
        if object_id != self._cb_object.get_id():
            return
        self.props.active = True
        self.show_notification()
        logging.debug('ClipboardIcon: %r was selected', object_id)

    def show_notification(self):
        self._notif_icon = NotificationIcon()
        self._notif_icon.props.icon_name = self._icon.props.icon_name
        self._notif_icon.props.xo_color = \
            XoColor('%s,%s' % (self._icon.props.stroke_color,
                               self._icon.props.fill_color))
        frame = jarabe.frame.get_view()
        self._timeout_id = frame.add_notification(
            self._notif_icon, Gtk.CornerType.BOTTOM_LEFT)

        # GTK4: Set up DragSource on notification icon
        notif_drag_source = Gtk.DragSource()
        notif_drag_source.connect('prepare', self._drag_prepare_cb)
        notif_drag_source.connect('drag-begin', self._drag_begin_handler)
        self._notif_icon.add_controller(notif_drag_source)

    def _drag_begin_handler(self, drag_source, drag):
        """GTK4: Handle drag begin"""
        frame = jarabe.frame.get_view()
        self._timeout_id = GLib.timeout_add(
            jarabe.frame.frame.NOTIFICATION_DURATION,
            lambda: frame.remove_notification(self._notif_icon))

        # GTK4: Use IconTheme from display
        display = Gdk.Display.get_default()
        icon_theme = Gtk.IconTheme.get_for_display(display)
        icon_paintable = icon_theme.lookup_icon(
            self._icon.props.icon_name,
            None,  # fallbacks
            style.STANDARD_ICON_SIZE,
            1,  # scale
            Gtk.TextDirection.NONE,
            Gtk.IconLookupFlags.FORCE_REGULAR)
        drag_source.set_icon(icon_paintable,
                             style.STANDARD_ICON_SIZE // 2,
                             style.STANDARD_ICON_SIZE // 2)

    def _notify_active_cb(self, widget, pspec):
        if self.props.active:
            self._put_in_clipboard()
        else:
            self.owns_clipboard = False
