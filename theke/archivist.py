from gi.repository import GObject

import theke.index

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
