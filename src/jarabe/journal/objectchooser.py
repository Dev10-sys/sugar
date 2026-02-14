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

from gettext import gettext as _
import logging

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk
#from gi.repository import Wnck

from sugar4.graphics import style
from sugar4.graphics.toolbutton import ToolButton
from sugar4.graphics.objectchooser import FILTER_TYPE_MIME_BY_ACTIVITY

from jarabe.journal.listview import BaseListView
from jarabe.journal.listmodel import ListModel
from jarabe.journal.journaltoolbox import MainToolbox
from jarabe.journal.volumestoolbar import VolumesToolbar
from jarabe.model import bundleregistry

from jarabe.journal.iconview import IconView


class ObjectChooser(Gtk.Window):

    __gtype_name__ = 'ObjectChooser'

    __gsignals__ = {
        'response': (GObject.SignalFlags.RUN_FIRST, None, ([int])),
    }

    def __init__(self, parent=None, what_filter='', filter_type=None,
                 show_preview=False):
        Gtk.Window.__init__(self)
        self.set_decorated(False)
        self.set_margin_start(style.LINE_WIDTH)
        self.set_margin_end(style.LINE_WIDTH)
        self.set_margin_top(style.LINE_WIDTH)
        self.set_margin_bottom(style.LINE_WIDTH)

        self._selected_object_id = None
        self._show_preview = show_preview

        self.connect('close-request', self.__delete_event_cb)

        key_controller = Gtk.EventControllerKey()
        key_controller.connect('key-pressed', self.__key_press_event_cb)
        self.add_controller(key_controller)

        if parent is not None:
            self.set_transient_for(parent)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(vbox)

        title_box = TitleBox(what_filter, filter_type)
        title_box.connect('volume-changed', self.__volume_changed_cb)
        title_box.close_button.connect('clicked',
                                       self.__close_button_clicked_cb)
        title_box.set_size_request(-1, style.GRID_CELL_SIZE)
        vbox.append(title_box)

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.append(separator)

        self._toolbar = MainToolbox(default_what_filter=what_filter,
                                    default_filter_type=filter_type)
        self._toolbar.connect('query-changed', self.__query_changed_cb)
        self._toolbar.set_size_request(-1, style.GRID_CELL_SIZE)
        vbox.append(self._toolbar)

        if not self._show_preview:
            self._list_view = ChooserListView(self._toolbar)
            self._list_view.connect('entry-activated',
                                    self.__entry_activated_cb)
            self._list_view.connect('clear-clicked', self.__clear_clicked_cb)
            vbox.append(self._list_view)
            self._list_view.set_vexpand(True)
        else:
            self._icon_view = IconView(self._toolbar)
            self._icon_view.connect('entry-activated',
                                    self.__entry_activated_cb)
            self._icon_view.connect('clear-clicked', self.__clear_clicked_cb)
            vbox.append(self._icon_view)
            self._icon_view.set_vexpand(True)

        self._toolbar.update_filters('/', what_filter, filter_type)


    def __entry_activated_cb(self, list_view, uid):
        self._selected_object_id = uid
        self.emit('response', Gtk.ResponseType.ACCEPT)

    def __delete_event_cb(self, chooser):
        self.emit('response', Gtk.ResponseType.DELETE_EVENT)

    def __key_press_event_cb(self, controller, keyval, keycode, state):
        keyname = Gdk.keyval_name(keyval)
        if keyname == 'Escape':
            self.emit('response', Gtk.ResponseType.DELETE_EVENT)

    def __close_button_clicked_cb(self, button):
        self.emit('response', Gtk.ResponseType.DELETE_EVENT)

    def get_selected_object_id(self):
        return self._selected_object_id

    def __query_changed_cb(self, toolbar, query):
        if not self._show_preview:
            self._list_view.update_with_query(query)
        else:
            self._icon_view.update_with_query(query)

    def __volume_changed_cb(self, volume_toolbar, mount_point):
        logging.debug('Selected volume: %r.', mount_point)
        self._toolbar.set_mount_point(mount_point)


    def __clear_clicked_cb(self, list_view):
        self._toolbar.clear_query()


class TitleBox(VolumesToolbar):
    __gtype_name__ = 'TitleBox'

    def __init__(self, what_filter='', filter_type=None):
        VolumesToolbar.__init__(self)

        label = Gtk.Label()
        title = _('Choose an object')
        if filter_type == FILTER_TYPE_MIME_BY_ACTIVITY:
            registry = bundleregistry.get_registry()
            bundle = registry.get_bundle(what_filter)
            if bundle is not None:
                title = _('Choose an object to open with %s activity') % \
                    bundle.get_name()

        label.set_markup('<b>%s</b>' % title)
        label.set_xalign(0)
        label.set_yalign(0.5)
        self._add_widget(label, expand=True)

        self.close_button = ToolButton(icon_name='dialog-cancel')
        self.close_button.set_tooltip(_('Close'))
        self.insert(self.close_button, -1)
        self.close_button.show()

    def _add_widget(self, widget, expand=False):
        if expand:
            widget.set_hexpand(True)
        self.append(widget)


class ChooserListView(BaseListView):
    __gtype_name__ = 'ChooserListView'

    __gsignals__ = {
        'entry-activated': (GObject.SignalFlags.RUN_FIRST,
                            None,
                            ([str])),
    }

    def __init__(self, toolbar):
        BaseListView.__init__(self, None)
        self._toolbar = toolbar

        self.tree_view.props.hover_selection = True

        gesture = Gtk.GestureClick()
        gesture.connect('released',
                               self.__button_release_event_cb)
        self.tree_view.add_controller(gesture)

    def _can_clear_query(self):
        return self._toolbar.is_filter_changed()

    def _favorite_clicked_cb(self, cell, path):
        pass

    def create_palette(self, path, column):
        # We don't want show the palette in the object chooser
        return None

    def __button_release_event_cb(self, gesture, n_press, x, y):
        # uid = self._model[tree_iter][ListModel.COLUMN_UID]
        # self.emit('entry-activated', uid)
        # Actually we need the path at pos
        pos = self.tree_view.get_path_at_pos(int(x), int(y))
        if pos is None:
            return

        path, column_, x_, y_ = pos
        uid = self.tree_view.get_model()[path][ListModel.COLUMN_UID]
        self.emit('entry-activated', uid)
