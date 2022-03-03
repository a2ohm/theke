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
import theke.externalCache
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
        'context-updated': (GObject.SignalFlags.RUN_LAST, None, (int,)),
        'navigation-error': (GObject.SignalFlags.RUN_LAST, None, (int,))
        }

    ref = GObject.Property(type=object)

    toc = GObject.Property(type=object)

    is_loading = GObject.Property(type=bool, default=False)
    isMorphAvailable  = GObject.Property(type=bool, default=False)
    selectedWord = GObject.Property(type=object)

    def __init__(self, *args, **kwargs) -> None:
        logger.debug("Create a new instance")

        super().__init__(*args, **kwargs)

        self.index = theke.index.ThekeIndex()
        self._selectedSourcesNames = set()

    def goto_uri(self, uri, reload = False) -> None:
        """Ask the webview to load a given uri.

        Notice: all uri requests must go through the webview,
                even if it is then handled by this class.

        @parm uri: (string or ThekeUri)
        """
        if reload or self.ref is None or uri != self.ref.get_uri():
            logger.debug("Goto uri: %s", uri)

            if isinstance(uri, str):
                uri = theke.uri.parse(uri)

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
        """Add a new source to read the document from
        Emit a signal if the source was added
        """

        if sourceName not in self.availableSources:
            logger.debug("This source is not available for this document: %s", sourceName)
            return False

        elif sourceName not in self._selectedSourcesNames:
            logger.debug("Add source %s", sourceName)
            self._selectedSourcesNames.add(sourceName)
            self.emit("context-updated", SOURCES_UPDATED)

    def remove_source(self, sourceName) -> None:
        """Remove a source from the selection
        """
        if sourceName in self._selectedSourcesNames:

            logger.debug("Remove source %s", sourceName)
            self._selectedSourcesNames.discard(sourceName)

            # A source should be selected
            # Set a default source if needed
            if len(self._selectedSourcesNames) == 0:
                if self.ref.type == theke.TYPE_BIBLE:
                    logger.debug("Set source to default [bible]")
                    self._select_biblical_sources(self.ref)

                elif self.ref.type == theke.TYPE_BOOK:
                    logger.debug("Set source to default [book]")
                    self._select_book_sources(self.ref)

            self.emit("context-updated", SOURCES_UPDATED)

    ### Update context (from URI)

    def update_context_from_uri(self, uri) -> None:
        """Update local context according to the uri
        """
        if self.ref is not None:
            uriComparison = uri & self.ref.get_uri()
            if uriComparison == theke.uri.comparison.SAME_URI:
                # This is exactly the current uri, the context stays the same
                logger.debug("Update context (skip)")
                self.is_loading = False
                self.emit("context-updated", SAME_DOCUMENT)
                return

            elif uriComparison == theke.uri.comparison.DIFFER_BY_FRAGMENT:
                # Same uri with a different fragment
                logger.debug("Update context (section)")
                self.ref.section = uri.fragment
                self.emit("context-updated", NEW_SECTION)
                return

        ref = theke.reference.get_reference_from_uri(uri)

        # Reset selected sources
        self._selectedSourcesNames = set()

        # Add wanted sources from the uri
        wantedSources = uri.params.get('sources', '')
        for wantedSource in wantedSources.split(";"):
            if wantedSource in ref.get_available_sources().keys():
                self._selectedSourcesNames.add(wantedSource)

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
        self.is_loading = True
        
        if ref.type == theke.TYPE_BIBLE:
            logger.debug("Update context [bible]")

            # Same biblical reference with a different verse number
            if (ref & self.ref) == theke.reference.comparison.BR_DIFFERENT_VERSE:

                self.ref.verse = ref.verse

                self.is_loading = False
                self.emit("context-updated", NEW_VERSE)
                return

            with self.freeze_notify():
                # Update the table of content only if the document name is different
                if self.ref is None or ref.documentName != self.ref.documentName:
                    self.set_property("toc", theke.tableofcontent.get_toc_BIBLE(ref))

                # Different reference, update all the context
                self.set_property("ref", ref)

                # If needed, select sources to read the document from
                if not self._selectedSourcesNames:
                    self._select_biblical_sources(ref)

            self.emit("context-updated", NEW_DOCUMENT)
            return

        elif ref.type == theke.TYPE_BOOK:

            # Same book reference with a different section name
            if (ref & self.ref) == theke.reference.comparison.DIFFER_BY_SECTION:
                logger.debug("Update context [book] (section)")

                self.ref.section = ref.section
                self.is_loading = False
                self.emit("context-updated", NEW_SECTION)
                return

            logger.debug("Update context [book]")

            # If needed, select sources to read the document from
            if not self._selectedSourcesNames:
                self._select_book_sources(ref)

            source = ref.get_available_sources().get(list(self._selectedSourcesNames)[0])

            if source.type == theke.index.SOURCETYPE_EXTERN:
                if not theke.externalCache.is_source_cached(source.name):
                    contentUri = self.index.get_source_uri(source.name)
                    if not theke.externalCache.cache_document_from_external_source(source.name, contentUri):
                        # Fail to cache the document from the external source
                        self.is_loading = False
                        self.emit("navigation-error", theke.NavigationErrors.EXTERNAL_SOURCE_INACCESSIBLE)
                        return

                if not theke.externalCache.is_cache_cleaned(source.name):
                    theke.externalCache._build_clean_document(source.name)

            with self.freeze_notify():
                self.set_property("ref", ref)
                self.set_property("toc", None)
                self.set_property("isMorphAvailable", False)

            self.emit("context-updated", NEW_DOCUMENT)
            return

        elif ref.type == theke.TYPE_INAPP:
            logger.debug("Update context [inApp]")

            with self.freeze_notify():
                self.set_property("ref", ref)
                self.set_property("toc", None)
                self.set_property("isMorphAvailable", False)

            self.emit("context-updated", NEW_DOCUMENT)
            return

        else:
            logger.error("Reference type not supported: %s", ref)
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
                    source = self.ref.get_available_sources().get(list(self._selectedSourcesNames)[0])

                    if source.type == theke.index.SOURCETYPE_SWORD:
                        logger.debug("Load as a sword uri (BOOK): %s", uri)
                        html = self.get_sword_book_content(source.name)

                    if source.type == theke.index.SOURCETYPE_EXTERN:
                        logger.debug("Load as an extern uri (BOOK): %s", uri)
                        html = self.get_external_book_content(source.name)

            else:
                # Temporary solution:
                #   Permit to load document from a cached source
                #   even if it contains images and other contents
                #   that are not cached

                #raise ValueError('Unsupported theke uri: {}.'.format(uri))
                logger.error('Unsupported theke uri: %s.', uri)
                html = ''

            html_bytes = GLib.Bytes.new(html.encode('utf-8'))
            tmp_stream_in = Gio.MemoryInputStream.new_from_bytes(html_bytes)

            request.finish(tmp_stream_in, -1, 'text/html; charset=utf-8')

    def get_sword_bible_content(self) -> str:
        logger.debug("Load content")

        documents = []
        verses = []
        isMorphAvailable = False

        for sourceName in self._selectedSourcesNames:
            markup = theke.sword.MARKUP.get(sourceName, theke.sword.FMT_PLAIN)
            mod = theke.sword.SwordLibrary(markup=markup).get_bible_module(sourceName)
            documents.append({
                'lang' : mod.get_lang(),
                'source': sourceName
            })
            verses.append(mod.get_chapter(self.ref.bookName, self.ref.chapter))

            isMorphAvailable |= "OSISMorph" in mod.get_global_option_filter()

        self.set_property("isMorphAvailable", isMorphAvailable)

        return theke.templates.render('bible', {
            'documents': documents,
            'verses': verses,
            'ref': self.ref
        })

    def get_sword_book_content(self, sourceName) -> str:
        """Load a sword book.
        """

        mod = theke.sword.SwordLibrary().get_book_module(sourceName)
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

    def get_external_book_content(self, sourceName) -> None:
        """Load an external source
        """

        document_path = theke.externalCache.get_best_source_file_path(sourceName, relative=True)

        return theke.templates.render('external_book', {
            'ref': self.ref,
            'document_path': document_path})

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

    ### Helpers
    def _select_biblical_sources(self, ref):
        logger.debug("Automaticaly add sources ...")
        # TODO: Faire un choix plus intelligent ...
        self._selectedSourcesNames.add(list(ref.get_available_sources().keys())[0])

    def _select_book_sources(self, ref):
        # No sources are selected, the navigator should decide by itself
        logger.debug("Automaticaly add sources ...")
        # TODO: Faire un choix plus intelligent ...
        self._selectedSourcesNames.add(list(ref.get_available_sources().keys())[0])
    
    ### Properties
    
    @GObject.Property(type=str)
    def availableSources(self):
        """Available sources of the current documment
        """
        return list(self.ref.get_available_sources().keys())

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

    @GObject.Property(type=object)
    def selectedSourcesNames(self):
        """Set of selected sources names
        """
        return self._selectedSourcesNames

    @GObject.Property(type=object)
    def uri(self):
        """URI of the current documment (with sources)
        """
        uri = self.ref.get_uri()
        uri.params.update({'sources': ";".join(self._selectedSourcesNames)})

        return uri

    @GObject.Property(type=str)
    def contentUri(self):
        """Return the uri of the document
        """

        return self.ref.get_uri().get_encoded_URI()
