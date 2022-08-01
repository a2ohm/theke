import logging

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import WebKit2

import theke
import theke.navigator
import theke.reference

# Import needed to load the gui
from theke.gui.aboutDialog import AboutDialog
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
    _ThekeDocumentBox : Gtk.Box = Gtk.Template.Child()
    _ThekeSearchView : Gtk.Bin = Gtk.Template.Child()
    _ThekeToolsBox : Gtk.Box = Gtk.Template.Child()

    _loading_spinner : Gtk.Spinner = Gtk.Template.Child()
    _loading_label : Gtk.Label = Gtk.Template.Child()

    _document_softRefresh_menuItem: Gtk.MenuItem = Gtk.Template.Child()
    _document_hardRefresh_menuItem: Gtk.MenuItem = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__()

        self._app = application
        self._archivist = self._app.props.archivist
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

        #   ... gotoBar
        # Populate the gotobar autocompletion list
        for documentData in self._archivist.list_documents_by_type(theke.TYPE_BIBLE):
            self._ThekeGotoBar.append((documentData.name, 'powder blue'))

        for documentData in self._archivist.list_documents_by_type(theke.TYPE_BOOK):
            self._ThekeGotoBar.append((documentData.name, 'white smoke'))

        #   ... document view
        # ... document view > webview: where the document is displayed
        navigator = theke.navigator.ThekeNavigator(self._app, self)
        navigator.connect("context-updated", self._navigator_context_updated_cb)
        navigator.connect("notify::selectedWord", self._navigator_selected_word_changed_cb)

        self._ThekeDocumentView = ThekeDocumentView(self._app, navigator)
        self._ThekeDocumentBox.pack_end(self._ThekeDocumentView, True, True, 0)

        self._ThekeDocumentView.connect("document-load-changed", self._documentView_load_changed_cb)
        self._ThekeDocumentView.connect("navigation-error", self._documentView_navigation_error_cb)
        self._ThekeDocumentView.connect("webview-mouse-target-changed", self._documentView_mouse_target_changed_cb)
        self._ThekeDocumentView.connect("webview-scroll-changed", self._documentView_scroll_changed_cb)

        #   ... search panel
        self._ThekeSearchView.connect("selection-changed", self._searchView_selection_changed)
        self._ThekeSearchView.connect("start", self._searchView_start_cb)
        self._ThekeSearchView.connect("finish", self._searchView_finish_cb)

        # ... tools view
        self._ThekeToolsBox.search_button_connect(self._toolsBox_searchButton_clicked_cb)

        # BOTTOM
        #   ... sources bar
        self._ThekeSourcesBar.connect("source-requested", self._sourceBar_source_requested_cb)
        self._ThekeSourcesBar.connect("delete-source", self._sourceBar_delete_source_cb)

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
            # ... Ctrl+l: give focus to the gotobar
            if keyval == Gdk.KEY_l:
                self._ThekeGotoBar.grab_focus()
                return True

            # ... Ctrl+s: save modifications in the personal dictionary
            elif keyval == Gdk.KEY_s:
                self._ThekeDocumentView.export_document(self)
                self._ThekeToolsBox._toolsBox_dicoView.save()
                return True

            # ... Ctrl+<Right>: goto to the toc entry
            elif keyval == Gdk.KEY_Right:
                if not self._ThekeDocumentView.isReduce:
                    self._ThekeDocumentView.toc_select_neighbor(self._ThekeDocumentView.TOC_NEXT)
                    return True
            
            # ... Ctrl+<Left>: goto to the previous toc entry
            elif keyval == Gdk.KEY_Left:
                if not self._ThekeDocumentView.isReduce:
                    self._ThekeDocumentView.toc_select_neighbor(self._ThekeDocumentView.TOC_PREVIOUS)
                    return True

        else:
            if keyval == Gdk.KEY_Escape:
                # If the gotobar has the focus, cancel,
                # fill it with the current reference
                # and give the focus back to the document view
                if self._ThekeGotoBar.has_focus():
                    self.fill_gotobar_with_reference(self._ThekeDocumentView.doc)
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
            self._ThekeDocumentView.open_ref(ref)
        else:
            self.display_warning_modal("Référence inconnue.")
    
    ### Callbacks (from glade / menu bar)

    @Gtk.Template.Callback()
    def _file_export_menuItem_activate_cb(self, menu_item) -> None:
        """File > Export
        """
        self._ThekeDocumentView.export_document(self)

    @Gtk.Template.Callback()
    def _file_closeWindow_menuItem_activate_cb(self, menu_item) -> None:
        """File > Close window
        """
        self.close()

    @Gtk.Template.Callback()
    def _file_quit_menuItem_activate_cb(self, menu_item) -> None:
        """File > Quit
        """
        self._app.quit()

    @Gtk.Template.Callback()
    def _document_search_menuItem_activate_cb(self, menu_item) -> None:
        """Document > Search
        """
        searchMode = self.props.local_search_mode_active
        if searchMode and not self._ThekeDocumentView.local_search_bar_has_focus():
            self._ThekeDocumentView.local_search_bar_grab_focus()
        else:
            self.props.local_search_mode_active = not searchMode
    
    @Gtk.Template.Callback()
    def _document_hardRefresh_menuItem_activate_cb(self, menu_item) -> None:
        """Document > Refresh cache
        """
        self._ThekeDocumentView.hard_refresh_document_async()

    @Gtk.Template.Callback()
    def _document_softRefresh_menuItem_activate_cb(self, menu_item) -> None:
        """Document > Refresh layout
        """
        self._ThekeDocumentView.soft_refresh_document_async()

    @Gtk.Template.Callback()
    def _help_help_menuItem_activate_cb(self, menu_item) -> None:
        """Help > Help
        """
        self.open_uri(theke.URI_HELP)

    @Gtk.Template.Callback()
    def _help_logbook_menuItem_activate_cb(self, menu_item) -> None:
        """Help > Logbook
        """
        self.open_uri(theke.URI_LOGBOOK)

    @Gtk.Template.Callback()
    def _help_about_menuItem_activate_cb(self, menu_item) -> None:
        """Help > About...
        """
        aboutDialog = AboutDialog()
        aboutDialog.props.transient_for = self
        aboutDialog.run()
        aboutDialog.destroy()

    ### Callbacks (_documentView)
    def _documentView_load_changed_cb(self, documentView, web_view, load_event):
        """Handle the load changed signal of the document view

        This callback is run after _ThekeDocumentView._document_load_changed_cb().
        This callback is run after _ThekeDocumentView._webview.handle_load_changed().
        """
        if load_event == WebKit2.LoadEvent.STARTED:
            # Show the sourcesBar, if necessary
            if documentView.type == theke.TYPE_BIBLE:
                self._ThekeSourcesBar.set_reveal_child(True)
                self._statusbar_revealer.set_reveal_child(False)
            else:
                self._ThekeSourcesBar.set_reveal_child(False)
                self._statusbar_revealer.set_reveal_child(True)

        elif load_event == WebKit2.LoadEvent.FINISHED:
            # Scroll to the last position
            scrolled_value = self._ThekeHistoryBar.get_scrolled_value(documentView.shortTitle)
            documentView.update_scroll(scrolled_value)
    
    def _documentView_navigation_error_cb(self, object, error):
        if error == theke.NavigationErrors.EXTERNAL_SOURCE_INACCESSIBLE:
            # Display an error message in a modal
            self.display_warning_modal("La source externe est inaccessible.",
                "Vérifiez votre connexion internet.")

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
    
    def _documentView_scroll_changed_cb(self, object, uri):
        self._ThekeHistoryBar.save_scrolled_value(uri.params['shortTitle'], int(uri.params['y_scroll']))

    ### Callbacks (_navigator)
    def _navigator_context_updated_cb(self, navigator, update_type) -> None:
        if update_type == theke.navigator.NEW_DOCUMENT:
            # Update the status bar with the title of the document
            contextId = self._statusbar.get_context_id("navigation")
            self._statusbar.push(contextId, str(navigator.doc.title))

            # Update the goto bar with the current reference
            self.fill_gotobar_with_reference(navigator.doc)

            # Update the history bar
            self._ThekeHistoryBar.add_uri_to_history(navigator.doc.shortTitle, navigator.doc.uri)

            # Update the source bar
            self._ThekeSourcesBar.updateAvailableSources(navigator.doc.availableSources)
            self._ThekeSourcesBar.updateSources(navigator.doc.sources)

            # Activate or not some menu items
            sources = navigator.doc.sources
            if sources and sources[0].type == theke.index.SOURCETYPE_EXTERN:
                self._document_softRefresh_menuItem.set_sensitive(True)
                self._document_hardRefresh_menuItem.set_sensitive(True)
            else:
                self._document_softRefresh_menuItem.set_sensitive(False)
                self._document_hardRefresh_menuItem.set_sensitive(False)

        if update_type == theke.navigator.SOURCES_UPDATED:
            self._ThekeSourcesBar.updateSources(navigator.doc.sources)

    def _navigator_selected_word_changed_cb(self, navigator, params):
        """Transmit the selected word to the tools box
        """
        w = navigator.selectedWord

        self._ThekeToolsBox.set_morph(w.word, w.morph)

        self._ThekeToolsBox.set_lemma(w.lemma)
        self._ThekeToolsBox.set_strongs(w.strong)
        self._ThekeToolsBox.show()

    ### Callbacks (_searchView)
    def _searchView_selection_changed(self, object, result):
        """Goto to the selected search result
        """
        ref = theke.reference.parse_reference(result.reference)
        self._ThekeDocumentView.open_ref(ref)  

    def _searchView_start_cb(self, object, moduleName, lemma):
        self._ThekeToolsBox._toolsBox_search_button.set_sensitive(False)

    def _searchView_finish_cb(self, object):
        self._ThekeToolsBox._toolsBox_search_button.set_sensitive(True)  

    ### Callbacks (_sourceBar)
    def _sourceBar_delete_source_cb(self, object, sourceName):
        self._ThekeDocumentView._navigator.remove_source(sourceName)
    
    def _sourceBar_source_requested_cb(self, object, sourceName):
        self._ThekeDocumentView._navigator.add_source(sourceName)

    ### Callbacks (_toolsBox)
    def _toolsBox_searchButton_clicked_cb(self, button):
        self._ThekeSearchView.show()
        self._ThekeSearchView.search_start(self._ThekeDocumentView._navigator.selectedWord.source, self._ThekeDocumentView._navigator.selectedWord.rawStrong)

    ### Callbacks (other)
    def on_history_button_clicked(self, button):
        self.open_uri(button.uri)
        return True

    def fill_gotobar_with_reference(self, doc) -> None:
        """Fill the gotobar with the reference of the given document
        """
        if doc.type == theke.TYPE_BIBLE:
            self._ThekeGotoBar.set_text(doc.shortTitle)
        elif doc.type == theke.TYPE_BOOK:
            self._ThekeGotoBar.set_text(doc.title)
        else:
            self._ThekeGotoBar.set_text('')

    ### Helpers
    def open_uri(self, uri) -> None:
        self._ThekeDocumentView.open_uri(uri)

    def display_warning_modal(self, mainText, secondaryText = None):
        """Display a message dialog with a warning message
        """
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING,
            Gtk.ButtonsType.OK, mainText)
            
        if secondaryText:
            dialog.format_secondary_text(secondaryText)

        dialog.run()
        dialog.destroy()
    
    def set_loading(self, isLoading, loadingMsg = "") -> None:
        """Show or hide the loading spinner and a loading message
        """
        logger.debug("Set loading: %s", isLoading)

        if isLoading:
            self._loading_spinner.start()
            self._loading_label.set_label(loadingMsg)

        else:
            self._loading_spinner.stop()
            self._loading_label.set_label("")
