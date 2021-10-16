import logging
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk
from gi.repository import WebKit2

import theke
import theke.reference

from theke.gui.widget_ThekeWebView import ThekeWebView
from theke.gui.widget_ThekeGotoBar import ThekeGotoBar
from theke.gui.widget_ThekeHistoryBar import ThekeHistoryBar
from theke.gui.widget_ThekeSearchPane import ThekeSearchPane
from theke.gui.widget_ThekeSourcesBar import ThekeSourcesBar
from theke.gui.widget_ThekeTableOfContent import ThekeTableOfContent
from theke.gui.widget_ThekeToolsView import ThekeToolsView

logger = logging.getLogger(__name__)

class ThekeWindow():
    def __init__(self, navigator):
        self.navigator = navigator

        # UI BUILDING
        builder = Gtk.Builder()
        builder.add_from_file("./theke/gui/theke_mainwindow.glade")
        self.mainWindow = builder.get_object("mainWindow")

        # TOP
        #   = navigation bar
        _top_box = builder.get_object("top_box")

        #   ... historybar: shortcuts to last viewed documents
        self.historybar = ThekeHistoryBar(on_button_clicked_callback = self.on_history_button_clicked)

        #   ... gotobar: entry to open any document
        self.gotobar = ThekeGotoBar()
        self.gotobar.connect("activate", self.handle_gotobar_activate)
        self.gotobar.autoCompletion.connect("match-selected", self.handle_gotobar_match_selected)

        _top_box.pack_end(self.gotobar, False, False, 1)
        _top_box.pack_end(self.historybar, True, True, 1)

        #   ... TOC
        self.tableOfContent = ThekeTableOfContent(builder)
        self.tableOfContent.connect("selection-changed", self.handle_toc_selection_changed)
        
        #   ... document view
        _scrolled_window = builder.get_object("webview_scrolledWindow")

        # ... document view > webview: where the document is displayed
        self.webview = ThekeWebView(navigator=self.navigator)
        self.webview.connect("load_changed", self.handle_load_changed)
        self.webview.connect("mouse_target_changed", self.handle_mouse_target_changed)

        _scrolled_window.add(self.webview)

        #   ... search panel
        self.searchPane = ThekeSearchPane(builder)

        self.searchPane.connect("selection-changed", self.handle_searchResults_selection_changed)
        self.searchPane.connect("start", self.handle_search_start)
        self.searchPane.connect("finish", self.handle_search_finish)

        # Set size.
        builder.get_object("searchPane").connect("notify::max-position", self.handle_maxPosition_changed)
        builder.get_object("tocPane").connect("notify::min-position", self.handle_minPosition_changed)


        # ... tools view
        self.toolsView = ThekeToolsView(builder)
        self.toolsView.search_button_connect(self.handle_morphview_searchButton_clicked)
        self.navigator.connect("click_on_word", self.handle_selected_word_changed)

        # BOTTOM
        #   ... status bar
        self.statusbar = builder.get_object("Statusbar")
        #   ... sources bar
        self.sourcesBar = ThekeSourcesBar(builder)
        self.sourcesBar.connect("source-requested", self.handle_source_requested)
        self.sourcesBar.connect("delete-source", self.handle_delete_source)
        self.navigator.connect("notify::sources", self.handle_sources_updated)
        self.navigator.connect("notify::availableSources", self.handle_availableSources_updated)

        # Set the focus on the webview
        self.webview.grab_focus()

        # SET ACCELERATORS (keyboard shortcuts)
        accelerators = Gtk.AccelGroup()
        self.mainWindow.add_accel_group(accelerators)

        # ... Ctrl+l: give focus to the gotobar
        key, mod = Gtk.accelerator_parse('<Control>l')
        self.gotobar.add_accelerator('grab-focus', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

    def set_application(self, application):
        """Attach the main window to the application
        """
        self.mainWindow.set_application(application)

    def show_all(self):
        """Show the main window
        """
        self.mainWindow.show_all()

    def handle_availableSources_updated(self, object, param) -> None:
        self.sourcesBar.updateAvailableSources(self.navigator.availableSources)

    def handle_delete_source(self, object, sourceName):
        self.navigator.delete_source(sourceName)

    def handle_gotobar_activate(self, entry):
        '''@param entry: the object which received the signal.
        '''

        ref = theke.reference.parse_reference(entry.get_text().strip())
        if ref.type != theke.TYPE_UNKNOWN:
            self.navigator.goto_ref(ref)

    def handle_gotobar_match_selected(self, entry_completion, model, iter):
        # TODO: give name to column (and dont use a numerical value)
        # Update the text in the GotoBar
        self.gotobar.set_text("{} ".format(model.get_value(iter, 0)))

        # Move the cursor to the end
        self.gotobar.set_position(-1)
        return True

    def handle_load_changed(self, web_view, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            # Update the status bar with the title of the just loaded page
            contextId = self.statusbar.get_context_id("navigation")
            self.statusbar.push(contextId, str(self.navigator.title))

            # Update the history bar
            self.historybar.add_uri_to_history(self.navigator.shortTitle, self.navigator.uri)

            # Update the table of content
            if self.navigator.toc is None:
                self.tableOfContent.hide()
            else:
                self.tableOfContent.set_title(self.navigator.ref.documentName)
                self.tableOfContent.set_content(self.navigator.toc.toc)
                self.tableOfContent.show()

            # Hide the morphoView, if necessary
            if not self.navigator.isMorphAvailable:
                self.toolsView.hide()

            # Show the sourcesBar, if necessary
            if self.navigator.ref and self.navigator.ref.type == theke.TYPE_BIBLE:
                self.sourcesBar.show()
                self.statusbar.hide()
            else:
                self.sourcesBar.hide()
                self.statusbar.show()

            if self.navigator.ref and self.navigator.ref.type == theke.TYPE_BIBLE and self.navigator.ref.verse is not None:
                self.webview.scroll_to_verse(self.navigator.ref.verse)

    def handle_mouse_target_changed(self, web_view, hit_test_result, modifiers):
        if hit_test_result.context_is_link():
            context_id = self.statusbar.get_context_id("navigation-next")
            self.statusbar.pop(context_id)
            self.statusbar.push(context_id, "{}".format(hit_test_result.get_link_uri()))
        else:
            context_id = self.statusbar.get_context_id("navigation-next")
            self.statusbar.pop(context_id)

    def handle_morphview_searchButton_clicked(self, button):
        self.searchPane.show()
        self.searchPane.search_start(self.navigator.selectedWord.source, self.navigator.selectedWord.strong)

    def handle_searchResults_selection_changed(self, object, result):
        ref = theke.reference.parse_reference(result.reference, wantedSources = self.navigator.sources)
        
        if ref.type == theke.TYPE_UNKNOWN:
            logger.error("Reference type not supported in search results: %s", result.referenceType)
        else:
            self.navigator.goto_ref(ref)

    def handle_search_start(self, object, moduleName, lemma):
        self.toolsView.search_button.set_sensitive(False)

    def handle_search_finish(self, object):
        self.toolsView.search_button.set_sensitive(True)

    def handle_selected_word_changed(self, instance, param):
        w = self.navigator.selectedWord

        self.toolsView.set_morph(w.word, w.morph)

        self.toolsView.set_lemma(w.lemma)
        self.toolsView.set_strongs(w.strong)

        self.toolsView.show()

    def handle_source_requested(self, object, sourceName):
        self.navigator.add_source(sourceName)

    def handle_sources_updated(self, object, params) -> None:
        self.sourcesBar.updateSources(self.navigator.sources)

    def handle_toc_selection_changed(self, object, tree_selection):
        model, treeIter = tree_selection.get_selected()

        if treeIter is not None:
            self.navigator.goto_section(model[treeIter][1])

    def handle_maxPosition_changed(self, object, param):
        """Move the pane to its maximal value
        """
        object.set_position(object.props.max_position)

    def handle_minPosition_changed(self, object, param):
        """Move the pane to its minimal value
        """
        object.set_position(object.props.min_position)

    def on_history_button_clicked(self, button):
        self.navigator.goto_uri(button.uri)
        return True