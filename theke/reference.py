import re
import logging

from typing import Any

import theke
import theke.uri
import theke.index

logger = logging.getLogger(__name__)
index = theke.index.ThekeIndex()

DEFAULT_SWORD_BOOK_SECTION = "Couverture"

def get_reference_from_uri(uri):
    '''Return a reference according to an uri.
        theke:/app/welcome --> inApp reference to the welcome page
        theke:/doc/bible/John 1:1 --> biblical reference to Jn 1,1
        theke:/doc/book/VeritatisSplendor/1 --> book reference to VS 1

        @param uri: (ThekeUri)
    '''
    if uri.path[1] == theke.uri.SEGM_APP:
        return InAppReference(uri.path[2])

    if uri.path[1] == theke.uri.SEGM_DOC:
        if uri.path[2] == theke.uri.SEGM_BIBLE:
            wantedSources  = uri.params.get('sources', None)

            if wantedSources is None:
                return BiblicalReference(uri.path[3])
            
            return BiblicalReference(uri.path[3], wantedSources = set(wantedSources.split(';')))

        if uri.path[2] == theke.uri.SEGM_BOOK:
            if len(uri.path) == 4:
                return BookReference(uri.path[3], section = DEFAULT_SWORD_BOOK_SECTION)

            return BookReference(uri.path[3], section = uri.path[4])

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
            return BiblicalReference(rawReference, wantedSources)

        if documentType == theke.TYPE_BOOK:
            if match_r.group(2) != '':
                return BookReference(documentName, section = match_r.group(2))
            
            return BookReference(documentName)

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
        self.documentName = rawReference
        self.documentShortname = rawReference
        self.type = theke.TYPE_UNKNOWN

        self.sources = None
        self.availableSources = None
        self.defaultSource = None

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

    def get_sources(self):
        """List of sources designated by the reference
        """
        return self.sources if self.sources is not None else [self.defaultSource]

    def get_uri(self):
        raise NotImplementedError

class DocumentReference(Reference):
    def update_default_source(self) -> None:
        """Update the default source of a reference
        """
        # TOFIX: la source par défaut serait à choisir depuis l'index
        self.defaultSource = next(iter(self.availableSources))

    def update_data_from_index(self) -> None:
        """Use the ThekeIndex to update this reference metadata
        """
        self.availableSources = set(index.list_document_sources(self.documentName))

class BiblicalReference(DocumentReference):
    def __init__(self, rawReference, wantedSources = None, tags = None):
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
        self.update_default_source()

        if wantedSources is not None:
            self.sources = self.availableSources & wantedSources
            if len(self.sources) == 0:
                self.sources = {self.defaultSource}

        else:
            self.sources = {self.defaultSource}

    def add_source(self, source) -> bool:
        """Append a source to the reference
        Return True if the source was added
        """

        if source not in self.availableSources:
            logger.debug("ThekeReference − This document is not available in this source: %s", source)
            return False

        if source not in self.sources:
            logger.debug("ThekeReference − Add source %s", source)
            self.sources.add(source)
            return True

        return False

    def remove_source(self, source) -> bool:
        """Remove a source
        As self.sources can not be empty, a default source shoud be given
        """
        if source not in self.sources:
            return False

        logger.debug("ThekeReference - Remove source %s", source)
        self.sources.discard(source)

        if len(self.sources) == 0:
            logger.debug("ThekeReference - Set source to default %s", self.defaultSource)
            self.sources.add(self.defaultSource)

        return True

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
                "{} {}".format(self.bookName, self.chapter)],
                sources = self.sources)
        
        return theke.uri.build('theke', ['', theke.uri.SEGM_DOC, theke.uri.SEGM_BIBLE,
            "{} {}:{}".format(self.bookName, self.chapter, self.verse)],
            sources = self.sources)

    def update_data_from_index(self) -> None:
        """Use the ThekeIndex to update this biblical reference metadata
        """
        super().update_data_from_index()

        documentNames = index.get_biblical_book_names(self.bookName)
        self.documentName = documentNames['names'][0]
        self.documentShortname = documentNames['shortnames'][0] if len(documentNames['shortnames']) > 0 else documentNames['names'][0]

class BookReference(DocumentReference):
    def __init__(self, rawReference, rawSources = None, section = None):
        super().__init__(rawReference)

        self.type = theke.TYPE_BOOK
        self.documentName = self.rawReference
        self.section = section

        self.update_data_from_index()
        self.update_default_source()
        self.sources = rawSources.split(';') if rawSources is not None else [self.defaultSource]

    def get_repr(self) -> str:
        if self.section is None or self.section == DEFAULT_SWORD_BOOK_SECTION:
            return "{}".format(self.documentName)

        return "{} {}".format(self.documentName, self.section)

    def get_short_repr(self) -> str:
        if self.section is None or self.section == DEFAULT_SWORD_BOOK_SECTION:
            return "{}".format(self.documentShortname)

        return "{} {}".format(self.documentShortname, self.section)

    def get_uri(self):
        if self.section is None or self.section == DEFAULT_SWORD_BOOK_SECTION:
            return theke.uri.build('theke', ['', theke.uri.SEGM_DOC, theke.uri.SEGM_BOOK, self.documentName])

        return theke.uri.build('theke', ['', theke.uri.SEGM_DOC, theke.uri.SEGM_BOOK, self.documentName, str(self.section)])

    def update_data_from_index(self) -> None:
        """Use the ThekeIndex to update this reference metadata
        """
        super().update_data_from_index()

        documentNames = index.get_document_names(self.documentName)
        self.documentName = documentNames['names'][0]
        self.documentShortname = documentNames['shortnames'][0] if len(documentNames['shortnames']) > 0 else documentNames['names'][0]

class InAppReference(Reference):
    def __init__(self, rawReference):
        super().__init__(rawReference)

        logger.debug("Reference − Create a inApp reference : %s", rawReference)

        self.type = theke.TYPE_INAPP
        self.inAppUriData = theke.uri.inAppURI[self.rawReference]
        self.documentName = self.inAppUriData.title
        self.documentShortname = self.inAppUriData.shortTitle

    def get_uri(self) -> Any:
        return theke.uri.build('theke', ['', theke.uri.SEGM_APP, self.rawReference])

class WebpageReference(Reference):
    def __init__(self, title, section = None, uri = None):
        super().__init__(rawReference = title)

        logger.debug("Reference − Create an external reference : %s", title)

        self.type = theke.TYPE_WEBPAGE
        self.documentName = title
        if len(title) > 20:
            self.documentShortname = "{}...".format(title[:17])
        else:
            self.documentShortname = title
        self.section = section
        self.uri = uri

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
