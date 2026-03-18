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

from sugar3.graphics import tray
from sugar3.graphics import style

from jarabe.frame import clipboard
from jarabe.frame.clipboardicon import ClipboardIcon


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


    def __init__(self):
        tray.VTray.__init__(self, align=tray.ALIGN_TO_END)
        self._icons = {}
        self._context_map = ContextMap()

        display = Gdk.Display.get_default()
        if display:
            monitor = display.get_monitors().get_item(0)
            geometry = monitor.get_geometry()
            self._max_items = geometry.height // style.GRID_CELL_SIZE - 2
        else:
            self._max_items = 10

        cb_service = clipboard.get_instance()
        cb_service.connect('object-added', self._object_added_cb)
        cb_service.connect('object-deleted', self._object_deleted_cb)

    def owns_clipboard(self):
        for icon in list(self._icons.values()):
            if icon.owns_clipboard:
                return True
        return False

    def _add_selection(self, object_id, selection):
        if not selection.get_data():
            return

        selection_data = selection.get_data()

        selection_type_atom = selection.get_data_type()
        if hasattr(selection_type_atom, 'name'):
            selection_type = selection_type_atom.name()
        else:
            selection_type = str(selection_type_atom)

        logging.debug('ClipboardTray: adding type %r', selection_type)

        cb_service = clipboard.get_instance()
        if selection_type == 'text/uri-list':
            uris = selection.get_uris()
            if len(uris) > 1:
                raise NotImplementedError('Multiple uris in text/uri-list'
                                          ' still not supported.')

            cb_service.add_object_format(object_id,
                                         selection_type,
                                         uris[0],
                                         on_disk=True)
        else:
            cb_service.add_object_format(object_id,
                                         selection_type,
                                         selection_data,
                                         on_disk=False)

    def _object_added_cb(self, cb_service, cb_object):
        if self._icons:
            group = list(self._icons.values())[0]
        else:
            group = None

        icon = ClipboardIcon(cb_object, group)
        self.add_item(icon)
        icon.set_visible(True)
        self._icons[cb_object.get_id()] = icon

        children = []
        child = self.get_first_child()
        while child is not None:
            children.append(child)
            child = child.get_next_sibling()
        objects_to_delete = children[:-self._max_items] if len(children) > self._max_items else []
        for icon in objects_to_delete:
            logging.debug('ClipboardTray: deleting surplus object')
            cb_service = clipboard.get_instance()
            cb_service.delete_object(icon.get_object_id())

        logging.debug('ClipboardTray: %r was added', cb_object.get_id())

    def _object_deleted_cb(self, cb_service, object_id):
        icon = self._icons[object_id]
        self.remove_item(icon)
        del self._icons[object_id]
        # select the last available icon
        if self._icons:
            last_icon = None
            child = self.get_first_child()
            while child is not None:
                last_icon = child
                child = child.get_next_sibling()
            last_icon.props.active = True

        logging.debug('ClipboardTray: %r was deleted', object_id)

    def drag_motion_cb(self, widget, drop, x, y):
        logging.debug('ClipboardTray._drag_motion_cb')

        drag = drop.get_drag()
        if self._internal_drag(drag):
            drop.status(Gdk.DragAction.MOVE)
        else:
            drop.status(Gdk.DragAction.COPY)
            self.props.drag_active = True

        return Gdk.DragAction.COPY

    def drag_leave_cb(self, widget, drop):
        self.props.drag_active = False

    def drag_drop_cb(self, widget, drop, x, y):
        logging.debug('ClipboardTray._drag_drop_cb')

        drag = drop.get_drag()
        if self._internal_drag(drag):
            return False

        cb_service = clipboard.get_instance()
        object_id = cb_service.add_object(name="")

        formats = drop.get_formats()
        mime_types = formats.get_mime_types()
        valid_types = [t for t in mime_types if t not in ('TIMESTAMP', 'TARGETS', 'MULTIPLE')]
        self._context_map.add_context(drop, object_id, len(valid_types))

        for mime_type in valid_types:
            drop.read_value_async(mime_type, 0, None, self._drag_data_received_async, object_id)

        cb_service.set_object_percent(object_id, percent=100)

        return True

    def _drag_data_received_async(self, drop, result, object_id):
        try:
            value = drop.read_value_finish(result)
            if value:
                self._add_selection(object_id, value)
        except Exception as e:
            logging.warn('ClipboardTray: error receiving data: %s', e)
        finally:
            if not self._context_map.has_context(drop):
                drop.finish(Gdk.DragAction.COPY)

    def _internal_drag(self, drag):
        if drag is None:
            return False
        source_widget = drag.get_widget()
        if source_widget is None:
            return False
        view_ancestor = source_widget.get_ancestor(Gtk.Viewport)
        if view_ancestor is self._viewport:
            return True
        return False
