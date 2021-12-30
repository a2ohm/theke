import logging

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import WebKit2

import theke
import theke.reference

# Import needed to load the gui
from theke.gui.widget_ThekeHistoryBar import ThekeHistoryBar
from theke.gui.widget_ThekeGotoBar import ThekeGotoBar
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

    local_search_mode_active = GObject.Property(type=bool, default=False)

    _statusbar : Gtk.Statusbar = Gtk.Template.Child()
    _statusbar_revealer : Gtk.Revealer = Gtk.Template.Child()

    _ThekeHistoryBar : Gtk.ButtonBox = Gtk.Template.Child()
    _ThekeGotoBar : Gtk.SearchEntry = Gtk.Template.Child()
    _ThekeSourcesBar: Gtk.Box = Gtk.Template.Child()
    _ThekeDocumentView : Gtk.Paned = Gtk.Template.Child()
    _ThekeSearchView : Gtk.Bin = Gtk.Template.Child()
    _ThekeToolsBox : Gtk.Box = Gtk.Template.Child()

    _loading_spinner : Gtk.Spinner = Gtk.Template.Child()

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
        self._ThekeHistoryBar.set_button_clicked_callback(self.on_history_button_clicked)

        #   ... document view
        #   ... document view > TOC
        self._ThekeDocumentView.connect("toc-selection-changed", self.handle_toc_selection_changed)
        # ... document view > webview: where the document is displayed
        self._ThekeDocumentView.register_navigator(self._navigator)
        self._ThekeDocumentView.connect("document-load-changed", self.handle_document_load_changed)
        self._ThekeDocumentView.connect("webview-mouse-target-changed", self.handle_mouse_target_changed)

        #   ... search panel
        self._ThekeSearchView.connect("selection-changed", self.handle_searchResults_selection_changed)
        self._ThekeSearchView.connect("start", self.handle_search_start)
        self._ThekeSearchView.connect("finish", self.handle_search_finish)

        # ... tools view
        self._ThekeToolsBox.search_button_connect(self.handle_morphview_searchButton_clicked)
        self._navigator.connect("notify::selectedWord", self.handle_selected_word_changed)

        # BOTTOM
        #   ... sources bar
        self._ThekeSourcesBar.connect("source-requested", self.handle_source_requested)
        self._ThekeSourcesBar.connect("delete-source", self.handle_delete_source)

        self._navigator.connect("context-updated", self._navigator_context_updated_cb)

        # SET BINDINGS
        self.bind_property(
            "local-search-mode-active", self._ThekeDocumentView, "local-search-mode-active",
            GObject.BindingFlags.BIDIRECTIONAL
            | GObject.BindingFlags.SYNC_CREATE)
        
        # Set the focus on the webview
        self._ThekeDocumentView.grab_focus()

    ### Callbacks (from glade)
    @Gtk.Template.Callback()
    def mainWindow_key_press_event_cb(self, widget, event) -> None:
        """Handle shortcuts
        """
        modifiers = event.get_state() & Gtk.accelerator_get_default_mod_mask()
        (_, keyval) = event.get_keyval()

        control_mask = Gdk.ModifierType.CONTROL_MASK

        # Ctrl+<KEY>
        if control_mask == modifiers:
            # ... Ctrl+f: open search bar
            if keyval == Gdk.KEY_f:
                searchMode = self.props.local_search_mode_active
                if searchMode and not self._ThekeDocumentView.local_search_bar_has_focus():
                    self._ThekeDocumentView.local_search_bar_grab_focus()
                else:
                    self.props.local_search_mode_active = not searchMode
                return True

            # ... Ctrl+l: give focus to the gotobar
            elif keyval == Gdk.KEY_l:
                self._ThekeGotoBar.grab_focus()
                return True

            # ... Ctrl+s: save modifications in the personal dictionary
            elif keyval == Gdk.KEY_s:
                self.emit("save")
                return True

    @Gtk.Template.Callback()
    def _document_toolsBox_pane_max_position_notify_cb(self, object, param) -> None:
        object.set_position(object.props.max_position)

    @Gtk.Template.Callback()
    def _document_search_pane_max_position_notify_cb(self, object, param) -> None:
        object.set_position(object.props.max_position)

    @Gtk.Template.Callback()
    def _ThekeGotoBar_activate_cb(self, entry):
        '''@param entry: the object which received the signal.
        '''

        ref = theke.reference.parse_reference(entry.get_text().strip())
        if ref.type != theke.TYPE_UNKNOWN:
            self._navigator.goto_ref(ref)
    
    ### Signal handlers
    def do_save(self) -> None:
        self._ThekeToolsBox._toolsBox_dicoView.save()
    ###

    ### Callbacks (_navigator)
    def _navigator_context_updated_cb(self, object, update_type) -> None:
        if update_type == theke.navigator.NEW_DOCUMENT:
            self._ThekeSourcesBar.updateAvailableSources(self._navigator.availableSources)
            self._ThekeSourcesBar.updateSources(self._navigator.sources)

        if update_type == theke.navigator.SOURCES_UPDATED:
            self._ThekeSourcesBar.updateSources(self._navigator.sources)

    ### Callbacks (other)

    def handle_delete_source(self, object, sourceName):
        self._navigator.delete_source(sourceName)

    def handle_document_load_changed(self, obj, web_view, load_event):
        if load_event == WebKit2.LoadEvent.STARTED:
            # Update the status bar with the title of the just loaded page
            contextId = self._statusbar.get_context_id("navigation")
            self._statusbar.push(contextId, "Chargement ...")

            # Show the sourcesBar, if necessary
            if self._navigator.ref and self._navigator.ref.type == theke.TYPE_BIBLE:
                self._ThekeSourcesBar.set_reveal_child(True)
                self._statusbar_revealer.set_reveal_child(False)
            else:
                self._ThekeSourcesBar.set_reveal_child(False)
                self._statusbar_revealer.set_reveal_child(True)

            self._loading_spinner.start()

        elif load_event == WebKit2.LoadEvent.FINISHED:
            # Update the status bar with the title of the just loaded page
            contextId = self._statusbar.get_context_id("navigation")
            self._statusbar.push(contextId, str(self._navigator.title))

            # Update the history bar
            self._ThekeHistoryBar.add_uri_to_history(self._navigator.shortTitle, self._navigator.uri)

            # Hide the morphoView, if necessary
            if not self._navigator.isMorphAvailable:
                self._ThekeToolsBox.hide()

            self._loading_spinner.stop()

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
        self._ThekeSearchView.search_start(self._navigator.selectedWord.source, self._navigator.selectedWord.rawStrong)

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

    def handle_selected_word_changed(self, object, params):
        w = self._navigator.selectedWord

        self._ThekeToolsBox.set_morph(w.word, w.morph)

        self._ThekeToolsBox.set_lemma(w.lemma)
        self._ThekeToolsBox.set_strongs(w.strong)
        self._ThekeToolsBox.show()

    def handle_source_requested(self, object, sourceName):
        self._navigator.add_source(sourceName)

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
