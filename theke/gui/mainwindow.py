import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk
from gi.repository import WebKit2

import theke.reference

from theke.gui.widget_ThekeWebView import ThekeWebView
from theke.gui.widget_ThekeGotoBar import ThekeGotoBar
from theke.gui.widget_ThekeHistoryBar import ThekeHistoryBar
from theke.gui.widget_ThekeMorphoView import ThekeMorphoView

class ThekeWindow(Gtk.ApplicationWindow):
    def __init__(self, navigator, *args, **kwargs):
        Gtk.ApplicationWindow.__init__(self, *args, **kwargs)
        self.set_default_size(800, 600)
        self.set_icon_from_file("./assets/theke-logo.svg")

        self.navigator = navigator

        # State variables
        self.selectedSource = ''

        # UI BUILDING
        builder = Gtk.Builder()
        builder.add_from_file("./gui/theke_mainwindow.glade")
        self.add(builder.get_object("mainBox"))

        # TOP
        #   = navigation bar
        _top_box = builder.get_object("top_box")

        #   ... historybar: shortcuts to last viewed documents
        self.historybar = ThekeHistoryBar(navigator = self.navigator)

        #   ... gotobar: entry to open any document
        self.gotobar = ThekeGotoBar()
        self.gotobar.connect("activate", self.handle_goto)
        self.gotobar.autoCompletion.connect("match-selected", self.handle_match_selected)

        _top_box.pack_end(self.gotobar, False, False, 1)
        _top_box.pack_end(self.historybar, True, True, 1)

        # CONTENT
        _contentPane = builder.get_object("contentPane")

        #   ... TOC
        self.tocPanel_frame = builder.get_object("tocPanel_frame")
        #   ... TOC > title
        self.tocPanel_title = builder.get_object("tocPanel_title")
        #   ... TOC > content
        self.tocPanel_toc = builder.get_object("tocPanel_toc")

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Chapitre", renderer, text=0)
        self.tocPanel_toc.append_column(column)

        self.tocPanel_toc.get_selection().connect("changed", self.handle_toc_selection_changed)
        
        #   ... document view
        _scrolled_window = builder.get_object("webview_scrolledWindow")

        # ... document view > webview: where the document is displayed
        self.webview = ThekeWebView(navigator=self.navigator)
        self.webview.connect("load_changed", self.handle_load_changed)
        self.webview.connect("mouse_target_changed", self.handle_mouse_target_changed)

        _scrolled_window.add(self.webview)

        #   ... search panel

        # ... search panel > title
        self.searchPanel_title = builder.get_object("searchPanel_title")

        # ... search panel > results
        self.searchPanel_results = builder.get_object("searchPanel_results")
        self.searchPanel_results.set_headers_visible(False)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Reference", renderer, text=0)
        self.searchPanel_results.append_column(column)

        # # self.sidePanel_search.get_selection().connect("changed", self.handle_toc_selection_changed)

        # Set size.
        _searchPanel_pane = builder.get_object("searchPane")
        _searchPanel_pane.set_position(_searchPanel_pane.props.max_position)

        # ... tools view
        self.toolViewBox = builder.get_object("toolsViewBox")

        #   ... tools view > morphoview
        _morphoView_box = builder.get_object("morphoView_box")
        self.morphoView_word = builder.get_object("morphoView_word")
        self.morphoView_lemma = builder.get_object("morphoView_lemma")
        self.morphoView_lemmaText = builder.get_object("morphoView_lemmaText")
        self.morphview_searchButton = builder.get_object("morphoView_searchButton")

        self.morphview = ThekeMorphoView()
        self.navigator.connect("notify::word", self.handle_selected_word_changed)

        _morphoView_box.pack_start(self.morphview, True, True, 0)
        _contentPane.set_position(_contentPane.props.max_position)
        
        # BOTTOM
        bottomBox = builder.get_object("bottomBox")
        #   ... status bar
        self.statusbar = Gtk.Statusbar()
        bottomBox.pack_start(self.statusbar, False, True, 0)

        # Set the focus on the webview
        self.webview.grab_focus()

        # SET ACCELERATORS (keyboard shortcuts)
        accelerators = Gtk.AccelGroup()
        self.add_accel_group(accelerators)

        # ... Ctrl+l: give focus to the gotobar
        key, mod = Gtk.accelerator_parse('<Control>l')
        self.gotobar.add_accelerator('grab-focus', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

    def handle_goto(self, entry):
        '''@param entry: the object which received the signal.
        '''

        #TOFIX. Suppose that the content of the gotobar is a valid Sword Key
        ref = theke.reference.Reference(entry.get_text().strip(), source = self.selectedSource)
        self.navigator.goto_ref(ref)

    def handle_load_changed(self, web_view, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            # Update the status bar with the title of the just loaded page
            context_id = self.statusbar.get_context_id("navigation")
            self.statusbar.push(context_id, str(self.navigator.title))

            # Update the history bar
            self.historybar.add_uri_to_history(self.navigator.shortTitle, self.navigator.uri)

            if self.navigator.toc is None:
                self.tocPanel_frame.hide()
            else:
                self.tocPanel_title.set_text(self.navigator.ref.bookName)
                self.tocPanel_toc.set_model(self.navigator.toc.toc)
                self.tocPanel_frame.show()

            if not self.navigator.isMorphAvailable:
                self.toolViewBox.hide()

    def handle_match_selected(self, entry_completion, model, iter):
        # TODO: give name to column (and dont use a numerical value)
        # Update the text in the GotoBar
        self.gotobar.set_text("{} ".format(model.get_value(iter, 0)))

        # Save in a hidden variable the selected source.
        self.selectedSource = model.get_value(iter, 1)

        # Move the cursor to the end
        self.gotobar.set_position(-1)
        return True

    def handle_mouse_target_changed(self, web_view, hit_test_result, modifiers):
        if hit_test_result.context_is_link():
            context_id = self.statusbar.get_context_id("navigation-next")
            self.statusbar.pop(context_id)
            self.statusbar.push(context_id, "{}".format(hit_test_result.get_link_uri()))
        else:
            context_id = self.statusbar.get_context_id("navigation-next")
            self.statusbar.pop(context_id)

    def handle_selected_word_changed(self, instance, param):
        self.morphoView_word.set_text("{}".format(self.navigator.word))
        self.morphview.set_morph(self.navigator.morph)

        if self.navigator.lemma is None:
            self.morphoView_lemma.hide()
            self.morphview_searchButton.set_sensitive(False)
        else:
            self.morphoView_lemmaText.set_text(self.navigator.lemma)
            self.morphoView_lemma.show()
            self.morphview_searchButton.set_sensitive(True)

        self.toolViewBox.show()

    def handle_toc_selection_changed(self, tree_selection):
        model, treeIter = tree_selection.get_selected()

        if treeIter is not None:
            uri = model[treeIter][1]
            if uri != self.navigator.uri:
                self.navigator.goto_uri(uri)