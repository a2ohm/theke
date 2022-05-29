from gi.repository import Gtk

class ThekeSearchResults(Gtk.TreeStore):
    def __init__(self):
        # Columns
        #   0: (str) document name or reference
        #   1: (int) type of the reference
        #   2: (int) number of results in a given book
        super().__init__(str, int, str)

    def add(self, bookName, rawReferences, referenceType):
        bookIter = self.append(None, [bookName, -1, str(len(rawReferences))])
        for ref in rawReferences:
            self.append(bookIter, [ref, referenceType, ''])