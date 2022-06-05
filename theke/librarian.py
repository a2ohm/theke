from gi.repository import GObject

import theke
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

        if ref.type == theke.TYPE_INAPP:
            file_path = './assets/{}'.format(ref.inAppUriData.fileName)
            handler = theke.document.FileHandler(file_path)

            return theke.document.ThekeDocument(ref, handler)
