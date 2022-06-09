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

        self._doLoadUriFlag = False

        context = self.get_context()
        context.register_uri_scheme('theke', self.handle_theke_uri, None)

        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        # ... self
        self.connect("load-changed", self.handle_load_changed)
        self.connect("decide-policy", self.handle_decide_policy)

        # ... navigator
        self._navigator.connect("context-updated", self._navigator_context_updated_cb)

    # Signals callbacks
    def do_click_on_word(self, uri) -> None:
        self._navigator.handle_webview_click_on_word_cb(None, uri)

    # Navigator callbacks
    def _navigator_context_updated_cb(self, object, update_type) -> None:
        """Handle update of context

        @param uri: (str) raw uri
        @param update_type: (int) type of the update

            = theke.NEW_DOCUMENT --> load the uri
            = theke.NEW_VERSE --> jump to the verse
        """
        if update_type == theke.navigator.NEW_DOCUMENT \
            or update_type == theke.navigator.SOURCES_UPDATED:
            uri = self._navigator.contentUri

            logger.debug("Loading: %s", uri)

            self._doLoadUriFlag = True
            self.load_uri(uri)

            self.grab_focus()

        elif update_type == theke.navigator.NEW_VERSE:
            self.scroll_to_verse(self._navigator.ref.get_verse())
            self.grab_focus()
        
        elif update_type == theke.navigator.NEW_SECTION:
            self.jump_to_anchor(self._navigator.ref.section)
            self.grab_focus()

        else:
            logger.debug("Unknown navigator context update type: %s", update_type)

    # Webview callbacks
    def handle_decide_policy(self, web_view, decision, decision_type):
        """Decide where navigation actions are sent

        By default, navigation actions are submited to the navigator in
        order to update the context.

        Then, the navigator will rise the context-updated signal.
        Then, the webview check if new content should be loaded
        (see self._navigator_context_updated_cb()). In this case, the
        _doLoadUri flag is risen and the navigation should not be submited
        to the navigator and should continue its own way.

        @param decision: (WebKit2.NavigationPolicyDecision)
        @param decision_type: (WebKit2.PolicyDecisionType)
        """

        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            # If the doLoadUri flag is up, just accept this navigation action
            if self._doLoadUriFlag:
                self._doLoadUriFlag = False
                decision.use()
                return True

            uri = theke.uri.parse(decision.get_request().get_uri())

            if uri.scheme not in theke.uri.validSchemes:
                logger.error("Unsupported uri: %s", uri)
                return False

            if uri.scheme in theke.uri.webpageSchemes:
                logger.debug("Navigation action submited to the navigator: %s", uri)
                self._navigator.update_context_from_uri(uri)
                decision.ignore()
                return True

            if uri.path[1] in [theke.uri.SEGM_APP, theke.uri.SEGM_DOC] :
                logger.debug("Navigation action submited to the navigator: %s", uri)
                self._navigator.update_context_from_uri(uri)
                decision.ignore()
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
            doc = self._librarian.get_document(self._navigator.ref, self._navigator.selectedSources)
            request.finish(doc.inputStream, -1, 'text/html; charset=utf-8')

    def handle_load_changed(self, web_view, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            # The title of external webpage can only be set when the page is loaded
            if self._navigator.type == theke.TYPE_WEBPAGE:
                self._navigator.ref.set_title(web_view.get_title())

            # Inject the scrolling handler
            script = """
                // Scrolling handler
                window.onbeforeunload = function(){{
                    // Get scroll position
                    scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    r = "theke:/signal/scroll_position?shortTitle={}&y_scroll=" + scrollTop;
                    fetch(r);
                }};""".format(self._navigator.shortTitle)
            self.run_javascript(script, None, None, None)

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
