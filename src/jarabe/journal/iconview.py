# Copyright (C) 2013, Gonzalo Odiard
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
import time
from gettext import gettext as _

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gdk

from jarabe.journal.iconmodel import IconModel
from sugar4.graphics.icon import Icon
from jarabe.journal import model
from sugar4.graphics.objectchooser import get_preview_pixbuf
from sugar4.graphics import style
from sugar4.activity.activity import PREVIEW_SIZE


def _set_css_bg(widget, color):
    css_provider = Gtk.CssProvider()
    css = "* { background-color: %s; }" % color.get_html()
    css_provider.load_from_data(css.encode())
    context = widget.get_style_context()
    context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


class PreviewRenderer(Gtk.CellRendererPixbuf):

    def __init__(self, **kwds):
        Gtk.CellRendererPixbuf.__init__(self, **kwds)
        self._preview_data = None

    def set_preview_data(self, data):
        self._preview_data = data

    def do_snapshot(self, snapshot, widget, background_area, cell_area, flags):
        pixbuf = get_preview_pixbuf(self._preview_data)
        if pixbuf:
            self.props.texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        else:
            self.props.texture = None
        Gtk.CellRendererPixbuf.do_snapshot(self, snapshot, widget, background_area,
                                         cell_area, flags)

    def do_get_size(self, widget, cell_area):
        x_offset, y_offset, width, height = Gtk.CellRendererPixbuf.do_get_size(
            self, widget, cell_area)
        width = PREVIEW_SIZE[0]
        height = PREVIEW_SIZE[1]
        return (x_offset, y_offset, width, height)


class PreviewIconView(Gtk.IconView):

    def __init__(self, title_col, preview_col):
        Gtk.IconView.__init__(self)

        self._preview_col = preview_col
        self._title_col = title_col

        self.set_spacing(3)

        _preview_renderer = PreviewRenderer()
        _preview_renderer.props.xalign = 0.5
        _preview_renderer.props.yalign = 0.5
        self.pack_start(_preview_renderer, False)
        self.set_cell_data_func(_preview_renderer,
                                self._preview_data_func, None)

        _title_renderer = Gtk.CellRendererText()
        _title_renderer.props.xalign = 0.5
        _title_renderer.props.yalign = 0.5
        self.pack_start(_title_renderer, True)
        self.set_cell_data_func(_title_renderer,
                                self._title_data_func, None)

    def _preview_data_func(self, view, cell, store, i, data):
        preview_data = store.get_value(i, self._preview_col)
        cell.set_preview_data(preview_data)

    def _title_data_func(self, view, cell, store, i, data):
        title = store.get_value(i, self._title_col)
        cell.props.markup = title


class IconView(Gtk.Box):
    __gtype_name__ = 'JournalBaseIconView'

    __gsignals__ = {
        'clear-clicked': (GObject.SignalFlags.RUN_FIRST, None, ([])),
        'entry-activated': (GObject.SignalFlags.RUN_FIRST,
                            None, ([str])),
    }

    def __init__(self, toolbar):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self._query = {}
        self._model = None
        self._progress_bar = None
        self._last_progress_bar_pulse = None
        self._scroll_position = 0.
        self._toolbar = toolbar

        self.connect('map', self.__map_cb)
        self.connect('unrealize', self.__unrealize_cb)
        self.connect('destroy', self.__destroy_cb)

        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_policy(Gtk.PolicyType.NEVER,
                                         Gtk.PolicyType.AUTOMATIC)
        self._scrolled_window.set_vexpand(True)
        self.append(self._scrolled_window)
        self._scrolled_window.set_visible(True)

        self.icon_view = PreviewIconView(IconModel.COLUMN_TITLE,
                                         IconModel.COLUMN_PREVIEW)
        self.icon_view.connect('item-activated', self.__item_activated_cb)

        click = Gtk.GestureClick()
        click.connect('released', self.__button_release_event_cb)
        self.icon_view.add_controller(click)

        self._scrolled_window.set_child(self.icon_view)
        self.icon_view.set_visible(True)

        # Auto-update stuff
        self._fully_obscured = True
        self._dirty = False
        self._refresh_idle_handler = None

        model.created.connect(self.__model_created_cb)
        model.updated.connect(self.__model_updated_cb)
        model.deleted.connect(self.__model_deleted_cb)

    def __button_release_event_cb(self, gesture, n_press, x, y):
        path = self.icon_view.get_path_at_pos(int(x), int(y))
        if path is None:
            return False
        uid = self.icon_view.get_model()[path][IconModel.COLUMN_UID]
        self.emit('entry-activated', uid)
        return False

    def __item_activated_cb(self, icon_view, path):
        uid = icon_view.get_model()[path][IconModel.COLUMN_UID]
        self.emit('entry-activated', uid)

    def _thumb_data_func(self, view, cell, store, i, data):
        preview_data = store.get_value(i, IconModel.COLUMN_PREVIEW)
        pixbuf = get_preview_pixbuf(preview_data)
        if pixbuf:
            cell.props.texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        else:
            cell.props.texture = None

    def __model_created_cb(self, sender, signal, object_id):
        if self._is_new_item_visible(object_id):
            self._set_dirty()

    def __model_updated_cb(self, sender, signal, object_id):
        if self._is_new_item_visible(object_id):
            self._set_dirty()

    def __model_deleted_cb(self, sender, signal, object_id):
        if self._is_new_item_visible(object_id):
            self._set_dirty()

    def _is_new_item_visible(self, object_id):
        """Check if the created item is part of the currently selected view"""
        if self._query['mountpoints'] == ['/']:
            return not object_id.startswith('/')
        return object_id.startswith(self._query['mountpoints'][0])

    def __destroy_cb(self, widget):
        if self._model is not None:
            self._model.stop()

    def update_with_query(self, query_dict):
        if 'order_by' not in query_dict:
            query_dict['order_by'] = ['+timestamp']
        self._query = query_dict
        self.refresh()

    def refresh(self):
        self._stop_progress_bar()

        if self._model is not None:
            self._model.stop()
        self._dirty = False

        self._model = IconModel(self._query)
        self._model.connect('ready', self.__model_ready_cb)
        self._model.connect('progress', self.__model_progress_cb)
        self._model.setup()

    def __model_ready_cb(self, tree_model):
        self._stop_progress_bar()

        self._scroll_position = self.icon_view.props.vadjustment.props.value
        logging.debug('IconView.__model_ready_cb %r', self._scroll_position)

        # Cannot set it up earlier because will try to access the model
        # and it needs to be ready.
        self.icon_view.set_model(self._model)

        self.icon_view.props.vadjustment.props.value = self._scroll_position
        # vadjustment.value_changed is gone or automatic, no need to call it

        if len(tree_model) == 0:
            documents_path = model.get_documents_path()
            if self._is_query_empty():
                if self._query['mountpoints'] == ['/']:
                    self._show_message(_('Your Journal is empty'))
                elif documents_path and self._query['mountpoints'] == \
                        [documents_path]:
                    self._show_message(_('Your documents folder is empty'))
                else:
                    self._show_message(_('The device is empty'))
            else:
                self._show_message(
                    _('No matching entries'),
                    show_clear_query=self._toolbar.is_filter_changed())
        else:
            self._clear_message()

    def __map_cb(self, widget):
        logging.debug('IconView.__map_cb %r', self._scroll_position)
        self.icon_view.props.vadjustment.props.value = self._scroll_position

    def __unrealize_cb(self, widget):
        self._scroll_position = self.icon_view.props.vadjustment.props.value
        logging.debug('IconView.__map_cb %r', self._scroll_position)

    def _is_query_empty(self):
        # FIXME: This is a hack, we shouldn't have to update this every time
        # a new search term is added.
        return not (self._query.get('query') or self._query.get('mime_type') or
                    self._query.get('keep') or self._query.get('mtime') or
                    self._query.get('activity'))

    def __model_progress_cb(self, tree_model):
        if self._progress_bar is None:
            self._start_progress_bar()

        if time.time() - self._last_progress_bar_pulse > 0.05:
            self._progress_bar.pulse()
            self._last_progress_bar_pulse = time.time()

    def _start_progress_bar(self):
        alignment = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        alignment.set_halign(Gtk.Align.CENTER)
        alignment.set_valign(Gtk.Align.CENTER)
        
        while self.get_first_child():
            self.remove(self.get_first_child())
            
        self.append(alignment)
        alignment.set_visible(True)

        self._progress_bar = Gtk.ProgressBar()
        self._progress_bar.props.pulse_step = 0.01
        self._last_progress_bar_pulse = time.time()
        alignment.append(self._progress_bar)
        self._progress_bar.set_visible(True)

    def _stop_progress_bar(self):
        if self._progress_bar is None:
            return
        while self.get_first_child():
            self.remove(self.get_first_child())
        self.append(self._scrolled_window)
        self._progress_bar = None

    def _show_message(self, message, show_clear_query=False):
        while self.get_first_child():
            self.remove(self.get_first_child())

        background_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        background_box.set_hexpand(True)
        background_box.set_vexpand(True)
        _set_css_bg(background_box, style.COLOR_WHITE)
        self.append(background_box)

        alignment = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        alignment.set_halign(Gtk.Align.CENTER)
        alignment.set_valign(Gtk.Align.CENTER)
        alignment.set_hexpand(True)
        alignment.set_vexpand(True)
        background_box.append(alignment)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        alignment.append(box)

        icon = Icon(pixel_size=style.LARGE_ICON_SIZE,
                    icon_name='activity-journal',
                    stroke_color=style.COLOR_BUTTON_GREY.get_svg(),
                    fill_color=style.COLOR_TRANSPARENT.get_svg())
        icon.set_hexpand(True)
        icon.set_vexpand(True)
        box.append(icon)

        label = Gtk.Label()
        color = style.COLOR_BUTTON_GREY.get_html()
        label.set_markup('<span weight="bold" color="%s">%s</span>' % (
            color, GLib.markup_escape_text(message)))
        label.set_hexpand(True)
        label.set_vexpand(True)
        box.append(label)

        if show_clear_query:
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            button_box.set_halign(Gtk.Align.CENTER)
            button_box.set_margin_top(style.DEFAULT_SPACING)
            box.append(button_box)
            button_box.set_visible(True)

            button = Gtk.Button(label=_('Clear search'))
            button.connect('clicked', self.__clear_button_clicked_cb)
            
            icon_img = Icon(icon_name='dialog-cancel',
                            pixel_size=style.SMALL_ICON_SIZE)
            
            box_img = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            box_img.append(icon_img)
            lbl = Gtk.Label(label=_('Clear search'))
            box_img.append(lbl)
            button.set_child(box_img)

            button_box.append(button)

        background_box.set_visible(True)
        alignment.set_visible(True)
        box.set_visible(True)
        icon.set_visible(True)
        label.set_visible(True)

    def __clear_button_clicked_cb(self, button):
        self.emit('clear-clicked')

    def _clear_message(self):
        if self.get_first_child() == self._scrolled_window:
            return
        while self.get_first_child():
            self.remove(self.get_first_child())
        self.append(self._scrolled_window)
        self._scrolled_window.set_visible(True)

    def _set_dirty(self):
        if self._fully_obscured:
            self._dirty = True
        else:
            self.refresh()

    def set_is_visible(self, visible):
        if visible != self._fully_obscured:
            return

        logging.debug('canvas_visibility_notify_event_cb %r', visible)
        if visible:
            self._fully_obscured = False
            if self._dirty:
                self.refresh()
        else:
            self._fully_obscured = True
