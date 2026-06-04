import re

with open("C:/Users/LOQ/OneDrive/Desktop/Frustose/sugar/src/jarabe/desktop/viewtoolbar_orig_utf8.py", "r", encoding="utf-8") as f:
    content = f.read()

# Subclass Gtk.Box instead of Gtk.Toolbar
content = content.replace("class ViewToolbar(Gtk.Toolbar):", "class ViewToolbar(Gtk.Box):")
content = content.replace("Gtk.Toolbar.__init__(self)", "Gtk.Box.__init__(self)")

# Replace insert with append
content = content.replace("self.insert(tool_item, -1)", "self.append(tool_item)")
content = content.replace("self.insert(toolitem, -1)", "self.append(toolitem)")
content = content.replace("self.insert(self._list_button, -1)", "self.append(self._list_button)")
content = content.replace("self.insert(separator, -1)", "self.append(separator)")

# Gtk.ToolItem is gone, use Gtk.Box instead, or just direct
content = content.replace("tool_item = Gtk.ToolItem()", "tool_item = Gtk.Box()")
content = content.replace("toolitem = Gtk.ToolItem()", "toolitem = Gtk.Box()")
content = content.replace("Gtk.SeparatorToolItem()", "Gtk.Separator()")
content = content.replace("toolitem.add(", "toolitem.append(")
content = content.replace("tool_item.add(", "tool_item.append(")
content = content.replace("self._button_box.add(", "self._button_box.append(")

# Separator expand / draw
content = content.replace("separator.props.draw = False", "# separator.props.draw = False")
content = content.replace("separator.set_expand(True)", "separator.set_hexpand(True)")

# layouts_grid.pack_start
content = content.replace("layouts_grid.pack_start(layout_item, True, False, 0)", "layouts_grid.append(layout_item)")
content = content.replace("layouts_grid.show_all()", "pass # layouts_grid.show_all()")

# write to actual viewtoolbar.py
with open("C:/Users/LOQ/OneDrive/Desktop/Frustose/sugar/src/jarabe/desktop/viewtoolbar.py", "w", encoding="utf-8") as f:
    f.write(content)
