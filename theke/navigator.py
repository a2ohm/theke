from collections import namedtuple
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject

import re

import theke
import theke.uri
import theke.index
import theke.sword
import theke.templates
import theke.reference
import theke.tableofcontent

import logging
logger = logging.getLogger(__name__)

SelectedWord = namedtuple('selectedWord',['word','lemma','strong','morph','source'])

def format_sword_syntax(text) -> str:
    '''Format rendered text from sword into a theke comprehensible syntax
    '''
    return text.replace("title", "h2")

class ThekeNavigator(GObject.Object):
    """Load content and provide metadata.

    The ThekeNavigator loads any data requested by the webview.
    It provides metadata about the current view (=context) (eg. to be used in the UI).
    Outside of the webview workflow, it has to be called to open an uri or a reference.
    """

    __gsignals__ = {
        'click_on_word': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,))
        }

    ref = GObject.Property(type=object)

    toc = GObject.Property(type=object)

    isMorphAvailable  = GObject.Property(type=bool, default=False)
    selectedWord = GObject.Property(type=object)

    def __init__(self, *args, **kwargs) -> None:
        logger.debug("ThekeNavigator - Create a new instance")

        super().__init__(*args, **kwargs)

        self.webview = None
        self.index = theke.index.ThekeIndex()

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
        if reload or self.ref is None or uri != self.ref.get_uri():
            logger.debug("ThekeNavigator - Goto: %s", uri)

            if isinstance(uri, str):
                self.webview.load_uri(uri)
            elif isinstance(uri, theke.uri.ThekeURI):
                self.webview.load_uri(uri.get_encoded_URI())
            else:
                raise ValueError('This is not an uri: {}.'.format(uri))

        self.webview.grab_focus()

    def goto_ref(self, ref) -> None:
        """Ask the webview to load a given reference
        """
        self.goto_uri(ref.get_uri())

    def goto_section(self, tocData) -> None:
        """Ask the webview to load a document section
        """

        logger.debug("ThekeNavigator - Goto section: %s", tocData)

        if self.toc.type == theke.tableofcontent.BIBLE_TOC_TYPE:
            # tocData (int): chapter
            if self.ref.chapter != tocData:
                self.ref.chapter = tocData
                self.ref.verse = 0
                self.goto_uri(self.ref.get_uri(), reload = True)

        else:
            logging.error("This type of TOC (%s) is not supported yet.", self.toc.type)

    ### Edit the context

    def add_source(self, sourceName) -> None:
        if self.ref.add_source(sourceName):
            self.notify("sources")
            self.goto_uri(self.ref.get_uri(), reload = True)

    def delete_source(self, sourceName) -> None:
        if self.ref.remove_source(sourceName):
            self.notify("sources")
            self.goto_uri(self.ref.get_uri(), reload = True)

    ### Update context (from URI)

    def update_context(self, uri) -> None:
        """Update local context according to this uri
        """
        if self.ref is None or uri != self.ref.get_uri():
            logger.debug("ThekeNavigator − Update context")

            ref = theke.reference.get_reference_from_uri(uri)

            if ref.type == theke.TYPE_BIBLE:
                # Update the table of content only if needed
                if self.ref is None or ref.documentName != self.ref.documentName:
                    self.set_property("toc", theke.tableofcontent.get_toc_BIBLE(ref))

                self.set_property("ref", ref)
                self.notify("sources")

            else:
                self.set_property("ref", ref)
                self.set_property("toc", None)
                self.set_property("isMorphAvailable", False)

            self.notify("availableSources")

        else:
            logger.debug("ThekeNavigator − Update context (skip)")

    ### Get content

    def get_content_from_theke_uri(self, uri, request) -> None:
        """Return a stream to the content pointed by the theke uri.
        Case 1. The uri is a path to an assets file
            eg. uri = theke:/app/assets/default.css

        Case 2. The uri is a path to an inapp alias
            eg. uri = theke:/app/welcome

        Case 3. The uri is a signal
            eg. uri = theke:/signal/click_on_word?word=...

        Case 4. The uri is a path to a document
            eg. uri = theke:/doc/bible/John 1:1?sources=MorphGNT

        @param uri: (ThekeUri)
        @param request: a WebKit2.URISchemeRequest

        This function is only called by a webview.
        """

        logger.debug("ThekeNavigator - Get content from a theke uri: %s", uri)

        if uri.path[1] == theke.uri.SEGM_APP:
            if uri.path[2] == theke.uri.SEGM_ASSETS:
                # Case 1. Path to an asset file
                f = Gio.File.new_for_path('./assets/' + '/'.join(uri.path[3:]))
                request.finish(f.read(), -1, None)

            else:
                # Case 2. InApp uri
                self.update_context(uri)
                inAppUriData = theke.uri.inAppURI[uri.path[2]]

                f = Gio.File.new_for_path('./assets/{}'.format(inAppUriData.fileName))
                request.finish(f.read(), -1, 'text/html; charset=utf-8')

        else:
            if uri.path[1] == theke.uri.SEGM_SIGNAL:
                # Case 3. The uri is a signal
                logger.debug("ThekeNavigator - Catch a sword signal: %s", uri)

                if uri.path[2] == 'click_on_word':
                    self.emit("click_on_word", uri)
                    html = ""

            elif uri.path[1] == theke.uri.SEGM_DOC:
                # Case 4. The uri is a path to a document
                if uri.path[2] == theke.uri.SEGM_BIBLE:
                    self.update_context(uri)

                    logger.debug("ThekeNavigator - Load as a sword uri (BIBLE): %s", uri)
                    html = self.get_sword_bible_content()

                elif uri.path[2] == theke.uri.SEGM_BOOK:
                    self.update_context(uri)

                    logger.debug("ThekeNavigator - Load as a sword uri (BOOK): %s", uri)
                    html = self.get_sword_book_content(uri)

            else:
                raise ValueError('Unsupported theke uri: {}.'.format(uri))

            html_bytes = GLib.Bytes.new(html.encode('utf-8'))
            tmp_stream_in = Gio.MemoryInputStream.new_from_bytes(html_bytes)

            request.finish(tmp_stream_in, -1, 'text/html; charset=utf-8')

    def get_sword_bible_content(self) -> str:
        logger.debug("ThekeNavigator - Load content")

        documents = []
        verses = []
        isMorphAvailable = False

        for source in self.ref.sources:
            markup = theke.sword.MARKUP.get(source, theke.sword.FMT_PLAIN)
            mod = theke.sword.SwordLibrary(markup=markup).get_bible_module(source)
            documents.append({
                'lang' : mod.get_lang(),
                'source': source
            })
            verses.append(mod.get_chapter(self.ref.bookName, self.ref.chapter))

            isMorphAvailable |= "OSISMorph" in mod.get_global_option_filter()

        self.set_property("isMorphAvailable", isMorphAvailable)

        return theke.templates.render('bible', {
            'documents': documents,
            'verses': verses,
            'ref': self.ref
        })

    def get_sword_book_content(self, uri) -> str:
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

            self.ref.documentShortTitle = '{}'.format(mod.get_short_repr())

        elif len(uri.path) > 3:
            moduleName = uri.path[2]
            parID = uri.path[3]

            mod = theke.sword.SwordLibrary().get_book_module(moduleName)
            text = mod.get_paragraph_and_siblings(parID)

            self.ref.documentShortTitle = '{} {}'.format(mod.get_short_repr(), parID)

        else:
            raise ValueError("Invalid uri for a Sword Book: {}".format(uri.get_decoded_URI()))

        if text is None:
            text = """<p>Ce texte n'a pas été trouvé.</p>
            <p>uri : {}</p>""".format(uri.get_decoded_URI())
        else:
            text = format_sword_syntax(text)

        self.ref.documentName = mod.get_name()

        return theke.templates.render('book', {
            'title': mod.get_name(),
            'mod_name': mod.get_name(),
            'mod_description': mod.get_description(),
            'text': text})

    def register_web_uri(self, uri) -> None:
        """Update properties according to this web page data.
        """

        self.set_property("uri", uri)
        self.set_property("ref", None)

        self.set_property("toc", None)

        self.set_property("isMorphAvailable", False)

        self.notify("availableSources")

    ### Signals handling

    def do_click_on_word(self, uri) -> None:
        """Do what should be do when a new word is selected in the webview
        Action(s):
            - update morphological data
        """
        pattern_signal_clickOnWord = re.compile(r'(lemma.Strong:(?P<lemma>\w+))?\s?(strong:(?P<strong>\w\d+))?')
        match_signal_clickOnWord = pattern_signal_clickOnWord.match(uri.params.get('lemma', ''))

        self.set_property("selectedWord", SelectedWord(
            uri.params.get('word', '?'),
            match_signal_clickOnWord.group('lemma'),
            match_signal_clickOnWord.group('strong'),
            uri.params.get('morph', '-'),
            uri.params.get('source')
        ))

    def handle_navigation_action(self, decision) -> bool:
        """Decide if the webview should execute a navigation action.

        @param decision: (WebKit2.NavigationPolicyDecision)
        """
        uri = theke.uri.parse(decision.get_request().get_uri(), isEncoded=True)

        if uri.scheme == 'sword':

            ref = theke.reference.get_reference_from_uri(uri)

            # Catch a navigation action to a biblical reference where only the verse number change
            if (self.ref and
                self.ref.type == theke.TYPE_BIBLE and
                self.ref.bookName == ref.bookName and
                self.ref.chapter == ref.chapter and
                self.ref.verse != ref.verse):

                decision.ignore()
                self.webview.scroll_to_verse(ref.verse)
                return True

        return False

    @GObject.Property(type=str)
    def availableSources(self):
        """Available sources of the current documment
        """
        return self.ref.availableSources

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

    @GObject.Property(type=str)
    def sources(self):
        """Short title of the current documment
        """
        return self.ref.sources

    @GObject.Property(type=str)
    def uri(self):
        """URI of the current documment
        """
        return self.ref.get_uri()
