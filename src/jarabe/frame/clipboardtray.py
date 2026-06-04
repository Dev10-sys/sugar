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
from gi.repository import GObject

from sugar4.graphics import tray
from sugar4.graphics import style

from jarabe.frame import clipboard
from jarabe.frame.clipboardicon import ClipboardIcon

def _get_screen_height():
    display = Gdk.Display.get_default()
    if display:
        monitors = display.get_monitors()
        if monitors and monitors.get_n_items() > 0:
            return monitors.get_item(0).get_geometry().height
    return 768


class ContextMap(object):
    """Maps a drag context to the clipboard object involved in the dragging."""

    def __init__(self):
        self._context_map = {}

    def add_context(self, context, object_id, data_types):
        """Establishes the mapping. data_types will serve us for reference-
        counting this mapping.
        """
        self._context_map[context] = [object_id, data_types]

    def get_object_id(self, context):
        """Retrieves the object_id associated with context.
        Will release the association when this function was called as many
        times as the number of data_types that this clipboard object contains.
        """
        [object_id, data_types_left] = self._context_map[context]

        data_types_left = data_types_left - 1
        if data_types_left == 0:
            del self._context_map[context]
        else:
            self._context_map[context] = [object_id, data_types_left]

        return object_id

    def has_context(self, context):
        return context in self._context_map


class ClipboardTray(tray.VTray):

    MAX_ITEMS = _get_screen_height() // style.GRID_CELL_SIZE - 2

    def __init__(self):
        tray.VTray.__init__(self, align=tray.ALIGN_TO_END)
        self._icons = {}

        cb_service = clipboard.get_instance()
        cb_service.connect('object-added', self._object_added_cb)
        cb_service.connect('object-deleted', self._object_deleted_cb)

        formats = Gdk.ContentFormats.new_for_gtype(GObject.TYPE_STRING)
        self._drop_target = Gtk.DropTargetAsync.new(formats, actions=Gdk.DragAction.COPY | Gdk.DragAction.MOVE)
        self._drop_target.connect('drop', self._on_drop_async_cb)
        self.add_controller(self._drop_target)

    def owns_clipboard(self):
        for icon in list(self._icons.values()):
            if icon.owns_clipboard:
                return True
        return False

    def _object_added_cb(self, cb_service, cb_object):
        group = None
        if self._icons:
            group = list(self._icons.values())[0]

        icon = ClipboardIcon(cb_object, group)
        self.add_item(icon)
        icon.set_visible(True)
        self._icons[cb_object.get_id()] = icon

        # Enforce MAX_ITEMS
        children = []
        child = self.get_first_child()
        while child:
            children.append(child)
            child = child.get_next_sibling()

        if len(children) > self.MAX_ITEMS:
            objects_to_delete = children[:-self.MAX_ITEMS]
            for icon_to_delete in objects_to_delete:
                logging.debug('ClipboardTray: deleting surplus object')
                cb_service = clipboard.get_instance()
                cb_service.delete_object(icon_to_delete.get_object_id())

        logging.debug('ClipboardTray: %r was added', cb_object.get_id())

    def _object_deleted_cb(self, cb_service, object_id):
        icon = self._icons.get(object_id)
        if icon:
            self.remove_item(icon)
            del self._icons[object_id]
            
            # select the last available icon
            if self._icons:
                children = []
                child = self.get_first_child()
                while child:
                    children.append(child)
                    child = child.get_next_sibling()
                if children:
                    last_icon = children[-1]
                    if hasattr(last_icon, 'set_active'):
                        last_icon.set_active(True)

        logging.debug('ClipboardTray: %r was deleted', object_id)

    def _on_drop_async_cb(self, target, drop, x, y):
        logging.debug('ClipboardTray._on_drop_async_cb')

        drop.read_text_async(None, self._on_read_text_cb, None)
        return True
        
    def _on_read_text_cb(self, drop, result, user_data):
        try:
            text = drop.read_text_finish(result)
            if text:
                cb_service = clipboard.get_instance()
                object_id = cb_service.add_object(name="")
                cb_service.add_object_format(object_id, "text/plain", text, on_disk=False)
                cb_service.set_object_percent(object_id, percent=100)
        except Exception as e:
            logging.error("Failed to read dropped text: %s", e)
