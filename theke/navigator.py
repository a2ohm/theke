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
ERROR_REFERENCE_NOT_SUPPORTED = -1
SAME_DOCUMENT = 0
NEW_DOCUMENT = 1
NEW_SECTION = 2
NEW_VERSE = 3

SOURCES_UPDATED = 4

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


    is_loading = GObject.Property(type=bool, default=False)
    isMorphAvailable  = GObject.Property(type=bool, default=False)
    selectedWord = GObject.Property(type=object)

    def __init__(self, application, *args, **kwargs) -> None:
        logger.debug("Create a new instance")

        super().__init__(*args, **kwargs)

        self._app = application
        self._webview = None
        self._librarian = self._app.props.librarian

        self.index = theke.index.ThekeIndex()

        self._currentDocument = self._librarian.get_empty_document()
        self._selectedSourcesNames = list()

        # Load default biblical sources names from the settings file
        dbsn = self._app.props.settings.get("defaultBiblicalSourcesNames", None)
        if dbsn:
            self._defaultBiblicalSourcesNames = {
                theke.BIBLE_OT: dbsn.get('ot', ['OSHB', 'FreCrampon']),
                theke.BIBLE_NT: dbsn.get('nt', ['MorphGNT', 'FreCrampon']),
            }
        else:
            self._defaultBiblicalSourcesNames = {
                theke.BIBLE_OT: ['OSHB', 'FreCrampon'],
                theke.BIBLE_NT: ['MorphGNT', 'FreCrampon'],
            }

    def register_webview(self, webview) -> None:
        self._webview = webview

    ### GOTO functions

    def goto_uri(self, uri, reload = False) -> None:
        """Ask the webview to load a given uri.

        Notice: all uri requests must go through the webview,
                even if it is then handled by this class.

        @parm uri: (string or ThekeUri)
        """
        if isinstance(uri, theke.uri.ThekeURI):
            uri = uri.get_encoded_URI()

        self._webview.load_uri(uri)

        # if reload or uri != self.uri:
        #     logger.debug("Goto uri: %s", uri)

        #     if isinstance(uri, str):
        #         uri = theke.uri.parse(uri)

        #     # Reset selected sources
        #     self._selectedSourcesNames = list()

        #     self.update_context_from_uri(uri)

    def goto_ref(self, ref, reload = False) -> None:
        """Ask the webview to load a given reference
        """
        logger.warning("GOTO_REF(): should be deleted, use goto_uri() instead")

        if reload or self.ref is None or ref != self.ref:
            logger.debug("Goto ref: %s", ref)

            self.update_context_from_ref(ref)

    def goto_section(self, tocData) -> None:
        """Ask the webview to load a document section
        """

        logger.warning("GOTO_SECTION(): should be deleted, use goto_uri() instead")

        logger.debug("Goto section: %s", tocData)

        if self.doc.toc.type == theke.TYPE_BIBLE:
            # tocData (int): chapter
            if self._currentDocument.ref.chapter != tocData:
                self._currentDocument.ref.chapter = tocData
                self._currentDocument.ref.verse = 0
                self.emit("context-updated", NEW_DOCUMENT)

        else:
            logging.error("This type of TOC (%s) is not supported yet.", self.doc.toc.type)

    def reload(self) -> None:
        self.emit("context-updated", NEW_DOCUMENT)

    ### Edit the context

    def add_source(self, sourceName) -> None:
        """Add a new source to read the document from
        Emit a signal if the source was added
        """

        if sourceName not in self.availableSources:
            logger.debug("This source is not available for this document: %s", sourceName)

        elif sourceName not in self._selectedSourcesNames:
            logger.debug("Add source %s", sourceName)
            self._selectedSourcesNames.append(sourceName)

            if self.ref.type == theke.TYPE_BIBLE:
                self._defaultBiblicalSourcesNames[self.ref.testament].append(sourceName)

            self.emit("context-updated", SOURCES_UPDATED)

    def remove_source(self, sourceName) -> None:
        """Remove a source from the selection
        """
        if sourceName in self._selectedSourcesNames:

            logger.debug("Remove source %s", sourceName)
            self._selectedSourcesNames.remove(sourceName)

            if self.ref.type == theke.TYPE_BIBLE:
                self._defaultBiblicalSourcesNames[self.ref.testament].remove(sourceName)

            # A source should be selected
            # Set a default source if needed
            if len(self._selectedSourcesNames) == 0:
                if self.ref.type == theke.TYPE_BIBLE:
                    logger.debug("Set source to default [bible]")
                    self._get_default_biblical_sources(self.ref)

                elif self.ref.type == theke.TYPE_BOOK:
                    logger.debug("Set source to default [book]")
                    self._get_default_book_sources(self.ref)

            self.emit("context-updated", SOURCES_UPDATED)

    ### Update context (from URI)

    def update_context_from_uri(self, uri) -> None:
        """Get a document given its uri

        This function should be called by any webview handling a theke uri
        """
        if self._currentDocument is not None:
            uriComparison = uri & self._currentDocument.uri
            if uriComparison == theke.uri.comparison.SAME_URI:
                # This is exactly the current uri, the context stays the same
                logger.debug("Update context (same uri, skip)")
                return SAME_DOCUMENT

            elif uriComparison == theke.uri.comparison.DIFFER_BY_FRAGMENT:
                # Same uri with a different fragment
                logger.debug("Update context (section)")
                self._currentDocument.section = uri.fragment
                return NEW_SECTION

        ref = theke.reference.get_reference_from_uri(uri)

        # Collect sources names given in the uri
        # and available for this reference
        wantedSources = uri.params.get('sources', '')
        wantedSourcesNames = list()

        for wantedSource in wantedSources.split(";"):
             if wantedSource and wantedSource in ref.availableSources:
                wantedSourcesNames.append(wantedSource)
        
        return self.update_context_from_ref(ref, wantedSourcesNames)

    def update_context_from_ref(self, ref, wantedSourcesNames = None) -> None:
        """Update local context according to the ref
        """

        refComparisonMask = ref & self._currentDocument.ref if self._currentDocument else theke.reference.comparison.NOTHING_IN_COMMON        

        if ref.type == theke.TYPE_BIBLE:
            logger.debug("Update context [bible]")

            if refComparisonMask == theke.reference.comparison.DIFFER_BY_VERSE:
                # Same biblical reference with a different verse number
                self._currentDocument.section = ref.verse
                return NEW_VERSE

            with self.freeze_notify():
                # # Update the table of content only if the document name is different
                # if not ((refComparisonMask) & theke.reference.comparison.SAME_BOOKNAME):
                #     self.set_property("toc", theke.tableofcontent.get_toc_BIBLE(ref))

                # If needed, select sources to read the document from
                self._selectedSourcesNames = wantedSourcesNames or self._get_default_biblical_sources(ref)

                # Different reference, update all the context
                #self.set_property("ref", ref)

            self._currentDocument = self._librarian.get_document(ref, self._selectedSourcesNames)
            return NEW_DOCUMENT

        # elif ref.type == theke.TYPE_BOOK:

        #     # Same book reference with a different section name
        #     if (refComparisonMask) == theke.reference.comparison.DIFFER_BY_SECTION:
        #         logger.debug("Update context [book] (section)")

        #         self._currentDocument.section = ref.section
        #         #self.is_loading = False
        #         #self.emit("context-updated", NEW_SECTION)
        #         return self._currentDocument

        #     logger.debug("Update context [book]")

        #     # If needed, select sources to read the document from
        #     self._selectedSourcesNames = wantedSourcesNames or self._get_default_book_sources(ref)

        #     source = ref.availableSources.get(self._selectedSourcesNames[0])

        #     if source.type == theke.index.SOURCETYPE_EXTERN:
        #         if not theke.externalCache.is_source_cached(source.name):
        #             contentUri = self.index.get_source_uri(source.name)
        #             if not theke.externalCache.cache_document_from_external_source(source.name, contentUri):
        #                 # Fail to cache the document from the external source
        #                 self.is_loading = False
        #                 self.emit("navigation-error", theke.NavigationErrors.EXTERNAL_SOURCE_INACCESSIBLE)
        #                 return

        #         if not theke.externalCache.is_cache_cleaned(source.name):
        #             theke.externalCache._build_clean_document(source.name)

        #     with self.freeze_notify():
        #         self.set_property("ref", ref)
        #         self.set_property("toc", None)
        #         self.set_property("isMorphAvailable", False)

        #     self.emit("context-updated", NEW_DOCUMENT)
        #     return

        elif ref.type == theke.TYPE_INAPP:
            logger.debug("Update context [inApp]")

            with self.freeze_notify():
                self.set_property("isMorphAvailable", False)

            self._currentDocument = self._librarian.get_document(ref)
            return NEW_DOCUMENT

        else:
            logger.error("Reference type not supported: %s", ref)
            return ERROR_REFERENCE_NOT_SUPPORTED

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
    def _get_default_biblical_sources(self, ref):
        """Return default biblical sources
        """
        logger.debug("Automaticaly set sources ...")
        
        # Start from scratch
        sourcesNames = list()

        for sourceName in self._defaultBiblicalSourcesNames[ref.testament]:
            if sourceName in ref.availableSources:
                sourcesNames.append(sourceName)
        
        # If none of default biblical sources are available for this biblical book
        # use the first available source
        if self.ref is None or (self.ref.type == theke.TYPE_BIBLE and ref.testament == self.ref.testament):
            return self._selectedSourcesNames or sourcesNames or [list(ref.availableSources.keys())[0]]

        return sourcesNames or [list(ref.availableSources.keys())[0]]

    def _get_default_book_sources(self, ref):
        """Return default book sources
        """
        logger.debug("Automaticaly set sources ...")

        # TODO: Faire un choix plus intelligent ...
        return [list(ref.availableSources.keys())[0]]
    
    ### Properties

    @GObject.Property(type=str)
    def doc(self):
        """Current documment
        """
        return self._currentDocument
