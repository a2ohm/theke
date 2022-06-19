from gi.repository import GObject
from gi.repository import Gio
from gi.repository import GLib

import theke
import theke.index
import theke.externalCache
import theke.tableofcontent
import theke.templates

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

            #self.set_property("isMorphAvailable", isMorphAvailable)

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

            logger.debug("Get a document handler [external book] : %s", ref)

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

    ### API: proxy to the ThekeIndex
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
        self._content = content
        self._sources = sources

    def get_input_stream(self):
        return Gio.MemoryInputStream.new_from_data(self._content.encode('utf-8'))

    def get_sources(self):
        return self._sources

class FileHandler():
    def __init__(self, filePath, sources = None) -> None:
        self._filePath = filePath
        self._sources = sources

    def get_input_stream(self):
        return Gio.File.new_for_path(self._filePath).read()
    
    def get_sources(self):
        return self._sources
