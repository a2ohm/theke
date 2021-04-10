import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import WebKit2

import theke.uri
import theke.loaders

css = """
sup {
    color: #f00;
}
w:hover {
    background-color: #FCFABA;
}
"""

# Configurations
assets_path = "file://" + os.path.abspath(os.getcwd()) + "/assets/"

class ThekeWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        Gtk.ApplicationWindow.__init__(self, *args, **kwargs)
        self.set_default_size(800, 600)

        self._theke_window_main = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 0)

        self.navigationbar = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 0)
        self.scrolled_window = Gtk.ScrolledWindow()
        self.statusbar = Gtk.Statusbar()

        # TODO: Move all of this in an external widget class.
        self.gotobar = Gtk.SearchEntry()
        self.gotobar.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "go-next")
        self.gotobar.connect("activate", self.handleGoto)

        self.gotocompletion = Gtk.EntryCompletion()
        self.gotocompletionlist = Gtk.ListStore(str)
        for i in ['Matthew', 'Mark', 'Luke', 'John']:
            self.gotocompletionlist.append((i,))
        self.gotocompletion.set_model(self.gotocompletionlist)
        self.gotocompletion.set_text_column(0)
        self.gotobar.set_completion(self.gotocompletion)

        self.webview = WebKit2.WebView()
        self.webview.connect("load_changed", self.handle_load_changed)

        # Add sword:// and theke:// context
        self.context = self.webview.get_context()
        self.context.register_uri_scheme('theke', self.handle_theke_uri, None)
        self.context.register_uri_scheme('sword', self.handle_sword_uri, None)

        # Add css
        self.contentManager = self.webview.get_user_content_manager()
        self.styleSheet = WebKit2.UserStyleSheet(css,
            WebKit2.UserContentInjectedFrames.ALL_FRAMES,
            WebKit2.UserStyleLevel.USER,
            None, None)
        self.contentManager.add_style_sheet(self.styleSheet)

        self.navigationbar.add(self.gotobar)
        self.scrolled_window.add(self.webview)
        self._theke_window_main.pack_start(self.navigationbar, False, True, 0)
        self._theke_window_main.pack_start(self.scrolled_window, True, True, 0)
        self._theke_window_main.pack_start(self.statusbar, False, True, 0)
        self.add(self._theke_window_main)

        # Set the focus on the webview
        self.webview.grab_focus()

    def load_uri(self, uri):
        self.webview.load_uri(uri.get_coded_URI())

    def handle_theke_uri(self, request, *user_data):
        uri = theke.uri.ThekeURI(request.get_uri(), isRaw = True)
        f = Gio.File.new_for_path('./assets/' + '/'.join(uri.path))
        request.finish(f.read(), -1, None)

    def handle_sword_uri(self, request, *user_data):
        uri = theke.uri.ThekeURI(request.get_uri(), isRaw = True)
        html = theke.loaders.load_sword(uri)
        html_bytes = GLib.Bytes.new(html.encode('utf-8'))
        tmp_stream_in = Gio.MemoryInputStream.new_from_bytes(html_bytes)

        request.finish(tmp_stream_in, -1, 'text/html; charset=utf-8')

    def handleGoto(self, entry):
        '''@param entry: the object which received the signal.
        '''

        #TOFIX. Suppose that the content of the gotobar is a valid Sword Key
        key = entry.get_text()
        uri = theke.uri.ThekeURI("sword:///bible/{}".format(key))
        self.load_uri(uri)

    def handle_load_changed(self, web_view, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            # Update the status bar with the title of the just loaded page
            context_id = self.statusbar.get_context_id("navigation")
            self.statusbar.push(context_id, "{}".format(web_view.get_title()))