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
        # ... document view > webview: where the document is displayed
        self._ThekeDocumentView.register_navigator(self._navigator)
        self._ThekeDocumentView.connect("document-load-changed", self._documentView_load_changed_cb)
        self._ThekeDocumentView.connect("webview-mouse-target-changed", self._documentView_mouse_target_changed_cb)

        #   ... search panel
        self._ThekeSearchView.connect("selection-changed", self._searchView_selection_changed)
        self._ThekeSearchView.connect("start", self._searchView_start_cb)
        self._ThekeSearchView.connect("finish", self._searchView_finish_cb)

        # ... tools view
        self._ThekeToolsBox.search_button_connect(self._toolsBox_searchButton_clicked_cb)
        self._navigator.connect("notify::selectedWord", self._navigator_selected_word_changed_cb)

        # BOTTOM
        #   ... sources bar
        self._ThekeSourcesBar.connect("source-requested", self._sourceBar_source_requested_cb)
        self._ThekeSourcesBar.connect("delete-source", self._sourceBar_delete_source_cb)

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
                self._ThekeToolsBox._toolsBox_dicoView.save()
                return True

        else:
            if keyval == Gdk.KEY_Escape:
                # If the gotobar has the focus, cancel,
                # fill it with the current reference
                # and give the focus back to the document view
                if self._ThekeGotoBar.has_focus():
                    self.fill_gotobar_with_current_reference()
                    self._ThekeDocumentView.grab_focus()
                    return True

                if self.props.local_search_mode_active:
                    self.props.local_search_mode_active = False
                    return True

    @Gtk.Template.Callback()
    def _pane_max_position_notify_cb(self, object, param) -> None:
        """Set a pane to its maximal position
        """
        object.set_position(object.props.max_position)

    @Gtk.Template.Callback()
    def _ThekeGotoBar_activate_cb(self, entry):
        '''@param entry: the object which received the signal.
        '''

        ref = theke.reference.parse_reference(entry.get_text().strip())
        if ref.type != theke.TYPE_UNKNOWN:
            self._navigator.goto_ref(ref)

    ### Callbacks (_documentView)
    def _documentView_load_changed_cb(self, obj, web_view, load_event):
        """Handle the load changed signal of the document view

        This callback is run after _ThekeDocumentView._document_load_changed_cb().
        """
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

            # Update the goto bar with the current reference
            self.fill_gotobar_with_current_reference()

            # Update the history bar
            self._ThekeHistoryBar.add_uri_to_history(self._navigator.shortTitle, self._navigator.uri)

            # Hide the morphoView, if necessary
            if not self._navigator.isMorphAvailable:
                self._ThekeToolsBox.hide()

            self._loading_spinner.stop()

    def _documentView_mouse_target_changed_cb(self, obj, web_view, hit_test_result, modifiers):
        """Links hovered over by the mouse are shown in the status bar
        """
        if hit_test_result.context_is_link():
            context_id = self._statusbar.get_context_id("navigation-next")
            self._statusbar.pop(context_id)
            self._statusbar.push(context_id, "{}".format(hit_test_result.get_link_uri()))
        else:
            context_id = self._statusbar.get_context_id("navigation-next")
            self._statusbar.pop(context_id)

    ### Callbacks (_navigator)
    def _navigator_context_updated_cb(self, object, update_type) -> None:
        if update_type == theke.navigator.NEW_DOCUMENT:
            self._ThekeSourcesBar.updateAvailableSources(self._navigator.availableSources)
            self._ThekeSourcesBar.updateSources(self._navigator.sources)

        if update_type == theke.navigator.SOURCES_UPDATED:
            self._ThekeSourcesBar.updateSources(self._navigator.sources)

    def _navigator_selected_word_changed_cb(self, object, params):
        """Transmit the selected word to the tools box
        """
        w = self._navigator.selectedWord

        self._ThekeToolsBox.set_morph(w.word, w.morph)

        self._ThekeToolsBox.set_lemma(w.lemma)
        self._ThekeToolsBox.set_strongs(w.strong)
        self._ThekeToolsBox.show()

    ### Callbacks (_searchView)
    def _searchView_selection_changed(self, object, result):
        """Goto to the selected search result
        """
        ref = theke.reference.parse_reference(result.reference, wantedSources = self._navigator.sources)
        self._navigator.goto_ref(ref)  

    def _searchView_start_cb(self, object, moduleName, lemma):
        self._ThekeToolsBox._toolsBox_search_button.set_sensitive(False)

    def _searchView_finish_cb(self, object):
        self._ThekeToolsBox._toolsBox_search_button.set_sensitive(True)  

    ### Callbacks (_sourceBar)
    def _sourceBar_delete_source_cb(self, object, sourceName):
        self._navigator.delete_source(sourceName)
    
    def _sourceBar_source_requested_cb(self, object, sourceName):
        self._navigator.add_source(sourceName)

    ### Callbacks (_toolsBox)
    def _toolsBox_searchButton_clicked_cb(self, button):
        self._ThekeSearchView.show()
        self._ThekeSearchView.search_start(self._navigator.selectedWord.source, self._navigator.selectedWord.rawStrong)

    ### Callbacks (other)
    def on_history_button_clicked(self, button):
        self._navigator.goto_uri(button.uri)
        return True

    def fill_gotobar_with_current_reference(self) -> None:
        """Fill the gotobar with the current reference
        """
        if self._navigator.ref.type in [theke.TYPE_BOOK, theke.TYPE_BIBLE]:
            self._ThekeGotoBar.set_text(self._navigator.ref.get_short_repr())
        else:
            self._ThekeGotoBar.set_text('')
