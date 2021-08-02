import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject

import re

import theke.uri
import theke.index
import theke.sword
import theke.templates
import theke.reference
import theke.tableofcontent

import logging
logger = logging.getLogger(__name__)

# Config
# ... for sword
sword_default_module = "MorphGNT"

def format_sword_syntax(text) -> str:
    '''Format rendered text from sword into a theke comprehensible syntax
    '''
    return text.replace("title", "h2")

class ThekeNavigator(GObject.Object):
    """Load content and provide metadata.

    The ThekeNavigator loads any data requested by the webview.
    It provides metadata about the current view (eg. to be used in the UI).
    Outside of the webview workflow, it has to be called to open an uri or a reference.
    """

    __gsignals__ = {
        'click_on_word': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,))
        }

    uri = GObject.Property(type=object)
    ref = GObject.Property(type=object)
    sources = GObject.Property(type=object)
    availableSources = GObject.Property(type=object)

    #title = GObject.Property(type=str, default="")
    #shortTitle = GObject.Property(type=str, default="")

    toc = GObject.Property(type=object)

    isMorphAvailable  = GObject.Property(type=bool, default=False)
    word = GObject.Property(type=str)
    lemma = GObject.Property(type=str)
    strong = GObject.Property(type=str)
    morph = GObject.Property(type=str)


    def __init__(self, *args, **kwargs) -> None:
        logger.debug("ThekeNavigator - Create a new instance")

        super().__init__(*args, **kwargs)

        self.webview = None

    def register_webview(self, webview) -> None:
        """Register a reference to the webview this navigator is going to interact with.
        """
        self.webview = webview

    def goto_uri(self, uri, reload = False) -> None:
        """Ask the webview to load a given uri.

        Notice: all uri requests must go through the webview,
                even if it is then handled by this class.

        @parm uri: (string or ThekeUri)
        """
        if reload or uri != self.uri:
            logger.debug("ThekeNavigator - Goto: {}".format(uri))

            if isinstance(uri, str):
                self.webview.load_uri(uri)
            elif isinstance(uri, theke.uri.ThekeURI):
                self.webview.load_uri(uri.get_encoded_URI())
            else:
                raise ValueError('This is not an uri: {}.'.format(uri))

        self.webview.grab_focus()

    def goto_ref(self, ref) -> None:
        """Ask the webview to load a given reference.
        """
        self.goto_uri(ref.get_uri())

    def add_source(self, sourceName) -> None:
        if sourceName not in self.sources:
            logger.debug("ThekeNavigator - Add source {}".format(sourceName))

            self.sources += [sourceName]
            self.uri.params["sources"] = ";".join(self.sources)
            self.goto_uri(self.uri, reload = True)

    def delete_source(self, sourceName) -> None:
        if sourceName in self.sources:
            logger.debug("ThekeNavigator - Delete source {}".format(sourceName))

            self.sources.remove(sourceName)

            if len(self.sources) == 0:
                self.set_property("sources", [sword_default_module])
            else:
                self.notify("sources")

            self.uri.params["sources"] = ";".join(self.sources)
            self.goto_uri(self.uri, reload = True)

    def get_content_from_theke_uri(self, uri, request) -> None:
        """Return a stream to the file pointed by the theke uri.
        Case 1. The uri gives a path to a file
            eg. uri = theke:/default.css

        Case 2. The uri gives an alias
            eg. uri = theke:welcome

        @param uri: (ThekeUri)
        @param request: a WebKit2.URISchemeRequest

        This function is only called by a webview.
        """
        
        logger.debug("ThekeNavigator - Load as a theke uri: {}".format(uri))

        if uri.path[0] == '':
            # Case 1.
            f = Gio.File.new_for_path('./assets' + '/'.join(uri.path))
            request.finish(f.read(), -1, None)

        else:
            # Case 2.
            if self.ref is None or uri != self.ref.get_uri():
                self.update_context_from_theke_uri(uri)

            inAppUriData = theke.uri.inAppURI[uri.path[0]]

            ###
            logger.info("This reference to uri should be removed")
            self.set_property("uri", uri)
            ###

            f = Gio.File.new_for_path('./assets/{}'.format(inAppUriData.fileName))
            request.finish(f.read(), -1, 'text/html; charset=utf-8')

    def load_sword_uri(self, uri, request) -> None:
        '''Load an sword document given its uri and push it as a stream to request.

        @param uri: (ThekeUri) uri of the sword document (eg. sword:/bible/John 1:1?source=MorphGNT)
        @param request: (WebKit2.URISchemeRequest)
        '''

        if uri.path[1] == theke.uri.SWORD_BIBLE:
            logger.debug("ThekeNavigator - Load as a sword uri (BIBLE): {}".format(uri))
            if uri != self.uri:
                self.load_sword_bible_properties(uri)
            html = self.load_sword_bible_content()

        elif uri.path[1] == theke.uri.SWORD_BOOK:
            logger.debug("ThekeNavigator - Load as a sword uri (BOOK): {}".format(uri))
            html = self.load_sword_book(uri)

        elif uri.path[1] == theke.uri.SWORD_SIGNAL:
            logger.debug("ThekeNavigator - Catch a sword signal: {}".format(uri))

            if uri.path[2] == 'click_on_word':
                self.emit("click_on_word", uri)
                html = ""

        else:
            raise ValueError('Unknown sword book type: {}.'.format(uri.path[1]))

        html_bytes = GLib.Bytes.new(html.encode('utf-8'))
        tmp_stream_in = Gio.MemoryInputStream.new_from_bytes(html_bytes)

        request.finish(tmp_stream_in, -1, 'text/html; charset=utf-8')

    def load_sword_bible_properties(self, uri) -> None:
        """Update navigator properties from the uri.
        """
        logger.debug("ThekeNavigator - Update local properties")
        self.set_property("uri", uri)

        #   1. Get sources of the document to display
        #   Sources are choosen, by order:
        #       - from the uri
        #       - from the current context
        #       - from a hardcoded default source
        sources = uri.params.get('sources', None)
        if sources is None or sources == '':
            self.set_property("sources", [sword_default_module])
        else:
            self.set_property("sources", sources.split(";"))
            

        #   2. Get metadata from the reference
        ref = theke.reference.get_reference_from_uri(uri)

        if self.ref is None or ref.documentName != self.ref.documentName:
            self.set_property("toc", theke.tableofcontent.get_toc_from_ref(ref, self.sources))

        self.set_property("ref", ref)
        self.set_property("availableSources", theke.index.ThekeIndex().list_document_sources(ref.documentName))
        self.set_property("title", ref.get_repr())
        self.set_property("shortTitle", ref.get_short_repr())

    def load_sword_bible_content(self) -> str:
        logger.debug("ThekeNavigator - Load content")

        documents = []
        verses = []
        isMorphAvailable = False

        for source in self.sources:
            mod = theke.sword.SwordLibrary().get_bible_module(source)
            documents.append({
                'lang' : mod.get_lang(),
                'source': source
            })
            verses.append(mod.get_chapter(self.ref.bookName, self.ref.chapter))

            isMorphAvailable |= "OSISMorph" in mod.get_global_option_filter()
        
        self.set_property("isMorphAvailable", isMorphAvailable)
        self.set_property("morph", "-")

        return theke.templates.render('bible', {
            'documents': documents,
            'verses': verses,
            'ref': self.ref
        })

    def load_sword_book(self, uri) -> str:
        """Load a sword book.

        @param uri: (ThekeUri) a theke.uri matching "sword:/book/moduleName/parID"
            moduleName (mandatory): a valid sword book name (eg. VeritatisSplendor)
            parID: a paragraph id matching any osisID of the the sword book.
        @param request: (WebKit2.URISchemeRequest)
        """
        if len(uri.path) == 3:
            moduleName = uri.path[2]
            parID = 'Couverture'
            
            mod = theke.sword.SwordLibrary().get_book_module(moduleName)
            text = mod.get_paragraph(parID)

            self.set_property("shortTitle", '{}'.format(mod.get_short_repr()))
        elif len(uri.path) > 3:
            moduleName = uri.path[2]
            parID = uri.path[3]

            mod = theke.sword.SwordLibrary().get_book_module(moduleName)
            text = mod.get_paragraph_and_siblings(parID)

            self.set_property("shortTitle", '{} {}'.format(mod.get_short_repr(), parID))
        else:
            raise ValueError("Invalid uri for a Sword Book: {}".format(uri.get_decoded_URI()))

        if text is None:
            text = """<p>Ce texte n'a pas été trouvé.</p>
            <p>uri : {}</p>""".format(uri.get_decoded_URI())
        else:
            text = format_sword_syntax(text)

        self.set_property("uri", uri)
        self.set_property("ref", None)
        self.set_property("availableSources", None)

        self.set_property("toc", None)
        self.set_property("title", mod.get_name())
        self.set_property("isMorphAvailable", False)
        self.set_property("morph", "-")

        return theke.templates.render('book', {
            'title': mod.get_name(),
            'mod_name': mod.get_name(),
            'mod_description': mod.get_description(),
            'text': text})

    def update_context_from_theke_uri(self, uri) -> None:
        """Update the local context according to this theke uri.
        """
        self.set_property("ref", theke.reference.get_reference_from_uri(uri))

        self.set_property("toc", None)
        self.set_property("isMorphAvailable", False)
        self.set_property("morph", "-")

    def register_web_uri(self, uri) -> None:
        """Update properties according to this web page data.
        """

        self.set_property("uri", uri)
        self.set_property("ref", None)
        self.set_property("availableSources", None)

        self.set_property("title", self.webview.get_title())
        self.set_property("shortTitle", uri.netlock)

        self.set_property("toc", None)

        self.set_property("isMorphAvailable", False)
        self.set_property("morph", "-")

    def do_click_on_word(self, uri) -> None:
        """Do what should be do when a new word is selected in the webview
        Action(s):
            - update morphological data
        """
        pattern_signal_clickOnWord = re.compile(r'(lemma.Strong:(?P<lemma>\w+))?\s?(strong:(?P<strong>\w\d+))?')
        match_signal_clickOnWord = pattern_signal_clickOnWord.match(uri.params.get('lemma', ''))

        self.lemma = match_signal_clickOnWord.group('lemma')
        self.strong = match_signal_clickOnWord.group('strong')

        self.set_property("morph", uri.params.get('morph', '-'))
        self.set_property("word", uri.params.get('word', '?'))

    def handle_navigation_action(self, decision) -> bool:
        """Decide if the webview should execute a navigation action.

        @param decision: (WebKit2.NavigationPolicyDecision)
        """
        uri = theke.uri.parse(decision.get_request().get_uri(), isEncoded=True)

        if uri.scheme == 'sword':

            defaultSource = self.ref.source if self.ref else sword_default_module
            ref = theke.reference.get_reference_from_uri(uri, defaultSource = defaultSource)

            # Catch a navigation action to a biblical reference where only the verse number change
            if (self.ref and
                self.ref.type == theke.reference.TYPE_BIBLE and
                self.ref.bookName == ref.bookName and
                self.ref.chapter == ref.chapter and
                self.ref.verse != ref.verse):

                # self.set_property("uri", uri)
                # self.set_property("ref", ref)
                # self.set_property("title", ref.get_repr())
                # self.set_property("shortTitle", ref.get_short_repr())

                decision.ignore()
                self.webview.scroll_to_verse(ref.verse)
                return True

        return False

    @GObject.Property(type=str)
    def title(self):
        """Title of the current documment
        """
        return self.ref.get_repr()

    @GObject.Property(type=str)
    def shortTitle(self):
        """Short title of the current documment
        """
        return self.ref.get_short_repr()
