import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

class ThekeSearchResults(Gtk.ListStore):
    def __init__(self):
        super().__init__(str)

    def add_result(self, ref):
        self.append((str(ref),))