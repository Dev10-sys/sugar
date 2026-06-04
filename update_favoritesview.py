import re

with open("C:/Users/LOQ/OneDrive/Desktop/Frustose/sugar/src/jarabe/desktop/favoritesview.py", "r") as f:
    content = f.read()

# Replace pack_start and pack_end
content = re.sub(r'\.pack_start\((.*?),\s*True,\s*True,\s*0\)', r'.append(\1)', content)
content = re.sub(r'\.pack_start\((.*?),\s*False,\s*True,\s*0\)', r'.append(\1)', content)
content = re.sub(r'\.pack_start\((.*?),\s*False,\s*False,\s*0\)', r'.append(\1)', content)
content = re.sub(r'\.pack_end\((.*?),\s*True,\s*True,\s*0\)', r'.append(\1)', content)

# Events
content = content.replace("self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |\n                        Gdk.EventMask.POINTER_MOTION_HINT_MASK)", "# self.add_events(...)")
content = content.replace("self.drag_dest_set(0, [], 0)", "# self.drag_dest_set(0, [], 0)")

# Reorder child
content = content.replace("self.reorder_child(alert, 0)", "

# DND stubs
content = content.replace("target_entry = Gtk.TargetEntry.new(*_ICON_DND_TARGET)\n            target_list = Gtk.TargetList.new([target_entry])\n            widget.drag_begin(target_list,\n                              Gdk.DragAction.MOVE,\n                              1,\n                              event)", "pass # widget.drag_begin(...)")
content = content.replace("Gtk.drag_set_icon_pixbuf(context, pixbuf, self._hot_x, self._hot_y)", "pass # Gtk.drag_set_icon_pixbuf")
content = content.replace("Gdk.drag_status(context, context.get_suggested_action(), time)", "pass # Gdk.drag_status")
content = content.replace("self.drag_get_data(context, target, time)", "pass # self.drag_get_data")
content = content.replace("Gdk.drop_finish(context, success=True, time_=time)", "pass # Gdk.drop_finish")

# get_children
content = content.replace("for icon in self.get_children():", """children = []
        child = self.get_first_child()
        while child:
            children.append(child)
            child = child.get_next_sibling()
        for icon in children:""")

# time_ / timestamp
content = content.replace("window.activate(Gtk.get_current_event_time())", "window.present() # window.activate(...)")

content = content.replace("self._children.append(child)", "self._children.append(child); self.append(child) # Add to fixed/box")
content = content.replace("if child.get_realized():\n            child.set_parent_window(self.get_parent_window())", "# child.set_parent_window(...)")
content = content.replace("child.set_parent(self)", "# child.set_parent(self)")

with open("C:/Users/LOQ/OneDrive/Desktop/Frustose/sugar/src/jarabe/desktop/favoritesview.py", "w") as f:
    f.write(content)
