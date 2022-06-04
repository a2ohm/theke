import theke.index

import logging
logger = logging.getLogger(__name__)

class ThekeArchivist():
    """The archivist indexes and stores documents
    """

    def update_index(self, force = False):
        """Update the index
        """
        indexBuilder = theke.index.ThekeIndexBuilder()
        indexBuilder.build(force)
