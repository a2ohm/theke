from gi.repository import GObject

import theke
import theke.archivist
import theke.document
import theke.reference

import logging
logger = logging.getLogger(__name__)

class ThekeLibrarian(GObject.GObject):
    """With the help of an Archivist, extract and prepare documents to be displayed.
    """
    
    def __init__(self, archivist) -> None:
        self._archivist = archivist

    def get_document(self, ref, sourceNames = None):
        """Find and return a document
        """

        logger.debug("Get a document : {}".format(ref))

        handler = self._archivist.get_document_handler(ref, sourceNames)
        toc = self._archivist.get_document_toc(ref)

        return theke.document.ThekeDocument(ref, handler, toc) if handler else None

    def get_empty_document(self):
        """Return an empty document

        To be used instead of a None where a document is needed
        """
        emptyRef = theke.reference.EmptyReference()
        emptyHandler = theke.archivist.ContentHandler("")

        return theke.document.ThekeDocument(emptyRef, emptyHandler)
