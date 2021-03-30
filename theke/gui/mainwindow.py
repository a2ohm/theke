import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, WebKit2

css = """
w:hover {
    background-color: #FCFABA;
}
"""

class ThekeWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Theke")
        self.set_default_size(800, 600)

        self.scrolled_window = Gtk.ScrolledWindow()
        self.webview = WebKit2.WebView()
        self.contentManager = self.webview.get_user_content_manager()

        # Add css
        self.styleSheet = WebKit2.UserStyleSheet(css,
            WebKit2.UserContentInjectedFrames.ALL_FRAMES,
            WebKit2.UserStyleLevel.USER,
            None, None)
        self.contentManager.add_style_sheet(self.styleSheet)

        self.webview.load_html("", "foo:///")

        self.scrolled_window.add(self.webview)
        self.add(self.scrolled_window)

    def load_html(self, html):
        self.webview.load_html(html, "foo:///")