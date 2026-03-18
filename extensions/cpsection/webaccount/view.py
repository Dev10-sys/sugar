# Copyright (C) 2013, Walter Bender - Raul Gutierrez Segales
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

from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gdk

from jarabe.webservice.accountsmanager import get_webaccount_services
from jarabe.controlpanel.sectionview import SectionView

from sugar3.graphics.icon import CanvasIcon, Icon
from sugar3.graphics import style


def get_service_name(service):
    if hasattr(service, '_account'):
        if hasattr(service._account, 'get_description'):
            return service._account.get_description()
    return ''


class WebServicesConfig(SectionView):
    def __init__(self, model, alerts):
        SectionView.__init__(self)

        self._model = model
        self.restart_alerts = alerts

        services = get_webaccount_services()

        grid = Gtk.Grid()

        if len(services) == 0:
            grid.set_row_spacing(style.DEFAULT_SPACING)

            icon = Icon(pixel_size=style.LARGE_ICON_SIZE,
                        icon_name='module-webaccount',
                        stroke_color=style.COLOR_BUTTON_GREY.get_svg(),
                        fill_color=style.COLOR_TRANSPARENT.get_svg())

            grid.attach(icon, 0, 0, 1, 1)
            icon.set_visible(True)

            label = Gtk.Label()
            label.set_justify(Gtk.Justification.CENTER)
            label.set_markup(
                '<span foreground="%s" size="large">%s</span>'
                % (style.COLOR_BUTTON_GREY.get_html(),
                   GLib.markup_escape_text(
                       _('No web services are installed.\n'
                         'Please visit %s for more details.' %
                         'http://wiki.sugarlabs.org/go/WebServices'))))
            label.set_visible(True)
            grid.attach(label, 0, 1, 1, 1)

            grid.set_halign(Gtk.Align.CENTER)
            grid.set_valign(Gtk.Align.CENTER)
            grid.set_visible(True)

            self.set_child(grid)
            return

        grid.set_row_spacing(style.DEFAULT_SPACING * 4)
        grid.set_column_spacing(style.DEFAULT_SPACING * 4)
        grid.set_margin_start(style.DEFAULT_SPACING * 2)
        grid.set_margin_end(style.DEFAULT_SPACING * 2)
        grid.set_margin_top(style.DEFAULT_SPACING * 2)
        grid.set_margin_bottom(style.DEFAULT_SPACING * 2)
        grid.set_column_homogeneous(True)

        display = Gdk.Display.get_default()
        monitor = display.get_monitors().get_item(0)
        geometry = monitor.get_geometry()
        width = geometry.width - 2 * style.GRID_CELL_SIZE
        nx = int(width / (style.GRID_CELL_SIZE + style.DEFAULT_SPACING * 4))

        self._service_config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        x = 0
        y = 0
        for service in services:
            service_grid = Gtk.Grid()
            icon = CanvasIcon(icon_name=service.get_icon_name())
            icon.set_visible(True)
            service_grid.attach(icon, x, y, 1, 1)

            icon.connect('activate', service.config_service_cb, None,
                         self._service_config_box)

            label = Gtk.Label()
            label.set_justify(Gtk.Justification.CENTER)
            name = get_service_name(service)
            label.set_markup(name)
            service_grid.attach(label, x, y + 1, 1, 1)
            label.set_visible(True)

            grid.attach(service_grid, x, y, 1, 1)
            service_grid.set_visible(True)

            x += 1
            if x == nx:
                x = 0
                y += 1

        grid.set_halign(Gtk.Align.CENTER)
        grid.set_valign(Gtk.Align.START)
        grid.set_visible(True)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.append(grid)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox.append(scrolled)

        self.set_child(vbox)
        vbox.set_visible(True)
        scrolled.set_visible(True)

        workspace = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scrolled.set_child(workspace)
        workspace.set_visible(True)

        workspace.append(self._service_config_box)
        self._service_config_box.set_visible(True)

    def undo(self):
        pass
