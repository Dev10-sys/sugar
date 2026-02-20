from jarabe.util.backend import is_x11_backend


class WindowBackend:

    def connect_window_opened(self, callback):
        return None

    def connect_window_closed(self, callback):
        return None

    def connect_active_window_changed(self, callback):
        return None

    def get_windows_stacked(self):
        return []

    def get_active_window(self):
        return None

    def toggle_showing_desktop(self, show_desktop):
        return None

    def is_window_dialog(self, window):
        return False

    def is_window_normal(self, window):
        return False

    def is_window_normal_or_splash(self, window):
        return False

    def is_window_state_minimized_changed(self, changed_mask, new_state):
        return False


class X11WindowBackend(WindowBackend):

    def __init__(self):
        from gi.repository import Wnck
        self._Wnck = Wnck
        self._screen = Wnck.Screen.get_default()

    def connect_window_opened(self, callback):
        return self._screen.connect('window-opened', callback)

    def connect_window_closed(self, callback):
        return self._screen.connect('window-closed', callback)

    def connect_active_window_changed(self, callback):
        return self._screen.connect('active-window-changed', callback)

    def get_windows_stacked(self):
        return self._screen.get_windows_stacked()

    def get_active_window(self):
        return self._screen.get_active_window()

    def toggle_showing_desktop(self, show_desktop):
        self._screen.toggle_showing_desktop(show_desktop)

    def is_window_dialog(self, window):
        return window.get_window_type() == self._Wnck.WindowType.DIALOG

    def is_window_normal(self, window):
        return window.get_window_type() == self._Wnck.WindowType.NORMAL

    def is_window_normal_or_splash(self, window):
        return window.get_window_type() in (
            self._Wnck.WindowType.NORMAL,
            self._Wnck.WindowType.SPLASHSCREEN,
        )

    def is_window_state_minimized_changed(self, changed_mask, new_state):
        return changed_mask & self._Wnck.WindowState.MINIMIZED


class DummyWindowBackend(WindowBackend):
    pass


def get_window_backend():
    if is_x11_backend():
        return X11WindowBackend()
    return DummyWindowBackend()
