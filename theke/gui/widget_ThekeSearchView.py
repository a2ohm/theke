from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Pango

import theke
import theke.searchResults
import theke.sword

from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

ResultData = namedtuple('resultData', ['reference', 'referenceType', 'nbOfResults'])

@Gtk.Template.from_file('./theke/gui/templates/ThekeSearchView.glade')
class ThekeSearchView(Gtk.Bin):
    __gtype_name__ = "ThekeSearchView"

    __gsignals__ = {
        'selection-changed': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,)),
        'start': (GObject.SIGNAL_RUN_FIRST, None,
                      (str, str)),
        'finish': (GObject.SIGNAL_RUN_FIRST, None,
                      ())
        }

    isReduce = GObject.Property(type=bool, default=True)

    _reduceExpand_button = Gtk.Template.Child()
    _title_label = Gtk.Template.Child()
    _close_button = Gtk.Template.Child()

    _results_window = Gtk.Template.Child()
    _results_treeView = Gtk.Template.Child()
    

    def __init__(self, *args, **kwargs) -> None:
        logger.debug("ThekeSearchPane - Create a new instance")

        super().__init__(*args, **kwargs)

        self.results = None

        self._setup_view()

    def _setup_view(self) -> None:
        # Setup the reference column
        cellrenderertext = Gtk.CellRendererText()
        cellrenderertext.set_property("ellipsize", Pango.EllipsizeMode.END)

        column = Gtk.TreeViewColumn("Référence", cellrenderertext, text=0)
        column.set_expand(True)

        self._results_treeView.append_column(column)

        # Setup the number of results column
        cellrenderertext = Gtk.CellRendererText()
        cellrenderertext.set_property("foreground", "grey")

        column = Gtk.TreeViewColumn("", cellrenderertext, text=2)
        self._results_treeView.append_column(column)

        # Setup the expand/reduce button
        self._reduceExpand_button.set_orientation(self._reduceExpand_button.ORIENTATION_LEFT)

    ### Callbacks (from glade)
    @Gtk.Template.Callback()
    def _close_button_clicked_cb(self, button) -> None:
        self.hide()

    @Gtk.Template.Callback()
    def _reduceExpand_button_clicked_cb(self, button) -> None:
        if self.props.isReduce:
            self.expand()
        else:
            self.reduce()

    @Gtk.Template.Callback()
    def _results_treeSelection_changed_cb(self, tree_selection) -> None:
        model, treeIter = tree_selection.get_selected()

        if treeIter is not None:
            if model.iter_has_child(treeIter):
                tree_selection.unselect_all()
            else:
                self.emit("selection-changed", ResultData(*model[treeIter]))
    
    ### Others
    def _search_callback(self, results):
        logger.debug("ThekeSearchPane - Load search results in the SearchPane")

        self.results = theke.searchResults.ThekeSearchResults()
        self._results_treeView.set_model(self.results)

        for bookName, rawReferences in results.items():
            self.results.add(bookName, rawReferences, theke.TYPE_BIBLE)

        logger.debug("ThekeSearchPane - End of the search")
        self.emit("finish")    
    ###

    def search_start(self, moduleName, keyword):
        self.emit("start", moduleName, keyword)
        logger.debug("ThekeSearchPane - Start a search: %s in %s", keyword, moduleName)
        theke.sword.bibleSearch_keyword_async(moduleName, keyword, self._search_callback)

    def show(self):
        super().show()
        if self.isReduce:
            self.expand()

    def expand(self):
        self.props.isReduce = False
        self._results_window.show()
        self._title_label.show()
        self._close_button.show()
        self._reduceExpand_button.switch()

    def reduce(self):
        self.props.isReduce = True
        self._results_window.hide()
        self._title_label.hide()
        self._close_button.hide()
        self._reduceExpand_button.switch()
