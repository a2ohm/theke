import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import GObject

import theke.searchResults
import theke.sword

from collections import namedtuple

resultData = namedtuple('resultData', ['reference'])

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

        self.searchPane_frame = builder.get_object("searchFrame")
        self.searchPane_resultsWindow = builder.get_object("searchPane_resultsWindow")
        self.searchPane_title = builder.get_object("searchPane_title")
        self.results_treeView = builder.get_object("searchPanel_resultsTreeView")
        self.close_button = builder.get_object("searchPane_close_button")
        self.reduceExpand_button = builder.get_object("searchPane_reduceExpand_button")
        self.reduceExpand_image = builder.get_object("searchPane_reduceExpand_image")

        self.isReduce = True

        column = Gtk.TreeViewColumn("Référence", Gtk.CellRendererText(), text=0)
        self.results_treeView.append_column(column)

        self.results_treeView.get_selection().connect("changed", self.handle_results_selection_changed)
        self.reduceExpand_button.connect("clicked", self.handle_reduceExpand_button_clicked)
        self.close_button.connect("clicked", self.handle_close_button_clocked)

    def search_start(self, moduleName, keyword):
        self.emit("start", moduleName, keyword)
        theke.sword.bibleSearch_keyword_async(moduleName, keyword, self.search_callback)

    def search_callback(self, results):
        self.results = theke.searchResults.ThekeSearchResults()
        self.results_treeView.set_model(self.results)

        for bookName, rawReferences in results.items():
            self.results.add(bookName, rawReferences)

        self.emit("finish")

    def show(self):
        self.searchPane_frame.show()
        if self.isReduce:
            self.expand()

    def expand(self):
        self.isReduce = False
        self.searchPane_resultsWindow.show()
        self.searchPane_title.show()
        self.close_button.show()
        self.reduceExpand_image.set_from_icon_name("pan-end-symbolic", Gtk.IconSize.BUTTON)

    def hide(self):
        self.searchPane_frame.hide()
        self.isReduce = True

    def reduce(self):
        self.isReduce = True
        self.searchPane_resultsWindow.hide()
        self.searchPane_title.hide()
        self.close_button.hide()
        self.reduceExpand_image.set_from_icon_name("pan-start-symbolic", Gtk.IconSize.BUTTON)

    def handle_close_button_clocked(self, button):
        self.hide()

    def handle_reduceExpand_button_clicked(self, button):
        if self.isReduce:
            self.expand()
        else:
            self.reduce()

    def handle_results_selection_changed(self, tree_selection):
        model, treeIter = tree_selection.get_selected()

        if treeIter is not None:
            if model.iter_has_child(treeIter):
                tree_selection.unselect_all()
            else:
                self.emit("selection-changed", resultData(*model[treeIter]))