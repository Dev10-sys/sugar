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

from jarabe.frame.framewindow import FrameWindow
from jarabe.frame.clipboardtray import ClipboardTray

import jarabe.frame.clipboard as clipboard


class ClipboardPanelWindow(FrameWindow):

    def __init__(self, frame, orientation):
        FrameWindow.__init__(self, orientation)

        self._frame = frame

        # Listening for new clipboard objects
        self._clipboard = Gdk.Display.get_default().get_clipboard()
        self._clipboard.connect('changed', self._owner_change_cb)

        self._clipboard_tray = ClipboardTray()
        self._clipboard_tray.set_visible(True)
        self.append(self._clipboard_tray)


    def _owner_change_cb(self, cb):
        logging.debug('owner_change_cb')

        if self._clipboard_tray.owns_clipboard():
            return

        cb_service = clipboard.get_instance()
        formats = cb.get_formats()

        if formats is None or not formats.get_mime_types():
            return

        cb.read_text_async(None, self._read_text_cb, cb_service)

    def _read_text_cb(self, cb, result, cb_service):
        try:
            text = cb.read_text_finish(result)
            if not text:
                return
            data_hash = hash(text)
            key = cb_service.add_object(name="", data_hash=data_hash)
            if key is None:
                return
            cb_service.set_object_percent(key, percent=0)
            cb_service.add_object_format(key, "text/plain", text, on_disk=False)
            cb_service.set_object_percent(key, percent=100)
        except Exception as e:
            logging.error("Failed to read clipboard: %s", e)

    def _md5_for_file(self, file_name):
        '''Calculate md5 for file data

        Calculating block wise to prevent issues with big files in memory
        '''
        block_size = 8192
        md5 = hashlib.md5()
        f = open(file_name, 'r')
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        f.close()
        return md5.digest()
