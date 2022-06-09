from gi.repository import GObject

import theke
import theke.archivist
import theke.document

import logging
logger = logging.getLogger(__name__)

class ThekeLibrarian(GObject.GObject):
    """With the help of an Archivist, extract and prepare documents to be displayed.
    """
    
    def __init__(self, archivist) -> None:
        self._archivist = archivist

    def get_document(self, ref, sources):
        """Find and return a document
        """

        logger.debug("Get a document : {}".format(ref))

        handler = self._archivist.get_document_handler(ref, sources)
        return theke.document.ThekeDocument(ref, handler) if handler else None
