import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, WebKit2

css = """
sup {
    color: #f00;
}
w:hover {
    background-color: #FCFABA;
}
"""

class ThekeWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        Gtk.ApplicationWindow.__init__(self, *args, **kwargs)
        self.set_default_size(800, 600)

        self._theke_window_main = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 0)

        self.scrolled_window = Gtk.ScrolledWindow()
        self.statusbar = Gtk.Statusbar()

        self.webview = WebKit2.WebView()
        self.contentManager = self.webview.get_user_content_manager()

        # Add css
        self.styleSheet = WebKit2.UserStyleSheet(css,
            WebKit2.UserContentInjectedFrames.ALL_FRAMES,
            WebKit2.UserStyleLevel.USER,
            None, None)
        self.contentManager.add_style_sheet(self.styleSheet)

        self.webview.load_html("", "theke:///")

        self.scrolled_window.add(self.webview)
        self._theke_window_main.pack_start(self.scrolled_window, True, True, 0)
        self._theke_window_main.pack_start(self.statusbar, False, True, 0)
        self.add(self._theke_window_main)

    def load_html(self, html):
        '''Load a html page in the webview.
        @param html: html code to display
        '''
        self.webview.load_html(html, "theke:///")