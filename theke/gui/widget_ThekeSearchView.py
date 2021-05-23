import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import GObject

import theke.searchResults
import theke.sword

class ThekeSearchView(Gtk.TreeView):
    __gsignals__ = {
        'start': (GObject.SIGNAL_RUN_FIRST, None,
                      (str, str)),
        'finish': (GObject.SIGNAL_RUN_FIRST, None,
                      ())
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.set_headers_visible(False)

        column = Gtk.TreeViewColumn("Référence", Gtk.CellRendererText(), text=0)
        self.append_column(column)

        self.show_all()

    def search(self, moduleName, lemma):
        self.emit("start", moduleName, lemma)

    def do_start(self, moduleName, lemma):
        self.results = theke.searchResults.ThekeSearchResults()
        self.set_model(self.results)

        for r in theke.sword.bibleSearch_lemma(moduleName, lemma):
            self.results.add_result(r)

        self.emit("finish")

    def do_finish(self):
        pass


    
