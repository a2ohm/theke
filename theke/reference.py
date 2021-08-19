import re
import logging

from typing import Any

import theke
import theke.uri
import theke.index

logger = logging.getLogger(__name__)

def get_reference_from_uri(uri, defaultSources = None):
    '''Return a reference according to an uri.
        sword:/bible/John 1:1 --> biblical reference to Jn 1,1

        @param uri: (ThekeUri)
        @param defaultSources: (str)
    '''
    if uri.scheme == 'theke':
        return InAppReference(uri.path[0])

    if uri.scheme == 'sword':
        if uri.path[1] == theke.uri.SWORD_BIBLE:
            return BiblicalReference(uri.path[2], rawSources = uri.params.get('sources', defaultSources))

        if uri.path[1] == theke.uri.SWORD_BOOK:
            if len(uri.path) == 3:
                return BookReference(uri.path[2], section = 0)

            return BookReference(uri.path[2], section = uri.path[3])

        raise ValueError('Unsupported book type: {}.'.format(uri.path[1]))

def parse_reference(rawReference):
    """Parse a raw reference
    """
    pattern_r = re.compile(r'^(\D+)(.*)')
    match_r = pattern_r.match(rawReference)

    if match_r is not None:
        documentName = match_r.group(1).strip()
        documentType = theke.index.ThekeIndex().get_document_type(documentName)

        if documentType == theke.TYPE_BIBLE:
            return BiblicalReference(rawReference)

        if documentType == theke.TYPE_BOOK:
            return BookReference(documentName, match_r.group(2))

    return Reference(rawReference)

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

class Reference():
    '''Reference of any document readable by Theke.
    (application screen, Sword reference)
    '''

    def __init__(self, rawReference):
        self.rawReference = rawReference
        self.documentTitle = rawReference
        self.documentShortTitle = rawReference
        self.type = theke.TYPE_UNKNOWN

    def get_repr(self):
        """Representation of the reference
        eg. long title
        """
        return self.documentTitle

    def get_short_repr(self):
        """Short representation of the refenrece
        eg. short title
        """
        return self.documentShortTitle

    def get_uri(self):
        raise NotImplementedError

class BiblicalReference(Reference):
    def __init__(self, rawReference, rawSources = None, tags = None):
        super().__init__(rawReference)

        logger.debug("Reference − Create a biblical reference : %s", rawReference)

        self.type = theke.TYPE_BIBLE
        self.bookName, self.chapter, self.verse = parse_biblical_reference(self.rawReference)
        self.documentTitle = self.bookName
        self.documentShortTitle = self.bookName

        self.sources = rawSources.split(';') if rawSources is not None else None
        self.tags = tags

    def add_source(self, source) -> bool:
        """Append a source to the reference
        Return True if the source was added
        """
        if source not in self.sources:
            logger.debug("ThekeReference - Add source %s", source)
            self.sources.append(source)
            return True

        return False

    def remove_source(self, source, defaultSource) -> bool:
        """Remove a source
        As self.sources can not be empty, a default source shoud be given
        """
        if source not in self.sources:
            return False

        logger.debug("ThekeReference - Remove source %s", source)
        self.sources.remove(source)

        if len(self.sources) == 0:
            logger.debug("ThekeReference - Set source to default %s", defaultSource)
            self.sources.append(defaultSource)

        return True

    def get_repr(self):
        """Return a long representation of the biblical reference
        eg. John 1:1
        """
        if self.verse == 0:
            return "{} {}".format(self.documentTitle, self.chapter)

        return "{} {}:{}".format(self.documentTitle, self.chapter, self.verse)

    def get_short_repr(self):
        """Return a short representation of the biblical reference
        (without verse number)
        eg. John 1
        """
        return "{} {}".format(self.documentShortTitle, self.chapter)

    def get_uri(self):
        if self.verse == 0:
            return theke.uri.build('sword', ['', theke.uri.SWORD_BIBLE,
                "{} {}".format(self.bookName, self.chapter)],
                sources = self.sources)
        
        return theke.uri.build('sword', ['', theke.uri.SWORD_BIBLE,
            "{} {}:{}".format(self.bookName, self.chapter, self.verse)],
            sources = self.sources)

class BookReference(Reference):
    def __init__(self, rawReference, section = 0):
        super().__init__(rawReference)

        self.type = theke.TYPE_BOOK
        self.documentTitle = self.rawReference
        self.section = section

    def get_repr(self) -> str:
        if self.section == 0:
            return "{}".format(self.documentTitle)
        else:
            return "{} {}".format(self.documentTitle, self.section)

    def get_short_repr(self) -> str:
        return "{}".format(self.documentShortTitle)

    def get_uri(self):
        return theke.uri.build('sword', ['', theke.uri.SWORD_BOOK, self.rawReference])

class InAppReference(Reference):
    def __init__(self, rawReference):
        super().__init__(rawReference)

        logger.debug("Reference − Create a inApp reference : %s", rawReference)

        self.type = theke.TYPE_INAPP
        self.inAppUriData = theke.uri.inAppURI[self.rawReference]
        self.documentTitle = self.inAppUriData.title
        self.documentShortTitle = self.inAppUriData.shortTitle

    def get_uri(self) -> Any:
        return theke.uri.build('theke', [self.rawReference])

class ExternalReference(Reference):
    def __init__(self, uri, title):
        super().__init__(rawReference = repr(uri))

        logger.debug("Reference − Create an external reference : %s", title)

        self.type = theke.TYPE_EXTERNAL
        self.uri = uri
        self.documentTitle = title
        self.documentShortTitle = title

    def get_uri(self) -> Any:
        return self.uri
