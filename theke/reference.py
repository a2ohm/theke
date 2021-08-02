import re
import logging

from typing import Any

import theke.uri

logger = logging.getLogger(__name__)

def get_reference_from_uri(uri, defaultSource = None):
    '''Return a reference according to an uri.
        sword:/bible/John 1:1 --> biblical reference to Jn 1,1

        @param uri: (ThekeUri)
    '''
    if uri.scheme == 'theke':
        return InAppReference(uri.path[0])

    if uri.scheme != 'sword':
        raise ValueError('Unsupported scheme: {}.'.format(uri.scheme))

    if uri.path[1] != 'bible':
        raise ValueError('Unsupported book type: {}.'.format(uri.path[1]))

    return BiblicalReference(uri.path[2], source = uri.params.get('source', defaultSource))

def parse_biblical_reference(rawReference):
    """Extract book name, chapter and verse from a raw reference
    """
    pattern_br_EN = re.compile(r'^([\w\s]+) (\d+)(:(\d+))?$')
    match_br_EN = pattern_br_EN.match(rawReference)

    if match_br_EN is not None:
        if match_br_EN.group(4) is None:
            # Chapter reference: "bookName chapter"
            return match_br_EN.group(1), int(match_br_EN.group(2)), 0
        else:
            # Verse reference: "bookName chapter:verse"
            return match_br_EN.group(1), int(match_br_EN.group(2)), int(match_br_EN.group(4))

    # This is not a biblical reference
    return None

TYPE_UNKNOWN = 0
TYPE_BIBLE = 1
TYPE_INAPP = 2

class Reference():
    '''Reference of any document readable by Theke.
    (application screen, Sword reference)
    '''

    def __init__(self, rawReference, **kwargs):
        self.rawReference = rawReference
        self.documentName = ''
        self.type = TYPE_UNKNOWN

    def get_repr(self):
        """Representation of the reference
        eg. long title
        """
        return self.rawReference

    def get_short_repr(self):
        """Short representation of the refenrece
        eg. short title
        """
        return self.rawReference

    def get_uri(self):
        raise NotImplementedError

class BiblicalReference(Reference):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        logger.debug("Reference − Create a biblical reference")

        self.type = TYPE_BIBLE
        self.bookName, self.chapter, self.verse = parse_biblical_reference(self.rawReference)
        self.documentName = self.bookName
        self.source = kwargs.get('source', None)
        self.tags = kwargs.get('tags', [])

    def get_repr(self):
        """Return a long representation of the biblical reference
        eg. John 1:1
        """
        if self.verse == 0:
            return "{} {}".format(self.bookName, self.chapter)
        
        return "{} {}:{}".format(self.bookName, self.chapter, self.verse)

    def get_short_repr(self):
        """Return a short representation of the biblical reference
        (without verse number)
        eg. John 1
        """
        return "{} {}".format(self.bookName, self.chapter)

    def get_uri(self):
        if self.source is None:
            return theke.uri.build('sword', ['', theke.uri.SWORD_BIBLE, self.rawReference])
        
        return theke.uri.build('sword', ['', theke.uri.SWORD_BIBLE, self.rawReference],
            {'sources': self.source})

class InAppReference(Reference):
    def __init__(self, rawReference, *args, **kwargs):
        super().__init__(rawReference, *args, **kwargs)

        logger.debug("Reference − Create a inApp reference")

        self.type = TYPE_INAPP
        self.inAppUriData = theke.uri.inAppURI[self.rawReference]

    def get_uri(self) -> Any:
        return theke.uri.build('theke', [self.rawReference])

    def get_repr(self) -> str:
        """Long representation
        (title of the page)
        """
        return self.inAppUriData.title

    def get_short_repr(self) -> str:
        """ Short representation
        (short title)
        """
        return self.inAppUriData.shortTitle
