from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import WebKit2

import theke.uri
import theke.navigator

import logging
logger = logging.getLogger(__name__)

class ThekeWebView(WebKit2.WebView):

    __gsignals__ = {
        'click_on_word': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,))
        }

    def __init__(self, *args, **kwargs):
        logger.debug("ThekeWebView - Create a new instance")

        WebKit2.WebView.__init__(self, *args, **kwargs)

        self._navigator = None

        self._doLoadUriFlag = False

        self.connect("load-changed", self.handle_load_changed)
        self.connect("decide-policy", self.handle_decide_policy)

        context = self.get_context()
        context.register_uri_scheme('theke', self.handle_theke_uri, None)

    def register_navigator(self, navigator):
        self._navigator = navigator
        self._navigator.connect("context-updated", self._navigator_context_updated_cb)

    # Signals callbacks
    def do_click_on_word(self, uri) -> None:
        self._navigator.handle_webview_click_on_word_cb(None, uri)

    # Navigator callbacks
    def _navigator_context_updated_cb(self, object, uri, update_type) -> None:
        """Handle update of context

        @param uri: (str) raw uri
        @param update_type: (int) type of the update

            = theke.NEW_DOCUMENT --> load the uri
            = theke.NEW_VERSE --> jump to the verse
        """
        if update_type == theke.navigator.NEW_DOCUMENT:
            logger.debug("Loading: %s", uri)

            self._doLoadUriFlag = True
            self.load_uri(uri)

            self.grab_focus()

        elif update_type == theke.navigator.NEW_VERSE:
            self.scroll_to_verse(self._navigator.ref.verse)
            self.grab_focus()

        else:
            logger.debug("ThekeWebview - Unknown navigator context update type: %s", update_type)

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
                return False

            uri = theke.uri.parse(decision.get_request().get_uri(), isEncoded=True)

            if uri.scheme not in theke.uri.validSchemes:
                logger.error("Unsupported uri: %s", uri)
                return False

            if uri.path[1] in [theke.uri.SEGM_APP, theke.uri.SEGM_DOC] :
                logger.debug("Navigation action submited to the navigator: %s", uri)
                self._navigator.update_context(uri)
                decision.ignore()
                return True

        return False

    def handle_theke_uri(self, request, *user_data):
        """Return a stream to the content pointed by the theke uri.

        Handle localy some uri. Others are handle by _navigator.

        Case 1. The uri is a Theke signal
            eg. uri = theke:/signal/click_on_word?word=...
        """
        uri = theke.uri.parse(request.get_uri(), isEncoded = True)

        if uri.path[1] == theke.uri.SEGM_SIGNAL:
            # Case 1. The uri is a signal
            logger.debug("ThekeWebView - Catch a sword signal: %s", uri)

            if uri.path[2] == 'click_on_word':
                self.emit("click_on_word", uri)
                
            html_bytes = GLib.Bytes.new("".encode('utf-8'))
            tmp_stream_in = Gio.MemoryInputStream.new_from_bytes(html_bytes)

            request.finish(tmp_stream_in, -1, 'text/html; charset=utf-8')

        else:
            # Other cases. Handled by the navigator
            self._navigator.get_content_from_theke_uri(uri, request)

    def handle_load_changed(self, web_view, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            uri = theke.uri.parse(web_view.get_uri())

            if uri.scheme in ['http', 'https']:
                # Those uri are loaded out of the navigator scope
                # so they have to be registered manually
                self._navigator.register_web_uri(uri, web_view.get_title())

    # Webview API
    def jump_to_anchor(self, anchor):
        script = """var element_to_scroll_to = document.getElementById('{}');
        element_to_scroll_to.scrollIntoView({{behavior: "smooth", block: "center", inline: "nearest"}});
        """.format(anchor)
        self.run_javascript(script, None, None, None)

    def scroll_to_verse(self, verse):
        if verse > 0:
            script = 'jump_to_verse("verse-{}")'.format(verse)
            self.run_javascript(script, None, None, None)
