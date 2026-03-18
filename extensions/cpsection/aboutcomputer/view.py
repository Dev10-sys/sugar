# coding=utf-8
# Copyright (C) 2008, OLPC
# Copyright (C) 2009 Simon Schampijer
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

from gi.repository import Gtk, Pango
from gi.repository import Gdk

from sugar3.graphics import style

from jarabe import config
from jarabe.controlpanel.sectionview import SectionView


class AboutComputer(SectionView):
    def __init__(self, model, alerts=None):
        SectionView.__init__(self)

        self._model = model

        self.set_margin_start(style.DEFAULT_SPACING * 2)
        self.set_margin_end(style.DEFAULT_SPACING * 2)
        self.set_margin_top(style.DEFAULT_SPACING * 2)
        self.set_margin_bottom(style.DEFAULT_SPACING * 2)
        self.set_spacing(style.DEFAULT_SPACING)

        self._group = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)

        scrollwindow = Gtk.ScrolledWindow()
        scrollwindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(scrollwindow)
        scrollwindow.set_visible(True)

        self._vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scrollwindow.set_child(self._vbox)
        self._vbox.set_visible(True)

        self._setup_identity()

        self._setup_software()
        self._setup_copyright()

    def create_information_box(self, label_text, value_text):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=style.DEFAULT_SPACING)
        label = Gtk.Label(label=label_text)
        label.set_xalign(1.0)
        label.set_yalign(0.0)
        box.append(label)
        self._group.add_widget(label)
        label.set_visible(True)
        value = Gtk.Label(label=value_text)
        value.set_xalign(0.0)
        value.set_yalign(0.0)
        box.append(value)
        value.set_visible(True)
        box.set_visible(True)
        return box

    def _setup_identity(self):
        separator_identity = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self._vbox.append(separator_identity)
        separator_identity.set_visible(True)

        label_identity = Gtk.Label(label=_('Identity'))
        label_identity.set_xalign(0.0)
        label_identity.set_yalign(0.0)
        self._vbox.append(label_identity)
        label_identity.set_visible(True)
        vbox_identity = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox_identity.set_margin_start(style.DEFAULT_SPACING * 2)
        vbox_identity.set_margin_end(style.DEFAULT_SPACING * 2)
        vbox_identity.set_margin_top(style.DEFAULT_SPACING * 2)
        vbox_identity.set_margin_bottom(style.DEFAULT_SPACING * 2)
        vbox_identity.set_spacing(style.DEFAULT_SPACING)

        hardware_model = self._model.get_hardware_model()
        if hardware_model:
            vbox_identity.append(
                self.create_information_box(_('Model:'), hardware_model))

        vbox_identity.append(
            self.create_information_box(_('Serial Number:'),
                                        self._model.get_serial_number()))

        self._vbox.append(vbox_identity)
        vbox_identity.set_visible(True)

    def _setup_software(self):
        separator_software = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self._vbox.append(separator_software)
        separator_software.set_visible(True)

        label_software = Gtk.Label(label=_('Software'))
        label_software.set_xalign(0.0)
        label_software.set_yalign(0.0)
        self._vbox.append(label_software)
        label_software.set_visible(True)
        box_software = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box_software.set_margin_start(style.DEFAULT_SPACING * 2)
        box_software.set_margin_end(style.DEFAULT_SPACING * 2)
        box_software.set_margin_top(style.DEFAULT_SPACING * 2)
        box_software.set_margin_bottom(style.DEFAULT_SPACING * 2)
        box_software.set_spacing(style.DEFAULT_SPACING)

        box_software.append(
            self.create_information_box(_('Build:'),
                                        self._model.get_build_number()))

        box_software.append(
            self.create_information_box(_('Sugar:'),
                                        config.version))

        box_software.append(
            self.create_information_box(_('Firmware:'),
                                        self._model.get_firmware_number()))

        box_software.append(
            self.create_information_box(_('Wireless Firmware:'),
                                        self._model.get_wireless_firmware()))

        days_from_last_update = self._model.days_from_last_update()
        if days_from_last_update >= 0:
            if days_from_last_update > 0:
                msg = _('%d days ago') % days_from_last_update
            else:
                msg = _('Today')

            box_software.append(
                self.create_information_box(_('Last system update:'), msg))

        self._vbox.append(box_software)
        box_software.set_visible(True)

    def _setup_copyright(self):
        separator_copyright = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self._vbox.append(separator_copyright)
        separator_copyright.set_visible(True)

        label_copyright = Gtk.Label(label=_('Copyright and License'))
        label_copyright.set_xalign(0.0)
        label_copyright.set_yalign(0.0)
        self._vbox.append(label_copyright)
        label_copyright.set_visible(True)
        vbox_copyright = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox_copyright.set_margin_start(style.DEFAULT_SPACING * 2)
        vbox_copyright.set_margin_end(style.DEFAULT_SPACING * 2)
        vbox_copyright.set_margin_top(style.DEFAULT_SPACING * 2)
        vbox_copyright.set_margin_bottom(style.DEFAULT_SPACING * 2)
        vbox_copyright.set_spacing(style.DEFAULT_SPACING)

        copyright_text = '© 2006-2020 One Laptop per Child Association Inc,' \
                         ' Sugar Labs Inc, Red Hat Inc, Collabora Ltd and' \
                         ' Contributors.'
        label_copyright = Gtk.Label(label=copyright_text)
        label_copyright.set_xalign(0.0)
        label_copyright.set_yalign(0.0)
        
        display = Gdk.Display.get_default()
        monitor = display.get_monitors().get_item(0)
        geometry = monitor.get_geometry()
        label_copyright.set_size_request(geometry.width / 2, -1)
        label_copyright.set_line_wrap(True)
        label_copyright.set_visible(True)
        vbox_copyright.append(label_copyright)

        # TRANS: The word "Sugar" should not be translated.
        info_text = _('Sugar is the graphical user interface that you are'
                      ' looking at. Sugar is free software, covered by the'
                      ' GNU General Public License, and you are welcome to'
                      ' change it and/or distribute copies of it under'
                      ' certain conditions described therein.')
        label_info = Gtk.Label(label=info_text)
        label_info.set_xalign(0.0)
        label_info.set_yalign(0.0)
        label_info.set_max_width_chars(80)
        label_info.set_line_wrap(True)
        label_info.set_size_request(geometry.width / 2, -1)
        label_info.set_visible(True)
        vbox_copyright.append(label_info)

        expander = Gtk.Expander(label=_('Full license:'))
        expander.connect('notify::expanded', self.license_expander_cb)
        expander.set_visible(True)
        vbox_copyright.append(expander)

        # display secondary licenses, if any
        for license_text in self._model.get_secondary_licenses():
            label_license = Gtk.Label(label=license_text)
            label_license.set_xalign(0.0)
            label_license.set_yalign(0.0)
            label_license.set_line_wrap(True)
            label_license.set_size_request(geometry.width / 2, -1)
            label_license.set_visible(True)

            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            vbox_copyright.append(separator)
            separator.set_visible(True)
            vbox_copyright.append(label_license)

        self._vbox.append(vbox_copyright)
        vbox_copyright.set_visible(True)

    def license_expander_cb(self, expander, param_spec):
        # load/destroy the license viewer on-demand, to avoid storing the
        # GPL in memory at all times
        if expander.get_expanded():
            view_license = Gtk.TextView()
            view_license.set_editable(False)
            view_license.get_buffer().set_text(self._model.get_license())
            # GTK4: modify_font removed; use CSS instead
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(b'textview { font-family: Monospace; }')
            view_license.get_style_context().add_provider(
                css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            view_license.set_visible(True)
            expander.set_child(view_license)
        else:
            expander.get_child().destroy()
