from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import WebKit2

import theke
import theke.uri
import theke.navigator

import logging
logger = logging.getLogger(__name__)

class ThekeWebView(WebKit2.WebView):

    __gsignals__ = {
        'click_on_word': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,)),
        'scroll-changed': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,))
        }

    def __init__(self, application, navigator):
        logger.debug("Create a new instance")

        WebKit2.WebView.__init__(self)

        self._app = application
        self._librarian = self._app.props.librarian

        self._navigator = navigator
        self._navigator.register_webview(self)

        #self._doLoadUriFlag = False

        context = self.get_context()
        context.register_uri_scheme('theke', self.handle_theke_uri, None)

        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        # ... self
        self.connect("load-changed", self.handle_load_changed)
        self.connect("decide-policy", self.handle_decide_policy)

    # Signals callbacks
    def do_click_on_word(self, uri) -> None:
        self._navigator.handle_webview_click_on_word_cb(None, uri)

    # Webview callbacks
    def handle_decide_policy(self, web_view, decision, decision_type):
        """Take a decision according to the context update

        @param decision: (WebKit2.NavigationPolicyDecision)
        @param decision_type: (WebKit2.PolicyDecisionType)
        """

        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            self._navigator.set_loading(True)

            uri = theke.uri.parse(decision.get_request().get_uri())
            updateType = self._navigator.update_context_from_uri(uri)

            if updateType == theke.navigator.NEW_VERSE:
                # It is not necessary to reload the document
                # Just jump to the verse
                self.scroll_to_verse(self._navigator.doc.section)
                self.grab_focus()

                self._navigator.set_loading(False)
                decision.ignore()
                return True
        
            elif updateType == theke.navigator.NEW_SECTION:
                # It is not necessary to reload the document
                # Just jump to the section
                self.jump_to_anchor(self._navigator.doc.section)
                self.grab_focus()

                self._navigator.set_loading(False)
                decision.ignore()
                return True

            else:
                decision.use()
                return True
        
        return False

    def handle_theke_uri(self, request, *user_data):
        """Return a stream to the content pointed by the theke uri.

        Case 1. The uri is a Theke signal
            eg. uri = theke:/signal/click_on_word?word=...
        Case 2. The uri is a path to an asset
        Case 3. Else, the uri is a path to a document
        """
        uri = theke.uri.parse(request.get_uri())

        # TODO: catch unsupported uri and display an error page
        #       if uri.scheme not in theke.uri.validSchemes ...
        
        if uri.path[1] == theke.uri.SEGM_SIGNAL:
            # Case 1. The uri is a signal
            logger.debug("Catch a sword signal: %s", uri)

            if uri.path[2] == 'click_on_word':
                self.emit("click_on_word", uri)

            if uri.path[2] == 'scroll_position':
                self.emit("scroll-changed", uri)
                
            html_bytes = GLib.Bytes.new("".encode('utf-8'))
            tmp_stream_in = Gio.MemoryInputStream.new_from_bytes(html_bytes)

            request.finish(tmp_stream_in, -1, 'text/html; charset=utf-8')

        elif uri.path[1] == theke.uri.SEGM_APP and uri.path[2] == theke.uri.SEGM_ASSETS:
            # Case 2. Path to an asset file
            f = Gio.File.new_for_path('./assets/' + '/'.join(uri.path[3:]))
            request.finish(f.read(), -1, None)

        else:
            # Case 3. Path to a document           
            request.finish(self._navigator.doc.inputStream, -1, 'text/html; charset=utf-8')

    def handle_load_changed(self, web_view, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            # The title of external webpage can only be set when the page is loaded
            if self._navigator.doc.type == theke.TYPE_WEBPAGE:
                self._navigator.doc.ref.set_title(web_view.get_title())

            # Inject the scrolling handler
            script = """
                // Scrolling handler
                window.onbeforeunload = function(){{
                    // Get scroll position
                    scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    r = "theke:/signal/scroll_position?shortTitle={}&y_scroll=" + scrollTop;
                    fetch(r);
                }};""".format(self._navigator.doc.shortTitle)
            self.run_javascript(script, None, None, None)

            self._navigator.set_loading(False)

    # Webview API
    def jump_to_anchor(self, anchor):
        """Ask the webview to scroll to an inner anchor
        
        Try to get the object by id (html5). If it fails, try by name.
        """
        
        script = """var e = document.getElementById('{anchor}');
        if (e) {{e.scrollIntoView({{behavior: "smooth", block: "start", inline: "nearest"}});}}
        
        e = document.getElementsByName('{anchor}');
        e[0].scrollIntoView({{behavior: "smooth", block: "start", inline: "nearest"}});
        """.format(anchor = anchor)
        self.run_javascript(script, None, None, None)
    
    def scroll_to_value(self, value, smooth = False):
        if smooth: 
            script = 'window.scroll({{left: 0, top: {}, behavior: "smooth"}});'.format(value)
        else:
            script = 'window.scroll(0, {});'.format(value)

        self.run_javascript(script, None, None, None)

    def scroll_to_verse(self, verse):
        if verse > 0:
            script = 'jump_to_verse("verse-{}")'.format(verse)
            self.run_javascript(script, None, None, None)
