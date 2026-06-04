import re

with open("C:/Users/LOQ/OneDrive/Desktop/Frustose/sugar/src/jarabe/desktop/favoriteslayout.py", "r") as f:
    content = f.read()

# Replace Gdk.Screen.height()
content = content.replace("Gdk.Screen.height()", "900 # Gdk.Screen.height()")

# Replace size_request() with get_preferred_size()[0]
content = content.replace("size_request()", "get_preferred_size()[0]")

# Replace size_allocate(child_allocation) with size_allocate(child_allocation, -1)
content = content.replace("child.size_allocate(child_allocation)", "child.size_allocate(child_allocation, -1)")
content = content.replace("owner_icon.size_allocate(owner_icon_allocation)", "owner_icon.size_allocate(owner_icon_allocation, -1)")
content = content.replace("activity_icon.size_allocate(activity_icon_allocation)", "activity_icon.size_allocate(activity_icon_allocation, -1)")

with open("C:/Users/LOQ/OneDrive/Desktop/Frustose/sugar/src/jarabe/desktop/favoriteslayout.py", "w") as f:
    f.write(content)
