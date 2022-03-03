from gi.repository import GObject

import re
import logging

from typing import Any

import theke
import theke.uri
import theke.index

logger = logging.getLogger(__name__)
index = theke.index.ThekeIndex()

DEFAULT_SWORD_BOOK_SECTION = "Couverture"

class comparison():
    """Byte masks for reference comparison
    """
    NOTHING_IN_COMMON = 0 << 0
    SAME_TYPE = 1 << 0

    # For biblical references comparison...
    BR_SAME_BOOKNAME = 1 << 1
    BR_SAME_CHAPTER = 1 << 2
    BR_SAME_VERSE = 1 << 3

    BR_DIFFERENT_VERSE = SAME_TYPE | BR_SAME_BOOKNAME | BR_SAME_CHAPTER

    # For book references comparison...
    SAME_DOCUMENTNAME = 1 << 1
    SAME_SECTION = 1 << 2

    DIFFER_BY_SECTION = SAME_TYPE | SAME_DOCUMENTNAME

def get_reference_from_uri(uri):
    '''Return a reference according to an uri.
        theke:/app/welcome --> inApp reference to the welcome page
        theke:/doc/bible/John 1:1 --> biblical reference to Jn 1,1
        theke:/doc/book/VeritatisSplendor/1 --> book reference to VS 1

        @param uri: (ThekeUri)
    '''
    if uri.scheme in theke.uri.webpageSchemes:
        return WebpageReference(uri = uri)

    if uri.path[1] == theke.uri.SEGM_APP:
        return InAppReference(uri.path[2], section = uri.fragment)

    if uri.path[1] == theke.uri.SEGM_DOC:
        if uri.path[2] == theke.uri.SEGM_BIBLE:
            return BiblicalReference(uri.path[3])

        if uri.path[2] == theke.uri.SEGM_BOOK:
            if len(uri.path) == 4:
                return BookReference(uri.path[3], section = uri.fragment)

            if uri.fragment:
                return BookReference(uri.path[3], section = "_".join([*uri.path[4:], uri.fragment]))

            return BookReference(uri.path[3], section = "_".join(uri.path[4:]))

        raise ValueError('Unsupported book type: {}.'.format(uri.path[2]))  

def parse_reference(rawReference, wantedSources = None):
    """Parse a raw reference

    @param wantedSources: (set)
    """
    pattern_r = re.compile(r'^(\D+)(.*)')
    match_r = pattern_r.match(rawReference)

    if match_r is not None:
        documentName = match_r.group(1).strip()
        documentType = theke.index.ThekeIndex().get_document_type(documentName)

        if documentType == theke.TYPE_BIBLE:
            return BiblicalReference(rawReference)

        if documentType == theke.TYPE_BOOK:
            if match_r.group(2) != '':
                return BookReference(documentName, section = match_r.group(2))
            
            return BookReference(documentName)

    return Reference(rawReference)

def parse_biblical_reference(rawReference):
    """Extract book name, chapter and verse from a raw reference
    """
    pattern_br_EN = re.compile(r'^([\D]+)(\s(\d+)(:(\d+))?)?$')
    match_br_EN = pattern_br_EN.match(rawReference)

    if match_br_EN is not None:
        if match_br_EN.group(5) is None:
            if match_br_EN.group(2) is None:
                # Book reference: "bookName" redirects to chapter 1
                return match_br_EN.group(1), 1, 0
            # Chapter reference: "bookName chapter"
            return match_br_EN.group(1), int(match_br_EN.group(3)), 0
        else:
            # Verse reference: "bookName chapter:verse"
            return match_br_EN.group(1), int(match_br_EN.group(3)), int(match_br_EN.group(5))

    # This is not a biblical reference
    return None

class Reference():
    '''Reference of any document readable by Theke.
    (application screen, Sword reference)
    '''

    def __init__(self, rawReference):
        self.rawReference = rawReference
        self.documentName = rawReference
        self.documentShortname = rawReference
        self.type = theke.TYPE_UNKNOWN

        self._availableSources = None

    def get_repr(self):
        """Representation of the reference
        eg. long title
        """
        return self.documentName

    def get_short_repr(self):
        """Short representation of the reference
        eg. short title
        """
        return self.documentShortname

    def get_uri(self):
        raise NotImplementedError

    def get_available_sources(self):
        """Get the list of available sources from the index for this reference
        """
        if self._availableSources is None:
            self._availableSources = {s.name: s for s in index.list_document_sources(self.documentName)}

        return self._availableSources

    def __eq__(self, other) -> bool:
        if isinstance(other, Reference):
            return other.get_repr() == self.get_repr()
        elif isinstance(other, str):
            return other == self.get_repr()
        return False
    
    def __and__(self, other) -> int:
        if isinstance(other, Reference):
            if self.type == other.type:
                return comparison.SAME_TYPE
            else:
                return comparison.NOTHING_IN_COMMON
        else:
            return comparison.NOTHING_IN_COMMON

    def __repr__(self) -> str:
        return self.get_repr()

class DocumentReference(Reference):

    def update_data_from_index(self) -> None:
        """Use the ThekeIndex to update this reference metadata
        """
        pass

class BiblicalReference(DocumentReference):
    def __init__(self, rawReference, tags = None):
        """A biblical reference

        @param rawReference: (string)
        @param wantedSources: (set) if possible, use those sources
        @param tags: (list)
        """
        super().__init__(rawReference)

        logger.debug("Reference − Create a biblical reference : %s", rawReference)

        self.type = theke.TYPE_BIBLE
        self.bookName, self.chapter, self.verse = parse_biblical_reference(self.rawReference)
        self.documentName = self.bookName
        self.documentShortname = self.bookName

        self.tags = tags

        self.update_data_from_index()

    def get_repr(self):
        """Return a long representation of the biblical reference
        eg. John 1:1
        """
        if self.verse == 0:
            return "{} {}".format(self.documentName, self.chapter)

        return "{} {}:{}".format(self.documentName, self.chapter, self.verse)

    def get_short_repr(self):
        """Return a short representation of the biblical reference
        (without verse number)
        eg. John 1
        """
        return "{} {}".format(self.documentShortname, self.chapter)

    def get_uri(self):
        if self.verse == 0:
            return theke.uri.build('theke', ['', theke.uri.SEGM_DOC, theke.uri.SEGM_BIBLE,
                "{} {}".format(self.bookName, self.chapter)])
        
        return theke.uri.build('theke', ['', theke.uri.SEGM_DOC, theke.uri.SEGM_BIBLE,
            "{} {}:{}".format(self.bookName, self.chapter, self.verse)])

    def update_data_from_index(self) -> None:
        """Use the ThekeIndex to update this biblical reference metadata
        """
        super().update_data_from_index()

        documentNames = index.get_biblical_book_names(self.bookName)
        self.documentName = documentNames['names'][0]
        self.documentShortname = documentNames['shortnames'][0] if len(documentNames['shortnames']) > 0 else documentNames['names'][0]

    def __and__(self, other) -> int:
        genericComparaison = super().__and__(other)

        if genericComparaison & comparison.SAME_TYPE:
            # This is two biblical references
            return (genericComparaison
                | comparison.BR_SAME_BOOKNAME * (self.bookName == other.bookName)
                | comparison.BR_SAME_CHAPTER * (self.chapter == other.chapter)
                | comparison.BR_SAME_VERSE * (self.verse == other.verse))
        
        else:
            return genericComparaison

class BookReference(DocumentReference):
    def __init__(self, rawReference, section = None):
        super().__init__(rawReference)

        self.type = theke.TYPE_BOOK
        self.documentName = self.rawReference
        self.section = section or ''

        self.update_data_from_index()

    def get_repr(self) -> str:
        if self.section is None or self.section == DEFAULT_SWORD_BOOK_SECTION:
            return "{}".format(self.documentName)

        return "{} {}".format(self.documentName, self.section)

    def get_short_repr(self) -> str:
        if self.section is None or self.section == DEFAULT_SWORD_BOOK_SECTION:
            return "{}".format(self.documentShortname)

        return "{} {}".format(self.documentShortname, self.section)

    def get_uri(self):
        return theke.uri.build('theke', ['', theke.uri.SEGM_DOC, theke.uri.SEGM_BOOK, self.documentName], fragment=self.section)

    def update_data_from_index(self) -> None:
        """Use the ThekeIndex to update this reference metadata
        """
        super().update_data_from_index()

        documentNames = index.get_document_names(self.documentName)
        self.documentName = documentNames['names'][0]
        self.documentShortname = documentNames['shortnames'][0] if len(documentNames['shortnames']) > 0 else documentNames['names'][0]

    def __and__(self, other) -> int:
        genericComparaison = super().__and__(other)

        if genericComparaison & comparison.SAME_TYPE:
            # This is two book references
            return (genericComparaison
                | comparison.SAME_DOCUMENTNAME * (self.documentName == other.documentName)
                | comparison.SAME_SECTION * (self.section == other.section))
        
        else:
            return genericComparaison

class InAppReference(Reference):
    def __init__(self, rawReference, section = None):
        super().__init__(rawReference)

        logger.debug("Reference − Create a inApp reference : %s", rawReference)

        self.type = theke.TYPE_INAPP
        self.section = section or ''
        
        self.inAppUriData = theke.uri.inAppURI[self.rawReference]
        self.documentName = self.inAppUriData.title
        self.documentShortname = self.inAppUriData.shortTitle

    def get_uri(self) -> Any:
        return theke.uri.build('theke', ['', theke.uri.SEGM_APP, self.rawReference], fragment=self.section)

class WebpageReference(Reference):
    def __init__(self, title = "???", section = None, uri = None):
        super().__init__(rawReference = title)

        logger.debug("Reference − Create an external reference : %s", title)

        self.type = theke.TYPE_WEBPAGE
        self.set_title(title)

        self.section = section or uri.fragment
        self.uri = uri

    def set_title(self, title) -> None:
        self.documentName = title

        if len(title) > 20:
            self.documentShortname = "{}...".format(title[:17])
        else:
            self.documentShortname = title

    def get_repr(self) -> str:
        if self.section is None:
            return "{}".format(self.documentName)

        return "{} {}".format(self.documentName, self.section)

    def get_short_repr(self) -> str:
        if self.section is None:
            return "{}".format(self.documentShortname)

        return "{} {}".format(self.documentShortname, self.section)

    def get_uri(self) -> Any:
        return self.uri
