from collections import namedtuple

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

SelectedWord = namedtuple('selectedWord',['word','lemma','rawStrong', 'strong','morph','source'])

# Return codes when the context is updated
SAME_DOCUMENT = 0
NEW_DOCUMENT = 1
NEW_SECTION = 2
NEW_VERSE = 3

SOURCES_UPDATED = 4

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
        'context-updated': (GObject.SignalFlags.RUN_LAST, None, (int,))
        }

    ref = GObject.Property(type=object)

    toc = GObject.Property(type=object)

    isMorphAvailable  = GObject.Property(type=bool, default=False)
    selectedWord = GObject.Property(type=object)

    def __init__(self, *args, **kwargs) -> None:
        logger.debug("Create a new instance")

        super().__init__(*args, **kwargs)

        self.index = theke.index.ThekeIndex()

        self.preventRefUpdateOnNextWebUriRegistering = False

    def goto_uri(self, uri, reload = False) -> None:
        """Ask the webview to load a given uri.

        Notice: all uri requests must go through the webview,
                even if it is then handled by this class.

        @parm uri: (string or ThekeUri)
        """
        if reload or self.ref is None or uri != self.ref.get_uri():
            logger.debug("Goto uri: %s", uri)

            if isinstance(uri, str):
                uri = theke.uri.parse(uri, isEncoded=True)

            self.update_context_from_uri(uri)

    ### GOTO functions

    def goto_ref(self, ref, reload = False) -> None:
        """Ask the webview to load a given reference
        """
        if reload or self.ref is None or ref != self.ref:
            logger.debug("Goto ref: %s", ref)
            self.update_context_from_ref(ref)

    def goto_section(self, tocData) -> None:
        """Ask the webview to load a document section
        """

        logger.debug("Goto section: %s", tocData)

        if self.toc.type == theke.TYPE_BIBLE:
            # tocData (int): chapter
            if self.ref.chapter != tocData:
                self.ref.chapter = tocData
                self.ref.verse = 0
                self.emit("context-updated", NEW_DOCUMENT)

        else:
            logging.error("This type of TOC (%s) is not supported yet.", self.toc.type)

    ### Edit the context

    def add_source(self, sourceName) -> None:
        if self.ref.add_source(sourceName):
            self.emit("context-updated", SOURCES_UPDATED)

    def delete_source(self, sourceName) -> None:
        if self.ref.remove_source(sourceName):
            self.emit("context-updated", SOURCES_UPDATED)

    ### Update context (from URI)

    def update_context_from_uri(self, uri) -> None:
        """Update local context according to the uri
        """
        if self.ref is not None and uri == self.ref.get_uri():
            # This is not a new uri, the context stays the same
            logger.debug("Update context (skip)")
            self.emit("context-updated", SAME_DOCUMENT)
            return

        ref = theke.reference.get_reference_from_uri(uri)
        self.update_context_from_ref(ref)

    def update_context_from_ref(self, ref) -> None:
        """Update local context according to the ref

        Returning code:
         - SAME_DOCUMENT: same uri as that of the open document
            --> the context is not updated

         - NEW_VERSE: (for biblical document only) same uri except the verse number
            --> only the verse number is updated

         - NEW_DOCUMENT: different uri
            --> the context is updated
        """

        if ref.type == theke.TYPE_BIBLE:
            logger.debug("Update context [bible]")

            # Update the table of content only if the document name is different
            if self.ref is None or ref.documentName != self.ref.documentName:
                self.set_property("toc", theke.tableofcontent.get_toc_BIBLE(ref))

            if (self.ref.type == theke.TYPE_BIBLE and
                self.ref.bookName == ref.bookName and
                self.ref.chapter == ref.chapter and
                self.ref.verse != ref.verse):

                # Same reference except the verse number
                self.ref.verse = ref.verse

                self.emit("context-updated", NEW_VERSE)
                return

            # Different reference, update all the context
            self.set_property("ref", ref)

            self.emit("context-updated", NEW_DOCUMENT)
            return

        else:
            logger.debug("Update context [book/inApp]")

            self.set_property("ref", ref)
            self.set_property("toc", None)
            self.set_property("isMorphAvailable", False)

            self.emit("context-updated", NEW_DOCUMENT)
            return

    ### Get content

    def get_content_from_theke_uri(self, uri, request) -> str:
        """Return a stream to the content pointed by the theke uri.
        NB. The context has been updated by handle_navigation_action()

        # Case 1. The uri is a path to an assets file
        #     eg. uri = theke:/app/assets/css/default.css

        # Case 2. The uri is a path to an inapp alias
        #     eg. uri = theke:/app/welcome

        Case 3. The uri is a path to a document
            eg. uri = theke:/doc/bible/John 1:1?sources=MorphGNT

        @param uri: (ThekeUri)
        @param request: a WebKit2.URISchemeRequest

        This function is only called by a webview.
        """

        logger.debug("Get content from a theke uri: %s", uri)

        if uri.path[1] == theke.uri.SEGM_APP:
            if uri.path[2] == theke.uri.SEGM_ASSETS:
                # Case 1. Path to an asset file
                f = Gio.File.new_for_path('./assets/' + '/'.join(uri.path[3:]))
                request.finish(f.read(), -1, None)

            else:
                # Case 2. InApp uri
                f = Gio.File.new_for_path('./assets/{}'.format(self.ref.inAppUriData.fileName))
                request.finish(f.read(), -1, 'text/html; charset=utf-8')

        else:
            if uri.path[1] == theke.uri.SEGM_DOC:
                # Case 3. The uri is a path to a document
                if uri.path[2] == theke.uri.SEGM_BIBLE:
                    logger.debug("Load as a sword uri (BIBLE): %s", uri)
                    html = self.get_sword_bible_content()

                elif uri.path[2] == theke.uri.SEGM_BOOK:
                    sourceType = self.index.get_source_type(self.ref.sources[0])

                    if sourceType == theke.index.SOURCETYPE_SWORD:
                        logger.debug("Load as a sword uri (BOOK): %s", uri)
                        html = self.get_sword_book_content()

                    elif sourceType == theke.index.SOURCETYPE_EXTERN:
                        externalUri = self.index.get_source_uri(self.ref.sources[0])

                        logger.debug("Load as a external uri (BOOK): %s", uri)
                        self.preventRefUpdateOnNextWebUriRegistering = True
                        html = self.get_external_book_content(externalUri)

            else:
                raise ValueError('Unsupported theke uri: {}.'.format(uri))

            html_bytes = GLib.Bytes.new(html.encode('utf-8'))
            tmp_stream_in = Gio.MemoryInputStream.new_from_bytes(html_bytes)

            request.finish(tmp_stream_in, -1, 'text/html; charset=utf-8')

    def get_sword_bible_content(self) -> str:
        logger.debug("Load content")

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

    def get_sword_book_content(self) -> str:
        """Load a sword book.
        """

        mod = theke.sword.SwordLibrary().get_book_module(self.ref.get_sources()[0])
        text = mod.get_paragraph(self.ref.section)

        if text is None:
            text = """<p>Ce texte n'a pas été trouvé.</p>
            <p>uri : {}</p>""".format(self.ref.get_uri())
        else:
            text = format_sword_syntax(text)

        return theke.templates.render('book', {
            'ref': self.ref,
            'mod_description': mod.get_description(),
            'text': text})

    def get_external_book_content(self, externalUri) -> None:
        """Load an external source
        """
        return theke.templates.render('external', {
            'ref': self.ref,
            'uri': externalUri})

    def register_web_uri(self, uri, title) -> None:
        """Update properties according to this web page data.
        """

        if self.preventRefUpdateOnNextWebUriRegistering:
            self.preventRefUpdateOnNextWebUriRegistering = False
        else:
            self.set_property("ref", theke.reference.WebpageReference(title, uri = uri))

        self.set_property("toc", None)

        self.set_property("isMorphAvailable", False)

    ### Signals handling

    def handle_webview_click_on_word_cb(self, object, uri) -> None:
        """Do what should be do when a new word is selected in the webview
        Action(s):
            - update morphological data
        """
        pattern_signal_clickOnWord = re.compile(r'(lemma.Strong:(?P<lemma>\w+))?\s?(strong:(?P<strong_raw>(?P<strong_key>\w)(?P<strong_nb>\d+)))?')
        match_signal_clickOnWord = pattern_signal_clickOnWord.match(uri.params.get('lemma', ''))

        # Format the Strong number adding padding zeros
        # (G520 --> G0520)
        strong = "{}{:04}".format(
            match_signal_clickOnWord.group('strong_key'),
            int(match_signal_clickOnWord.group('strong_nb'))
        )

        self.set_property("selectedWord", SelectedWord(
            uri.params.get('word', '?'),
            match_signal_clickOnWord.group('lemma'),
            match_signal_clickOnWord.group('strong_raw'),
            strong,
            uri.params.get('morph', '-'),
            uri.params.get('source')
        ))

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
