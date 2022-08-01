from collections import namedtuple

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

    isMorphAvailable  = GObject.Property(type=bool, default=False)
    selectedWord = GObject.Property(type=object)

    def __init__(self, application, parentWindow, *args, **kwargs) -> None:
        logger.debug("Create a new instance")

        super().__init__(*args, **kwargs)

        self._app = application
        self._parentWindow = parentWindow
        self._webview = None
        self._librarian = self._app.props.librarian

        self._currentDocument = self._librarian.get_empty_document()

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

    def goto_uri(self, uri) -> None:
        """Ask the webview to load a given uri.

        Notice: all uri requests must go through the webview,
                even if it is then handled by this class.

        @parm uri: (string or ThekeUri)
        """
        self.set_loading(True)

        if isinstance(uri, theke.uri.ThekeURI):
            uri = uri.get_encoded_URI()

        self._webview.load_uri(uri)

    def goto_ref(self, ref, reload = False) -> None:
        """Ask the webview to load a given reference
        """
        if reload or ref != self._currentDocument.ref:
            logger.debug("Goto ref: %s", ref)
            self.set_loading(True)
            self.update_context_from_ref(ref)
            self.reload()

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
        #self.emit("context-updated", NEW_DOCUMENT)
        self._webview.load_uri(self._currentDocument.uri.get_encoded_URI())

    ### Edit the context

    def add_source(self, newSourceName) -> None:
        """Add a new source to read the document from
        Emit a signal if the source was added
        """

        sourceNames = self._currentDocument.sourceNames

        if newSourceName not in self._currentDocument.availableSources:
            logger.debug("This source is not available for this document: %s", newSourceName)

        elif newSourceName not in sourceNames:
            logger.debug("Add source %s", newSourceName)
            sourceNames.append(newSourceName)

            if self._currentDocument.type == theke.TYPE_BIBLE:
                self._defaultBiblicalSourcesNames[self._currentDocument.ref.testament] = sourceNames

            self._currentDocument = self._librarian.get_document(self._currentDocument.ref, sourceNames)
            self.emit("context-updated", SOURCES_UPDATED)

            self.reload()

    def remove_source(self, obsoleteSourceName) -> None:
        """Remove a source from the selection
        Emit a signal if the source was removed
        """
        sourceNames = self._currentDocument.sourceNames

        if obsoleteSourceName in sourceNames:

            logger.debug("Remove source %s", obsoleteSourceName)
            sourceNames.remove(obsoleteSourceName)

            # A source should be selected
            # Set a default source if needed
            if len(sourceNames) == 0:
                if self._currentDocument.type == theke.TYPE_BIBLE:
                    logger.debug("Set source to default [bible]")
                    sourceNames = self._get_default_biblical_sources(self._currentDocument.ref)

                elif self._currentDocument.type == theke.TYPE_BOOK:
                    logger.debug("Set source to default [book]")
                    sourceNames = self._get_default_book_sources(self._currentDocument.ref)
            
            if self._currentDocument.type == theke.TYPE_BIBLE:
                self._defaultBiblicalSourcesNames[self._currentDocument.ref.testament] = sourceNames

            self._currentDocument = self._librarian.get_document(self._currentDocument.ref, sourceNames)
            self.emit("context-updated", SOURCES_UPDATED)

            self.reload()

    ### Update context (from URI)

    def update_context_from_uri(self, uri) -> None:
        """Get a document given its uri

        This function should be called by any webview handling a theke uri
        """

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

            sourcesNames = wantedSourcesNames or self._get_default_biblical_sources(ref)
            self._currentDocument = self._librarian.get_document(ref, sourcesNames)

            self.emit("context-updated", NEW_DOCUMENT)
            return NEW_DOCUMENT

        elif ref.type == theke.TYPE_BOOK:
            logger.debug("Update context [book]")

            if refComparisonMask == theke.reference.comparison.DIFFER_BY_SECTION:
                # Same book reference with a different section name
                self._currentDocument.section = ref.section
                return NEW_SECTION

            # If needed, select sources to read the document from
            sourcesNames = wantedSourcesNames or self._get_default_book_sources(ref)
            self._currentDocument = self._librarian.get_document(ref, sourcesNames)

            self.emit("context-updated", NEW_DOCUMENT)
            return NEW_DOCUMENT

        elif ref.type == theke.TYPE_INAPP:
            logger.debug("Update context [inApp]")

            with self.freeze_notify():
                self.set_property("isMorphAvailable", False)

            self._currentDocument = self._librarian.get_document(ref)
            self.emit("context-updated", NEW_DOCUMENT)
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

    ### GUI
    def set_loading(self, isLoading, loadingMsg = "Chargement ...") -> None:
        self._parentWindow.set_loading(isLoading, loadingMsg)

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
