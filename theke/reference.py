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

    elif uri.scheme == 'sword':
        if uri.path[1] == theke.uri.SWORD_BIBLE:
            return BiblicalReference(uri.path[2], rawSources = uri.params.get('sources', defaultSource))
        
        elif uri.path[1] == theke.uri.SWORD_BOOK:
            if len(uri.path) == 3:
                return BookReference(uri.path[2], section = 0)
            else:
                return BookReference(uri.path[2], section = uri.path[3])
        
        else:
            raise ValueError('Unsupported book type: {}.'.format(uri.path[1]))  

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
TYPE_BOOK = 3

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

        self.sources = kwargs.get('rawSources', None).split(';')
        self.tags = kwargs.get('tags', [])

    def add_source(self, source) -> bool:
        """Append a source to the reference
        Return True if the source was added
        """
        if source not in self.sources:
            logger.debug("ThekeReference - Add source {}".format(source))
            self.sources.append(source)
            return True

        return False

    def remove_source(self, source, defaultSource) -> bool:
        """Remove a source
        As self.sources can not be empty, a default source shoud be given
        """
        if source not in self.sources:
            return False

        logger.debug("ThekeReference - Remove source {}".format(source))
        self.sources.remove(source)

        if len(self.sources) == 0:
            logger.debug("ThekeReference - Set source to default {}".format(defaultSource))
            self.sources.append(defaultSource)

        return True

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
        if self.sources is None:
            return theke.uri.build('sword', ['', theke.uri.SWORD_BIBLE, self.rawReference])
        
        return theke.uri.build('sword', ['', theke.uri.SWORD_BIBLE, self.rawReference],
            sources = self.sources)

class BookReference(Reference):
    def __init__(self, rawReference, section = 0, **kwargs):
        super().__init__(rawReference, **kwargs)

        self.type = TYPE_BOOK
        self.bookName = self.rawReference
        self.section = section
        self.documentName = self.bookName

    def get_repr(self) -> str:
        if self.section == 0:
            return "{}".format(self.bookName)
        else:
            return "{} {}".format(self.bookName, self.section)

    def get_short_repr(self) -> str:
        return "{}".format(self.bookName)

    def get_uri(self):
        return theke.uri.build('sword', ['', theke.uri.SWORD_BOOK, self.rawReference])

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
