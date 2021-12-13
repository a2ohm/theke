import logging

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import WebKit2

import theke

logger = logging.getLogger(__name__)

from theke.gui.widget_ThekeWebView import ThekeWebView
from theke.gui.widget_ReduceExpandButton import ReduceExpandButton
from theke.gui.widget_ThekeLocalSearchBar import ThekeLocalSearchBar

@Gtk.Template.from_file('./theke/gui/templates/ThekeDocumentView.glade')
class ThekeDocumentView(Gtk.Paned):
    __gtype_name__ = "ThekeDocumentView"

    __gsignals__ = {
        'toc-selection-changed': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,)),
        'document-load-changed': (GObject.SIGNAL_RUN_LAST, None,
                      (object, object)),
        'webview-mouse-target-changed': (GObject.SIGNAL_RUN_LAST, None,
                      (object, object, int)),
        }

    isReduce = GObject.Property(type=bool, default=True)
    local_search_mode_active = GObject.Property(type=bool, default=False)

    _ThekeLocalSearchBar = Gtk.Template.Child()

    _webview_scrolledWindow = Gtk.Template.Child()
    _toc_reduceExpand_button = Gtk.Template.Child()
    _toc_frame = Gtk.Template.Child()
    _toc_title = Gtk.Template.Child()
    _toc_tocWindow = Gtk.Template.Child()
    _toc_treeView = Gtk.Template.Child()
    _toc_treeSelection = Gtk.Template.Child()

    def __init__(self, *args, **kwargs) -> None:
        logger.debug("ThekeDocumentView - Create a new instance")

        super().__init__(*args, **kwargs)

        self._navigator = None
        self._webview = ThekeWebView()
        self._webview_findController = self._webview.get_find_controller()

        self._setup_view()
        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        #   ... document view
        self.connect("notify::local-search-mode-active", self._local_search_mode_active_cb)
        # ... document view > webview: where the document is displayed
        self._webview.connect("load_changed", self._document_load_changed_cb)
        self._webview.connect("mouse-target-changed", self._webview_mouse_target_changed_cb)

    def _setup_view(self) -> None:
        self.bind_property(
            "local-search-mode-active", self._ThekeLocalSearchBar, "search-mode-active",
            GObject.BindingFlags.BIDIRECTIONAL
            | GObject.BindingFlags.SYNC_CREATE)

        self._ThekeLocalSearchBar.finish_setup()

        # Add the webview into the document view
        # (this cannot be done in Glade)
        self._webview_scrolledWindow.add(self._webview)

        # Setup the table of contents
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Chapitre", renderer, text=0)
        self._toc_treeView.append_column(column)

        # Setup the expand/reduce button
        self._toc_reduceExpand_button.set_orientation(self._toc_reduceExpand_button.ORIENTATION_RIGHT)

        # Connect
        self._ThekeLocalSearchBar.connect("notify::search-entry", self._local_search_entry_changed_cb)
        self._ThekeLocalSearchBar.connect("search-next-match", self._local_search_next_match_cb)
        self._ThekeLocalSearchBar.connect("search-previous-match", self._local_search_previous_match_cb)

    def register_navigator(self, navigator):
        self._navigator = navigator
        self._webview.register_navigator(navigator)

    ### Callbacks (from glade)
    @Gtk.Template.Callback()
    def ThekeDocumentView_min_position_notify_cb(self, object, param) -> None:
        object.set_position(object.props.min_position)

    @Gtk.Template.Callback()
    def _toc_reduceExpand_button_clicked_cb(self, button) -> None:
        if self.props.isReduce:
            self.expand_toc()
        else:
            self.reduce_toc()

    @Gtk.Template.Callback()
    def _toc_treeSelection_changed_cb(self, tree_selection):
        self.emit("toc-selection-changed", tree_selection)

    ### Other callbacks (from _webview)
    def _document_load_changed_cb(self, web_view, load_event):
        if load_event == WebKit2.LoadEvent.STARTED:
            # Update the table of content
            if self._navigator.toc is None:
                self.hide_toc()

        if load_event == WebKit2.LoadEvent.FINISHED:
            # Update the table of content
            if self._navigator.toc is not None:
                self.set_title(self._navigator.ref.documentName)
                self.set_content(self._navigator.toc.toc)

                if self._navigator.toc.type == theke.TYPE_BIBLE:
                    # Trick: as a biblical toc is the list of chapters
                    #        the index of a chapter is its value -1
                    self._toc_treeSelection.select_path(Gtk.TreePath(self._navigator.ref.chapter-1))

                self.show_toc()

            # If a verse is given, scroll to it
            if self._navigator.ref and self._navigator.ref.type == theke.TYPE_BIBLE and self._navigator.ref.verse is not None:
                self._webview.scroll_to_verse(self._navigator.ref.verse)

        self.emit("document-load-changed", web_view, load_event)

    def _webview_mouse_target_changed_cb(self, web_view, hit_test_result, modifiers):
        self.emit("webview-mouse-target-changed", web_view, hit_test_result, modifiers)

    ### Other callbacks (local search)

    def _local_search_mode_active_cb(self, object, value) -> None:
        if not self.props.local_search_mode_active:
            self._webview_findController.search_finish()

    def _local_search_next_match_cb(self, object) -> None:
        if self.props.local_search_mode_active:
            self._webview_findController.search_next()

    def _local_search_previous_match_cb(self, object) -> None:
        if self.props.local_search_mode_active:
            self._webview_findController.search_previous()

    def _local_search_entry_changed_cb(self, object, value) -> None:
        self._webview_findController.search(
            self._ThekeLocalSearchBar.search_entry,
            WebKit2.FindOptions.WRAP_AROUND, 100)

    ### API of the local search bar
    def local_search_bar_has_focus(self) -> bool:
        return self._ThekeLocalSearchBar._search_bar.has_focus()

    def local_search_bar_grab_focus(self) -> None:
        self._ThekeLocalSearchBar._search_bar.grab_focus()

    ### API of the webview

    def grabe_focus(self) -> None:
        self._webview.grab_focus()

    # def scroll_to_verse(self, verse) -> None:
    #     self._webview.scroll_to_verse(verse)

    ### API of the TOC

    def show_toc(self) -> None:
        """Show the table of content
        """
        self._toc_frame.show()
        if self.props.isReduce:
            self.expand_toc()
    
    def expand_toc(self) -> None:
        """Expand the table of content
        """
        self.props.isReduce = False
        self._toc_tocWindow.show()
        self._toc_title.show()
        self._toc_reduceExpand_button.switch()

    def hide_toc(self) -> None:
        """Hide the table of content
        """
        self._toc_frame.hide()
        self.props.isReduce = True

    def reduce_toc(self) -> None:
        """Reduce the table of content
        """
        self.props.isReduce = True
        self._toc_tocWindow.hide()
        self._toc_title.hide()
        self._toc_reduceExpand_button.switch()

    def set_title(self, title):
        """Set the title of the table of content
        """
        self._toc_title.set_text(title)

    def set_content(self, content):
        """Set the content of the table of content
        """
        self._toc_treeView.set_model(content)
