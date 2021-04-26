import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject

import theke.uri
import theke.loaders

class ThekeNavigator(GObject.Object):
    """Load content and provide metadata.

    The ThekeNavigator loads any data requested by the webview.
    It provides metadata about the current view (eg. to be used in the UI).
    Outside of the webview workflow, it has to be called to open an uri or a reference.
    """

    def __init__(self, *args, **kwargs):
        GObject.Object.__init__(self, *args, **kwargs)

        self.webview = None

        self._uri = None
        self._title = "Title"
        self._shortTitle = "ShortTitle"

    def register_webview(self, webview):
        self.webview = webview

    def goto_uri(self, uri):
        self.webview.load_uri(uri.get_encoded_URI())
        self.webview.grab_focus()

    def goto_ref(self, ref):
        self.goto_uri(ref.get_uri())

    def load_theke_uri(self, uri, request):
        """Return a stream to the file pointed by the theke uri.
        Case 1. The uri gives a path to a file
            eg. uri = theke:/default.css

        Case 2. The uri gives an alias
            eg. uri = theke:welcome

        @param uri: a ThekeUri
        @param request: a WebKit2.URISchemeRequest
        """
        if uri.path[0] == '':
            # Case 1.
            f = Gio.File.new_for_path('./assets' + '/'.join(uri.path))
            request.finish(f.read(), -1, None)

        else:
            # Case 2.
            inAppUriData = theke.uri.inAppURI[uri.path[0]]

            self.set_property("uri", uri)
            self.set_property("title", inAppUriData.title)
            self.set_property("shortTitle", inAppUriData.shortTitle)

            f = Gio.File.new_for_path('./assets/{}'.format(inAppUriData.fileName))
            request.finish(f.read(), -1, 'text/html; charset=utf-8')

    def load_sword_uri(self, uri, request):
        html = theke.loaders.load_sword(uri)
        html_bytes = GLib.Bytes.new(html.encode('utf-8'))
        tmp_stream_in = Gio.MemoryInputStream.new_from_bytes(html_bytes)

        self.set_property("uri", uri)
        self.set_property("title", uri.path[-1])
        self.set_property("shortTitle", uri.path[-1])

        request.finish(tmp_stream_in, -1, 'text/html; charset=utf-8')
    
    # PUBLIC PROPERTIES
    @GObject.Property
    def uri(self):
        """The current uri"""
        return self._uri

    @uri.setter
    def uri(self, uri):
        self._uri = uri

    @GObject.Property
    def title(self):
        """The title of the current uri"""
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    @GObject.Property
    def shortTitle(self):
        """The short title of the current uri"""
        return self._shortTitle

    @shortTitle.setter
    def shortTitle(self, shortTitle):
        self._shortTitle = shortTitle