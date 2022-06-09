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

    def __init__(self, application, *args, **kwargs) -> None:
        logger.debug("Create a new instance")

        super().__init__(*args, **kwargs)

        self._app = application
        self._librarian = self._app.props.librarian

        self.index = theke.index.ThekeIndex()

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

            # Reset selected sources
            self._selectedSourcesNames = list()

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

        # Collect sources names given in the uri
        # and available for this refernce
        wantedSources = uri.params.get('sources', '')
        wantedSourcesNames = list()

        for wantedSource in wantedSources.split(";"):
             if wantedSource and wantedSource in ref.availableSources:
                wantedSourcesNames.append(wantedSource)

        self.update_context_from_ref(ref, wantedSourcesNames)

    def update_context_from_ref(self, ref, wantedSourcesNames = None) -> None:
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
            if (ref & self.ref) == theke.reference.comparison.DIFFER_BY_VERSE:

                self.ref.verse = ref.verse

                self.is_loading = False
                self.emit("context-updated", NEW_VERSE)
                return

            with self.freeze_notify():
                # Update the table of content only if the document name is different
                if not ((ref & self.ref) & theke.reference.comparison.SAME_BOOKNAME):
                    self.set_property("toc", theke.tableofcontent.get_toc_BIBLE(ref))

                # If needed, select sources to read the document from
                self._selectedSourcesNames = wantedSourcesNames or self._get_default_biblical_sources(ref)

                # Different reference, update all the context
                self.set_property("ref", ref)

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
            self._selectedSourcesNames = wantedSourcesNames or self._get_default_book_sources(ref)

            source = ref.availableSources.get(self._selectedSourcesNames[0])

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

    def get_content_from_theke_uri(self, uri, request) -> None:
        """Return a stream to the content pointed by the theke uri.
        NB. The context has been updated by handle_navigation_action()

        @param uri: (ThekeUri)
        @param request: a WebKit2.URISchemeRequest

        This function is only called by a webview.
        """

        logger.debug("Get content from a theke uri: %s", uri)

        if uri.path[1] == theke.uri.SEGM_APP and uri.path[2] == theke.uri.SEGM_ASSETS:
            # Path to an asset file
            f = Gio.File.new_for_path('./assets/' + '/'.join(uri.path[3:]))
            request.finish(f.read(), -1, None)

        else:
            doc = self._librarian.get_document(self.ref, self.selectedSources)
            request.finish(doc.inputStream, -1, 'text/html; charset=utf-8')

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
    def type(self):
        """Type of the current documment
        """
        return self.ref.type if self.ref else None

    @GObject.Property(type=object)
    def selectedSourcesNames(self):
        """Set of selected sources names
        """
        return self._selectedSourcesNames
    
    @GObject.Property(type=object)
    def selectedSources(self):
        """List of selected sources
        """
        return [self.ref.availableSources[sourceName] for sourceName in self._selectedSourcesNames]

    @GObject.Property(type=object)
    def uri(self):
        """URI of the current documment (with sources)
        """
        uri = self.ref.get_uri()

        if self._selectedSourcesNames:
            uri.params.update({'sources': ";".join(self._selectedSourcesNames)})

        return uri

    @GObject.Property(type=str)
    def contentUri(self):
        """Return the uri of the document
        """

        return self.ref.get_uri().get_encoded_URI()
