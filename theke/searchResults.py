from gi.repository import Gtk

class ThekeSearchResults(Gtk.TreeStore):
    def __init__(self):
        # Columns
        #   0: (str) document name or reference
        #   1: (int) type of the reference
        super().__init__(str, int)

    def add(self, bookName, rawReferences, referenceType):
        bookIter = self.append(None, [bookName, -1])
        for ref in rawReferences:
            self.append(bookIter, [ref, referenceType])