from gi.repository import GObject
from gi.repository import Gio
from gi.repository import GLib

import theke
import theke.index
import theke.externalCache
import theke.tableofcontent
import theke.templates

import threading

import logging
logger = logging.getLogger(__name__)

class ThekeArchivist(GObject.GObject):
    """The archivist indexes and stores documents
    """

    def __init__(self) -> None:
        self._index = theke.index.ThekeIndex()

    def update_index(self, force = False):
        """Update the index
        """
        indexBuilder = theke.index.ThekeIndexBuilder()
        indexBuilder.build(force)

    def get_document_handler(self, ref, sourceNames):
        """Return a handler providing an input stream to the document

        @param sourceNames: list of source names
        """

        sources = [self._index.get_source_data(sourceName) for sourceName in sourceNames] if sourceNames else None

        if ref.type == theke.TYPE_INAPP:
            logger.debug("Get a document handler [inApp] : {}".format(ref))
            file_path = './assets/{}'.format(ref.inAppUriData.fileName)
            return FileHandler(file_path, sources)

        if ref.type == theke.TYPE_BIBLE:
            logger.debug("Get a document handler [bible] : {}".format(ref))

            documents = []
            verses = []
            #isMorphAvailable = False

            for source in sources:
                markup = theke.sword.MARKUP.get(source.name, theke.sword.FMT_PLAIN)
                mod = theke.sword.SwordLibrary(markup=markup).get_bible_module(source.name)
                documents.append({
                    'lang' : mod.get_lang(),
                    'source': source.name
                })
                verses.append(mod.get_chapter(ref.bookName, ref.chapter))

                #isMorphAvailable |= "OSISMorph" in mod.get_global_option_filter()

            content = theke.templates.render('bible', {
                'documents': documents,
                'verses': verses,
                'ref': ref
            })

            return ContentHandler(content, sources)

        if ref.type == theke.TYPE_BOOK:
            
            # For now, can only open the first source
            source = sources[0]

            if source.type == theke.index.SOURCETYPE_SWORD:
                logger.warning("Cannot open sword books : %s", ref)
                return ContentHandler("<p>Les livres provenant d'un module sword ne peuvent pas être ouvert par Theke.</p>", [source])

            if source.type == theke.index.SOURCETYPE_EXTERN:
                logger.debug("Get a document handler [external book] : %s", ref)

                if not theke.externalCache.is_source_cached(source.name):
                    contentUri = self._index.get_source_uri(source.name)

                    if not theke.externalCache.cache_document_from_external_source(source.name, contentUri):
                        # Fail to cache the document from the external source
                        #self.is_loading = False
                        #self.emit("navigation-error", theke.NavigationErrors.EXTERNAL_SOURCE_INACCESSIBLE)
                        return None

                if not theke.externalCache.is_cache_cleaned(source.name):
                    theke.externalCache._build_clean_document(source.name)

                document_path = theke.externalCache.get_best_source_file_path(source.name, relative=True)

                content = theke.templates.render('external_book', {
                    'ref': ref,
                    'document_path': document_path})

                return ContentHandler(content, [source])

        return None

    def get_document_toc(self, ref):
        """Return the table of contents of a reference
        """
        if ref.type == theke.TYPE_BIBLE:
            return theke.tableofcontent.get_toc_BIBLE(ref)

        return None
    
    ### External documents
    def clean_external_document_async(self, source, feedback, callback) -> None:
        """Asynchronously clean an external document

        @param feedback: function taking two arguments
            isWIP (bool): True if the work is in progress
            label (string): textual feedback for the user
        @param callback: function called at the end
        """
        logger.debug("Asynchronously clean an external document")
        feedback(True, "Actualisation de la mise en page")

        def _do_cleaning():
            theke.externalCache._build_clean_document(source.name)
            GLib.idle_add(callback)

        thread = threading.Thread(target=_do_cleaning, daemon=True)
        thread.start()
    
    def download_and_clean_external_document_async(self, source, feedback, callback) -> None:
        """Asynchronously download and clean an external document

        @param feedback: function taking two arguments
            isWIP (bool): True if the work is in progress
            label (string): textual feedback for the user
        @param callback: function called at the end taking one argument
            final state (bool): True if the task was successful
        """
        logger.debug("Asynchronously download and clean an external document")
        feedback(True, "Téléchargement du document")
        contentUri = self.get_source_uri(source.name)

        def _do_downloading_and_cleaning():
            if theke.externalCache.cache_document_from_external_source(source.name, contentUri):
                # Success to cache the document from the external source
                GLib.idle_add(feedback, True, "Actualisation de la mise en page")
                theke.externalCache._build_clean_document(source.name)
                GLib.idle_add(callback, True)

            else:
                GLib.idle_add(feedback, False)
                GLib.idle_add(callback, False)
        
        thread = threading.Thread(target=_do_downloading_and_cleaning, daemon=True)
        thread.start()

    ### API: proxy to the ThekeIndex
    def get_source_uri(self, sourceName):
        """Get the uri of a source from the index
        """
        return self._index.get_source_uri(sourceName)

    def list_external_documents(self):
        """List external documents from the index
        """
        return self._index.list_external_documents()

    def list_documents_by_type(self, documentType):
        """List documents from the index by type
        """
        return self._index.list_documents_by_type(documentType)

    def list_sword_sources(self, contentType = None):
        """List sources from the index

        @param contentType: theke.index.MODTYPE_*
        """
        return self._index.list_sources(theke.index.SOURCETYPE_SWORD, contentType)

class ContentHandler():
    def __init__(self, content, sources = None) -> None:
        """
        @param sources: list of source datas
        """
        self._content = content
        self._sources = sources

    def get_input_stream(self):
        return Gio.MemoryInputStream.new_from_data(self._content.encode('utf-8'))

    def get_sources(self):
        return self._sources

class FileHandler():
    def __init__(self, filePath, sources = None) -> None:
        """
        @param sources: list of source datas
        """
        self._filePath = filePath
        self._sources = sources

    def get_input_stream(self):
        return Gio.File.new_for_path(self._filePath).read()
    
    def get_sources(self):
        return self._sources
