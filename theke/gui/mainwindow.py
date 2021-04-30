import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk
from gi.repository import WebKit2

import theke.reference

from theke.gui.widget_ThekeWebView import ThekeWebView
from theke.gui.widget_ThekeGotoBar import ThekeGotoBar
from theke.gui.widget_ThekeHistoryBar import ThekeHistoryBar

class ThekeWindow(Gtk.ApplicationWindow):
    def __init__(self, navigator, *args, **kwargs):
        Gtk.ApplicationWindow.__init__(self, *args, **kwargs)
        self.set_default_size(800, 600)
        self.set_icon_from_file("./assets/theke-logo.svg")

        self.navigator = navigator

        # State variables
        self.selectedSource = ''

        # UI BUILDING
        # Main frame
        self._theke_window_main = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 0)

        # Top: navigation bar
        navigationbar = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 0)
        navigationbar.set_homogeneous(False)

        #   ... historybar: shortcuts to last viewed documents
        self.historybar = ThekeHistoryBar(navigator = self.navigator)

        #   ... gotobar: entry to open any document
        self.gotobar = ThekeGotoBar()
        self.gotobar.connect("activate", self.handle_goto)
        self.gotobar.autoCompletion.connect("match-selected", self.handle_match_selected)

        self._theke_window_main.pack_start(navigationbar, False, True, 0)
        navigationbar.pack_end(self.gotobar, False, False, 1)
        navigationbar.pack_end(self.historybar, True, True, 1)

        # Middle: content
        panes = Gtk.Paned()
        panes.set_position(150)
        self._theke_window_main.pack_start(panes, True, True, 0)

        # Pane 1: table of content, information about the current document, ...
        self.sidePanel_frame = Gtk.Frame()
        self.sidePanel_frame.set_shadow_type(Gtk.ShadowType.IN)
        self.sidePanel_frame.set_size_request(100, -1)

        sidePanel_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 0)
        sidePanel_box.set_homogeneous(False)


        # ... title
        self.sidePanel_title = Gtk.Label("Hello")

        # ... table of content
        self.sidePanel_TOC = Gtk.TreeView()

        sidePanel_box.pack_start(self.sidePanel_title, False, True, 0)
        sidePanel_box.pack_start(self.sidePanel_TOC, True, True, 0)

        self.sidePanel_frame.add(sidePanel_box)
        panes.pack1(self.sidePanel_frame, True, False)
        
        # Pane 2: document view
        scrolled_window = Gtk.ScrolledWindow()

        # ... webview: where the document is displayed
        self.webview = ThekeWebView(navigator=self.navigator)
        self.webview.connect("load_changed", self.handle_load_changed)
        self.webview.connect("mouse_target_changed", self.handle_mouse_target_changed)

        scrolled_window.add(self.webview)
        panes.pack2(scrolled_window, True, False)
        
        
        # Bottom: status bar
        self.statusbar = Gtk.Statusbar()

        self._theke_window_main.pack_start(self.statusbar, False, True, 0)
        self.add(self._theke_window_main)

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
            self.statusbar.push(context_id, "{}".format(self.navigator.title))

            # Update the history bar
            self.historybar.add_uri_to_history(self.navigator.shortTitle, self.navigator.uri)

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