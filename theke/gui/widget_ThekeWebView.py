import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import WebKit2

import theke.uri

class ThekeWebView(WebKit2.WebView):
    def __init__(self, navigator, *args, **kwargs):
        WebKit2.WebView.__init__(self, *args, **kwargs)

        self.navigator = navigator
        self.navigator.register_webview(self)
        
        context = self.get_context()
        context.register_uri_scheme('theke', self.handle_theke_uri, None)
        context.register_uri_scheme('sword', self.handle_sword_uri, None)

    def handle_theke_uri(self, request, *user_data):
        uri = theke.uri.parse(request.get_uri(), isEncoded = True)
        self.navigator.load_theke_uri(uri, request)

    def handle_sword_uri(self, request, *user_data):
        uri = theke.uri.parse(request.get_uri(), isEncoded = True)
        self.navigator.load_sword_uri(uri, request)