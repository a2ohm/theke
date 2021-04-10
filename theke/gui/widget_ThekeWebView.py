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

class ThekeWebView(WebKit2.WebView):
    def __init__(self, *args, **kwargs):
        WebKit2.WebView.__init__(self, *args, **kwargs)
        
        context = self.get_context()
        context.register_uri_scheme('theke', self.handle_theke_uri, None)
        context.register_uri_scheme('sword', self.handle_sword_uri, None)

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