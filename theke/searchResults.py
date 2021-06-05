import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

class ThekeSearchResults(Gtk.TreeStore):
    def __init__(self):
        # Columns
        #   0: (str) value
        super().__init__(str)

    def add(self, bookName, rawReferences):
        bookIter = self.append(None, [bookName,])
        for ref in rawReferences:
            self.append(bookIter, [ref,])