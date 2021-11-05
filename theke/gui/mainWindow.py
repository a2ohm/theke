import logging

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import WebKit2

import theke
import theke.reference

from theke.gui.widget_ThekeGotoBar import ThekeGotoBar
from theke.gui.widget_ThekeHistoryBar import ThekeHistoryBar
from theke.gui.widget_ThekeTableOfContent import ThekeTableOfContent

# Import needed to load the gui
from theke.gui.widget_ThekeSourcesBar import ThekeSourcesBar
from theke.gui.widget_ThekeDocumentView import ThekeDocumentView
from theke.gui.widget_ThekeSearchView import ThekeSearchView
from theke.gui.widget_ThekeToolsBox import ThekeToolsBox

logger = logging.getLogger(__name__)

@Gtk.Template.from_file('./theke/gui/mainWindow.glade')
class ThekeWindow(Gtk.ApplicationWindow):
    __gtype_name__ = "mainWindow"

    __gsignals__ = {
        'save': (GObject.SignalFlags.RUN_LAST | GObject.SignalFlags.ACTION, None, ())
        }

    _top_box: Gtk.Box = Gtk.Template.Child()
    _statusbar: Gtk.Statusbar = Gtk.Template.Child()

    _ThekeSourcesBar: Gtk.Box = Gtk.Template.Child()
    _ThekeDocumentView : Gtk.Paned = Gtk.Template.Child()
    _ThekeSearchView : Gtk.Bin = Gtk.Template.Child()
    _ThekeToolsBox : Gtk.Box = Gtk.Template.Child()

    def __init__(self, navigator):
        super().__init__()

        self._navigator = navigator
        self._setup_view()

        # TODO: Normalement, l'appel de self.show_all() n'est pas nécessaire
        #       car lorsque la fenêtre est créé, la fonction .preset() est appelée
        #       et elle même appelle .show()
        self.show_all()

    def _setup_view(self):

        # TOP
        #   = navigation bar
        #   ... historybar: shortcuts to last viewed documents
        self.historybar = ThekeHistoryBar(on_button_clicked_callback = self.on_history_button_clicked)

        #   ... gotobar: entry to open any document
        self.gotobar = ThekeGotoBar()
        self.gotobar.connect("activate", self.handle_gotobar_activate)
        self.gotobar.autoCompletion.connect("match-selected", self.handle_gotobar_match_selected)

        self._top_box.pack_end(self.gotobar, False, False, 1)
        self._top_box.pack_end(self.historybar, True, True, 1)

        #   ... document view
        self._ThekeDocumentView.finish_setup()
        #   ... document view > TOC
        self._ThekeDocumentView.connect("toc-selection-changed", self.handle_toc_selection_changed)
        # ... document view > webview: where the document is displayed
        self._ThekeDocumentView.register_navigator(self._navigator)
        self._ThekeDocumentView.connect("document-load-changed", self.handle_document_load_changed)
        self._ThekeDocumentView.connect("webview-mouse-target-changed", self.handle_mouse_target_changed)

        #   ... search panel
        #self.searchPane = ThekeSearchPane(builder)
        self._ThekeSearchView.finish_setup()

        self._ThekeSearchView.connect("selection-changed", self.handle_searchResults_selection_changed)
        self._ThekeSearchView.connect("start", self.handle_search_start)
        self._ThekeSearchView.connect("finish", self.handle_search_finish)

        # Set size.
        # builder.get_object("searchPane").connect("notify::max-position", self.handle_maxPosition_changed)

        # ... tools view
        self._ThekeToolsBox.finish_setup()
        self._ThekeToolsBox.search_button_connect(self.handle_morphview_searchButton_clicked)
        self._navigator.connect("click_on_word", self.handle_selected_word_changed)

        # BOTTOM
        #   ... sources bar
        self._ThekeSourcesBar.connect("source-requested", self.handle_source_requested)
        self._ThekeSourcesBar.connect("delete-source", self.handle_delete_source)
        self._navigator.connect("notify::sources", self.handle_sources_updated)
        self._navigator.connect("notify::availableSources", self.handle_availableSources_updated)

        # Set the focus on the webview
        self._ThekeDocumentView.grab_focus()

        # SET ACCELERATORS (keyboard shortcuts)
        accelerators = Gtk.AccelGroup()
        self.add_accel_group(accelerators)

        # ... Ctrl+l: give focus to the gotobar
        key, mod = Gtk.accelerator_parse('<Control>l')
        self.gotobar.add_accelerator('grab-focus', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

        # ... Ctrl+s: save modifications in the personal dictionary
        key, mod = Gtk.accelerator_parse('<Control>s')
        self.add_accelerator('save', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

    ### Callbacks (from glade)
    @Gtk.Template.Callback()
    def _document_toolsBox_pane_max_position_notify_cb(self, object, param) -> None:
        object.set_position(object.props.max_position)

    @Gtk.Template.Callback()
    def _document_search_pane_max_position_notify_cb(self, object, param) -> None:
        object.set_position(object.props.max_position)
    
    ### Signal handlers
    def do_save(self) -> None:
        self._ThekeToolsBox._toolsBox_dicoView.save()
    ###

    def handle_availableSources_updated(self, object, param) -> None:
        self._ThekeSourcesBar.updateAvailableSources(self._navigator.availableSources)

    def handle_delete_source(self, object, sourceName):
        self._navigator.delete_source(sourceName)

    def handle_gotobar_activate(self, entry):
        '''@param entry: the object which received the signal.
        '''

        ref = theke.reference.parse_reference(entry.get_text().strip())
        if ref.type != theke.TYPE_UNKNOWN:
            self._navigator.goto_ref(ref)

    def handle_gotobar_match_selected(self, entry_completion, model, iter):
        # TODO: give name to column (and dont use a numerical value)
        # Update the text in the GotoBar
        self.gotobar.set_text("{} ".format(model.get_value(iter, 0)))

        # Move the cursor to the end
        self.gotobar.set_position(-1)
        return True

    def handle_document_load_changed(self, obj, web_view, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            # Update the status bar with the title of the just loaded page
            contextId = self._statusbar.get_context_id("navigation")
            self._statusbar.push(contextId, str(self._navigator.title))

            # Update the history bar
            self.historybar.add_uri_to_history(self._navigator.shortTitle, self._navigator.uri)

            # Update the table of content
            if self._navigator.toc is None:
                self._ThekeDocumentView.hide_toc()
            else:
                self._ThekeDocumentView.set_title(self._navigator.ref.documentName)
                self._ThekeDocumentView.set_content(self._navigator.toc.toc)
                self._ThekeDocumentView.show_toc()

            # Hide the morphoView, if necessary
            if not self._navigator.isMorphAvailable:
                self._ThekeToolsBox.hide()

            # Show the sourcesBar, if necessary
            if self._navigator.ref and self._navigator.ref.type == theke.TYPE_BIBLE:
                self._ThekeSourcesBar.show()
                self._statusbar.hide()
            else:
                self._ThekeSourcesBar.hide()
                self._statusbar.show()

            if self._navigator.ref and self._navigator.ref.type == theke.TYPE_BIBLE and self._navigator.ref.verse is not None:
                self._ThekeDocumentView.scroll_to_verse(self._navigator.ref.verse)

    def handle_mouse_target_changed(self, obj, web_view, hit_test_result, modifiers):
        if hit_test_result.context_is_link():
            context_id = self._statusbar.get_context_id("navigation-next")
            self._statusbar.pop(context_id)
            self._statusbar.push(context_id, "{}".format(hit_test_result.get_link_uri()))
        else:
            context_id = self._statusbar.get_context_id("navigation-next")
            self._statusbar.pop(context_id)

    def handle_morphview_searchButton_clicked(self, button):
        self._ThekeSearchView.show()
        self._ThekeSearchView.search_start(self._navigator.selectedWord.source, self._navigator.selectedWord.strong)

    def handle_searchResults_selection_changed(self, object, result):
        ref = theke.reference.parse_reference(result.reference, wantedSources = self._navigator.sources)
        
        if ref.type == theke.TYPE_UNKNOWN:
            logger.error("Reference type not supported in search results: %s", result.referenceType)
        else:
            self._navigator.goto_ref(ref)

    def handle_search_start(self, object, moduleName, lemma):
        self._ThekeToolsBox._toolsBox_search_button.set_sensitive(False)

    def handle_search_finish(self, object):
        self._ThekeToolsBox._toolsBox_search_button.set_sensitive(True)

    def handle_selected_word_changed(self, instance, param):
        w = self._navigator.selectedWord

        self._ThekeToolsBox.set_morph(w.word, w.morph)

        self._ThekeToolsBox.set_lemma(w.lemma)
        self._ThekeToolsBox.set_strongs(w.strong)
        self._ThekeToolsBox.show()

    def handle_source_requested(self, object, sourceName):
        self._navigator.add_source(sourceName)

    def handle_sources_updated(self, object, params) -> None:
        self._ThekeSourcesBar.updateSources(self._navigator.sources)

    def handle_toc_selection_changed(self, object, tree_selection):
        model, treeIter = tree_selection.get_selected()

        if treeIter is not None:
            self._navigator.goto_section(model[treeIter][1])

    def handle_maxPosition_changed(self, object, param):
        """Move the pane to its maximal value
        """
        object.set_position(object.props.max_position)

    def on_history_button_clicked(self, button):
        self._navigator.goto_uri(button.uri)
        return True
