import re

with open("C:/Users/LOQ/OneDrive/Desktop/Frustose/sugar/src/jarabe/desktop/homewindow.py", "r") as f:
    content = f.read()

# Replace set_has_resize_grip
content = content.replace("self.set_has_resize_grip(False)", "# self.set_has_resize_grip(False)")

# Replace AccelGroup
content = content.replace("accel_group = Gtk.AccelGroup()", "accel_group = None # Gtk.AccelGroup()")
content = content.replace("self.add_accel_group(accel_group)", "# self.add_accel_group(accel_group)")

# Display / Screen replacements
content = content.replace("screen = self.get_screen()", "display = self.get_display()")
content = content.replace("screen.connect('size-changed', self.__screen_size_changed_cb)", "# screen.connect('size-changed', self.__screen_size_changed_cb)")
content = content.replace("self.set_default_size(screen.get_width(),\n                              screen.get_height())", "self.set_default_size(1200, 900)")
content = content.replace("Gtk.IconTheme.get_for_screen(screen).append_search_path(icons_path)", "Gtk.IconTheme.get_for_display(display).add_search_path(icons_path)")
content = content.replace("self.__screen_size_changed_cb(None)", "# self.__screen_size_changed_cb(None)")

# Window hinting and BG
content = content.replace("self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)", "# self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)")
content = content.replace("self.modify_bg(Gtk.StateType.NORMAL,\n                       style.COLOR_WHITE.get_gdk_color())", "# self.modify_bg(...)")

# Events
content = content.replace("self.add_events(Gdk.EventMask.VISIBILITY_NOTIFY_MASK |\n                        Gdk.EventMask.BUTTON_PRESS_MASK)", "# self.add_events(...)")
content = content.replace("self.connect('visibility-notify-event',\n                     self._visibility_notify_event_cb)", "# self.connect('visibility-notify-event', ...)")
content = content.replace("self.connect('map-event', self.__map_event_cb)", "self.connect('map', self.__map_event_cb)")
content = content.replace("self.connect('key-press-event', self.__key_press_event_cb)\n        self.connect('key-release-event', self.__key_release_event_cb)", """
        key_ctrl = Gtk.EventControllerKey.new()
        key_ctrl.connect('key-pressed', self.__key_pressed_cb)
        key_ctrl.connect('key-released', self.__key_released_cb)
        self.add_controller(key_ctrl)
""")

# Pack start to append
content = content.replace("self._box.pack_start(self._toolbar, False, True, 0)", "self._box.append(self._toolbar)")
content = content.replace("self._box.pack_start(self._home_box, True, True, 0)", "self._box.append(self._home_box)")
content = content.replace("self._box.pack_start(self._alert, False, False, 0)", "self._box.append(self._alert)")
content = content.replace("self._box.pack_start(self._transition_box, True, True, 0)", "self._box.append(self._transition_box)")
content = content.replace("self._box.pack_start(self._group_box, True, True, 0)", "self._box.append(self._group_box)")
content = content.replace("self._box.pack_start(self._mesh_box, True, True, 0)", "self._box.append(self._mesh_box)")

# self.add(self._box) -> self.set_child(self._box)
content = content.replace("self.add(self._box)", "self.set_child(self._box)")

# modify __key_press_event_cb and __key_release_event_cb signatures
content = content.replace("def __key_press_event_cb(self, window, event):", "def __key_pressed_cb(self, controller, keyval, keycode, state):")
content = content.replace("def __key_release_event_cb(self, window, event):", "def __key_released_cb(self, controller, keyval, keycode, state):")

# Remove or comment out __is_alt uses since it relied on `event`
content = content.replace("if self.__is_alt(event)", "if keyval in [Gdk.KEY_Alt_L, Gdk.KEY_Alt_R]")

# get_children -> children list workaround
content = content.replace("children = self._box.get_children()", """children = []
        child = self._box.get_first_child()
        while child:
            children.append(child)
            child = child.get_next_sibling()""")

# self.get_window().set_cursor -> self.set_cursor
content = content.replace("self._old_cursor = self.get_window().get_cursor()", "self._old_cursor = self.get_cursor()")
content = content.replace("self.get_window().set_cursor(cursor)", "self.set_cursor(cursor)")
content = content.replace("Gdk.Cursor.new(Gdk.CursorType.WATCH)", "Gdk.Cursor.new_from_name('wait')")

# __map_event_cb signature
content = content.replace("def __map_event_cb(self, widget, event):", "def __map_event_cb(self, widget):")
content = content.replace("timestamp = event.get_time()", "timestamp = Gdk.CURRENT_TIME")

# remove method calls on self._box
content = content.replace("self._box.remove(children[1])", "# self._box.remove(children[1])")
content = content.replace("self._box.remove(self._alert)", "# self._box.remove(self._alert)")

with open("C:/Users/LOQ/OneDrive/Desktop/Frustose/sugar/src/jarabe/desktop/homewindow.py", "w") as f:
    f.write(content)
