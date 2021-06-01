import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import GObject

import theke.searchResults
import theke.sword

class ThekeSearchPane(GObject.Object):
    __gsignals__ = {
        'selection-changed': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,)),
        'start': (GObject.SIGNAL_RUN_FIRST, None,
                      (str, str)),
        'finish': (GObject.SIGNAL_RUN_FIRST, None,
                      ())
        }

    def __init__(self, builder, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.searchPanel_frame = builder.get_object("searchFrame")
        self.results_treeView = builder.get_object("searchPanel_resultsTreeView")

        column = Gtk.TreeViewColumn("Référence", Gtk.CellRendererText(), text=0)
        self.results_treeView.append_column(column)

        self.results_treeView.get_selection().connect("changed", self.handle_results_selection_changed)

    def search(self, moduleName, lemma):
        self.emit("start", moduleName, lemma)

        self.results = theke.searchResults.ThekeSearchResults()
        self.results_treeView.set_model(self.results)

        for r in theke.sword.bibleSearch_lemma(moduleName, lemma):
            self.results.add_result(r)

        self.emit("finish")

    def show(self):
        self.searchPanel_frame.show()

    def do_start(self, moduleName, lemma):
        pass

    def do_finish(self):
        pass

    def handle_results_selection_changed(self, tree_selection):
        self.emit("selection-changed", tree_selection)

    
