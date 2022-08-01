import logging

from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import WebKit2

import threading

import theke
import theke.uri
import theke.index
import theke.externalCache

logger = logging.getLogger(__name__)

from theke.gui.widget_ThekeWebView import ThekeWebView
from theke.gui.widget_ReduceExpandButton import ReduceExpandButton
from theke.gui.widget_ThekeLocalSearchBar import ThekeLocalSearchBar

@Gtk.Template.from_file('./theke/gui/templates/ThekeDocumentView.glade')
class ThekeDocumentView(Gtk.Paned):
    __gtype_name__ = "ThekeDocumentView"

    __gsignals__ = {
        'document-load-changed': (GObject.SIGNAL_RUN_LAST, None,
                      (object, object)),
        'webview-mouse-target-changed': (GObject.SIGNAL_RUN_LAST, None,
                      (object, object, int)),
        'navigation-error': (GObject.SignalFlags.RUN_LAST, None, (int,)),
        'webview-scroll-changed': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,)),
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

    def __init__(self, application, navigator) -> None:
        logger.debug("ThekeDocumentView - Create a new instance")

        super().__init__()

        self._app = application
        self._navigator = navigator

        self._webview = ThekeWebView(self._app, self._navigator)
        self._webview_findController = self._webview.get_find_controller()

        self._setup_view()
        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        #   ... navigtor
        self._navigator.connect("navigation-error", self._navigator_navigation_error_cb)
        #   ... document view
        self.connect("notify::local-search-mode-active", self._local_search_mode_active_cb)
        # ... document view > webview: where the document is displayed
        self._webview.connect("load_changed", self._document_load_changed_cb)
        self._webview.connect("mouse-target-changed", self._webview_mouse_target_changed_cb)
        # ... document view > webview > find controller
        self._webview_findController.connect("found-text", self._local_search_found_text_cb)
        self._webview_findController.connect("failed-to-find-text", self._local_search_failed_to_find_text_cb)
        self._webview.connect("scroll-changed", self._webview_scroll_changed_cb)

    def _setup_view(self) -> None:
        self.bind_property(
            "local-search-mode-active", self._ThekeLocalSearchBar, "search-mode-active",
            GObject.BindingFlags.BIDIRECTIONAL
            | GObject.BindingFlags.SYNC_CREATE)

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

    def open_uri(self, uri) -> None:
        """Open a given uri
        """
        self._navigator.goto_uri(uri)
    
    def open_ref(self, ref) -> None:
        """Open a given ref
        """
        self._navigator.goto_ref(ref)

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
        """Go to the selected item of the toc
        """
        model, treeIter = tree_selection.get_selected()

        if treeIter is not None:
            uri = model[treeIter][1]

            if (uri & self.uri) & theke.uri.comparison.SAME_BASE_URI != theke.uri.comparison.SAME_BASE_URI:
                self._navigator.goto_uri(model[treeIter][1])

    ### Callbacks (from the navigator)
    def _navigator_navigation_error_cb(self, object, error) -> None:
        self.emit("navigation-error", error)

    ### Other callbacks (from _webview)
    def _document_load_changed_cb(self, web_view, load_event):
        """Handle the load changed signal of the document view

        This callback is run before mainWindow._documentView_load_changed_cb().
        """
        if load_event == WebKit2.LoadEvent.STARTED:
            # Update the table of content
            if self._navigator.doc.toc is None:
                self.hide_toc()

        if load_event == WebKit2.LoadEvent.FINISHED:
            # Update the table of content
            if self._navigator.doc.toc is not None:
                self.set_title(self._navigator.doc.title)
                self.set_content(self._navigator.doc.toc.toc)

                if self._navigator.doc.toc.type == theke.TYPE_BIBLE:
                    # Trick: as a biblical toc is the list of chapters
                    #        the index of a chapter is its value -1
                    self._toc_treeSelection.select_path(Gtk.TreePath(self._navigator._currentDocument.ref.chapter-1))

                self.show_toc()

            # # If a verse is given, scroll to it
            # if self._navigator.ref and self._navigator.ref.type == theke.TYPE_BIBLE and self._navigator.ref.verse is not None:
            #     self._webview.scroll_to_verse(self._navigator.ref.verse)

        self.emit("document-load-changed", web_view, load_event)

    def _webview_scroll_changed_cb(self, object, uri):
        self.emit("webview-scroll-changed", uri)

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
            WebKit2.FindOptions.WRAP_AROUND | WebKit2.FindOptions.CASE_INSENSITIVE
            , 100)
        self._ThekeLocalSearchBar.resetCount = True

    def _local_search_found_text_cb(self, find_controller, match_count) -> None:
        # Update the count only after a new search
        # and not when the user goes to the next or previous result
        if self._ThekeLocalSearchBar.resetCount:
            self._ThekeLocalSearchBar.display_match_count(match_count)
            self._ThekeLocalSearchBar.resetCount = False

    def _local_search_failed_to_find_text_cb(self, find_controller) -> None:
        self._ThekeLocalSearchBar.display_match_count(0)

    ### API
    def soft_refresh_document_async(self) -> None:
        """Soft refresh the current document.

        - If this is a document loaded from the cache, reclean it
        """
        logger.debug("Soft refresh the document")
        sources = self._navigator.doc.sources
        
        if sources and sources[0].type == theke.index.SOURCETYPE_EXTERN:
            self._navigator.set_loading(True, "Actualisation de la mise en page")

            def _do_cleaning():
                theke.externalCache._build_clean_document(sources[0].name)
                GLib.idle_add(self._navigator.reload)

            thread = threading.Thread(target=_do_cleaning, daemon=True)
            thread.start()

    def hard_refresh_document(self) -> None:
        """Hard refresh the current document.

        - If this is a document loaded from the cache, redownload it and reclean it
        """
        logger.debug("Hard refresh the document")
        sources = self._navigator.doc.sources
        
        if sources and sources[0].type == theke.index.SOURCETYPE_EXTERN:
            self._navigator.set_loading(True)
            contentUri = self._navigator.index.get_source_uri(sources[0].name)

            if theke.externalCache.cache_document_from_external_source(sources[0].name, contentUri):
                # Success to cache the document from the external source
                theke.externalCache._build_clean_document(sources[0].name)
                self._navigator.reload()

            else:
                self._navigator.set_loading(False)
                self.emit("navigation-error", theke.NavigationErrors.EXTERNAL_SOURCE_INACCESSIBLE)

    def goto_next_chapter(self):
        if self._navigator.doc.type == theke.TYPE_BIBLE:
            if self._navigator.props.ref.chapter < self._navigator.props.ref.nbOfChapters:
                logger.debug("Goto to next biblical chapter")
                self._navigator.props.ref.chapter += 1
                self._navigator.reload()

    def goto_previous_chapter(self):
        if self._navigator.doc.type == theke.TYPE_BIBLE:
            if self._navigator.props.ref.chapter > 1:
                logger.debug("Goto to previous biblical chapter")
                self._navigator.props.ref.chapter -= 1
                self._navigator.reload()

    ### API of the local search bar
    def local_search_bar_has_focus(self) -> bool:
        return self._ThekeLocalSearchBar._search_bar.has_focus()

    def local_search_bar_grab_focus(self) -> None:
        self._ThekeLocalSearchBar._search_bar.grab_focus()

    ### API of the webview

    def grabe_focus(self) -> None:
        self._webview.grab_focus()

    def export_document(self, window) -> None:
        if self._webview.has_focus():
            # Save the current document in a html file
            logger.debug("Export the current document...")

            dialog = Gtk.FileChooserDialog("Exporter le document", window,
                Gtk.FileChooserAction.SAVE,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
            dialog.set_current_name("{}.mhtml".format(self._navigator.doc.title))

            response = dialog.run()

            if response == Gtk.ResponseType.OK:
                logger.debug("Export the current document in %s", dialog.get_filename())
                file = Gio.File.new_for_path(dialog.get_filename())
                self._webview.save_to_file(file, WebKit2.SaveMode.MHTML, None, None, None)

            elif response == Gtk.ResponseType.CANCEL:
                logger.debug("Export the current document [canceled]")

            dialog.destroy()

    def update_scroll(self, scrolled_value) -> None:
        """Update scroll

        If this is a biblical document, scroll to the given verse
        Else, scroll to the given value
        """
        if (self._navigator.doc.type == theke.TYPE_BIBLE 
            and self._navigator.doc.ref.get_verse() > 0):
            self.scroll_to_verse(self._navigator.doc.ref.get_verse())

        else:            
            # Scrolling to 0 is most often counterproductive
            # For example, it prevents to jump to an anchor given in an uri
            if scrolled_value > 0:
                self.set_scrolled_value(scrolled_value)
    
    def set_scrolled_value(self, value) -> None:
        logger.debug("Set scrolled value: %d", value)
        self._webview.scroll_to_value(value)

    def scroll_to_verse(self, verse) -> None:
        self._webview.scroll_to_verse(verse)

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


    # Public properties
    @GObject.Property(type=object)
    def doc(self):
        """The current documment
        """
        return self._navigator.doc

    @GObject.Property(type=str)
    def title(self):
        """Title of the current documment
        """
        return self._navigator.doc.title

    @GObject.Property(type=str)
    def shortTitle(self):
        """Short title of the current documment
        """
        return self._navigator.doc.shortTitle
    
    @GObject.Property(type=str)
    def type(self):
        """Type of the current documment
        """
        return self._navigator.doc.type
    
    @GObject.Property(type=str)
    def availableSources(self):
        """Available sources of the current documment
        """
        return self._navigator.doc.availableSources
    
    @GObject.Property(type=object)
    def selectedSources(self):
        """List of selected sources
        """
        return self._navigator.doc.sources

    @GObject.Property(type=object)
    def uri(self):
        """URI of the current documment (with sources)
        """
        return self._navigator.doc.uri
