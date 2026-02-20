from gi.repository import Gdk


def get_screen_size():
    display = Gdk.Display.get_default()
    if display:
        monitor = display.get_primary_monitor()
        if monitor:
            geometry = monitor.get_geometry()
            return geometry.width, geometry.height

    # fallback safe default
    return 1024, 768


def get_default_display():
    return Gdk.Display.get_default()
