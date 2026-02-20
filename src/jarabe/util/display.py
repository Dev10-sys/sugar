from gi.repository import Gdk


def get_primary_geometry():
    display = Gdk.Display.get_default()
    monitor = display.get_primary_monitor()
    if monitor:
        return monitor.get_geometry()
    return None
