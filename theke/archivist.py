import theke.index

import logging
logger = logging.getLogger(__name__)

class ThekeArchivist():
    """The archivist indexes and stores documents
    """
    
    def updateIndex(self, force = False):
        indexBuilder = theke.index.ThekeIndexBuilder()
        indexBuilder.build(force)