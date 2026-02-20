from gi.repository import Gdk


def is_x11_backend():
    display = Gdk.Display.get_default()
    if display is None:
        return False
    name = display.get_name()
    if not name:
        return False
    return name.lower().startswith('gdkx11')
