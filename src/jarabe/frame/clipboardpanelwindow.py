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
from urllib.parse import urlparse
import hashlib

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

from jarabe.frame.framewindow import FrameWindow
from jarabe.frame.clipboardtray import ClipboardTray

from jarabe.frame import clipboard


class ClipboardPanelWindow(FrameWindow):

    def __init__(self, frame, orientation):
        FrameWindow.__init__(self, orientation)

        self._frame = frame

        # GTK4: Use Display clipboard API instead of Gtk.Clipboard
        display = Gdk.Display.get_default()
        self._clipboard = display.get_clipboard()
        self._clipboard.connect('changed', self._owner_change_cb)

        self._clipboard_tray = ClipboardTray()
        self._clipboard_tray.set_visible(True)
        self.append(self._clipboard_tray)

        # GTK4: Use DropTarget instead of legacy drag_dest_set
        drop_target = Gtk.DropTarget.new(
            GLib.types[GLib.TYPE_STRING] if hasattr(GLib, 'types')
            else GObject.TYPE_STRING,
            Gdk.DragAction.COPY)
        drop_target.connect('drop', self._clipboard_tray.drop_cb)
        drop_target.connect('motion', self._clipboard_tray.drag_motion_cb)
        drop_target.connect('leave', self._clipboard_tray.drag_leave_cb)
        self.add_controller(drop_target)

    def _owner_change_cb(self, gdk_clipboard):
        logging.debug('owner_change_cb')

        if self._clipboard_tray.owns_clipboard():
            return

        cb_service = clipboard.get_instance()

        # GTK4: Read clipboard content asynchronously
        self._clipboard.read_text_async(None, self._on_text_received, cb_service)

    def _on_text_received(self, clipboard, result, cb_service):
        try:
            text = clipboard.read_text_finish(result)
        except Exception:
            logging.debug('No text content in clipboard')
            return

        if text is None:
            return

        data_hash = hash(text.encode())
        key = cb_service.add_object(name="", data_hash=data_hash)
        if key is None:
            return
        cb_service.set_object_percent(key, percent=0)
        cb_service.add_object_format(key, 'text/plain', text.encode(),
                                     on_disk=False)
        cb_service.set_object_percent(key, percent=100)

    def _md5_for_file(self, file_name):
        '''Calculate md5 for file data

        Calculating block wise to prevent issues with big files in memory
        '''
        block_size = 8192
        md5 = hashlib.md5()
        f = open(file_name, 'rb')
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        f.close()
        return md5.digest()
