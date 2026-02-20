"""In-process activity/window registry.

This provides a Wayland-friendly alternative to querying the window manager
for global window state.
"""

from gi.repository import GObject


class ActivityRegistry(GObject.GObject):
    __gsignals__ = {
        'activity-registered': (GObject.SignalFlags.RUN_FIRST, None,
                                ([str, GObject.TYPE_PYOBJECT])),
        'activity-unregistered': (GObject.SignalFlags.RUN_FIRST, None,
                                  ([str])),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self._windows = {}

    def register(self, window, activity_id):
        if activity_id is None:
            raise ValueError('activity_id must be provided')

        key = str(activity_id)
        self._windows[key] = window
        self.emit('activity-registered', key, window)

    def unregister(self, activity_id):
        key = str(activity_id)
        if key in self._windows:
            del self._windows[key]
            self.emit('activity-unregistered', key)

    def list_running(self):
        return list(self._windows.keys())

    def get_window(self, activity_id):
        return self._windows.get(str(activity_id))


_REGISTRY = ActivityRegistry()


def get_registry():
    return _REGISTRY

