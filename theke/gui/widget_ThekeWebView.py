from gi.repository import WebKit2

import theke.uri

import logging
logger = logging.getLogger(__name__)

class ThekeWebView(WebKit2.WebView):
    def __init__(self, *args, **kwargs):
        logger.debug("ThekeWebView - Create a new instance")

        WebKit2.WebView.__init__(self, *args, **kwargs)

        self._navigator = None

        self.connect("load-changed", self.handle_load_changed)
        self.connect("decide-policy", self.handle_decide_policy)

        context = self.get_context()
        context.register_uri_scheme('theke', self.handle_theke_uri, None)

    def register_navigator(self, navigator):
        self._navigator = navigator

    def jump_to_anchor(self, anchor):
        script = """var element_to_scroll_to = document.getElementById('{}');
        element_to_scroll_to.scrollIntoView({{behavior: "smooth", block: "center", inline: "nearest"}});
        """.format(anchor)
        self.run_javascript(script, None, None, None)

    def scroll_to_verse(self, verse):
        if verse > 0:
            script = 'jump_to_verse("verse-{}")'.format(verse)
            self.run_javascript(script, None, None, None)

    def handle_decide_policy(self, web_view, decision, decision_type):
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            return self._navigator.handle_navigation_action(decision)
        return False

    def handle_theke_uri(self, request, *user_data):
        uri = theke.uri.parse(request.get_uri(), isEncoded = True)
        self._navigator.get_content_from_theke_uri(uri, request)

    def handle_load_changed(self, web_view, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            uri = theke.uri.parse(web_view.get_uri())

            if uri.scheme in ['http', 'https']:
                # Those uri are loaded out of the navigator scope
                # so they have to be registered manually
                self._navigator.register_web_uri(uri, web_view.get_title())
