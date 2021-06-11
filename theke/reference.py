import theke.uri
import re

def get_reference_from_uri(uri, defaultSource = None):
    '''Return a reference according to an uri.
        sword:/bible/John 1:1 --> biblical reference to Jn 1,1

        @param uri: (ThekeUri)
    '''
    if uri.scheme != 'sword':
        raise ValueError('Unsupported scheme: {}.'.format(uri.scheme))

    if uri.path[1] != 'bible':
        raise ValueError('Unsupported book type: {}.'.format(uri.path[1]))

    return BiblicalReference(uri.path[2], source = uri.params.get('source', defaultSource))

def get_standard_reference(rawReference):
    '''Try to standadize a reference.
    If it is biblical reference, return it in a valid OSIS format.

    @param rawReference: raw reference (string)
    @return: standardized reference.
    '''
    return rawReference

def parse_biblical_reference(reference):
    pattern_br_EN = re.compile(r'^([\w\s]+) (\d+)(:(\d+))?$')
    match_br_EN = pattern_br_EN.match(reference)

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

    def __init__(self, rawReference, **kwargs):
        self.reference = get_standard_reference(rawReference)
        self.source = kwargs.get('source', None)
        self.tags = kwargs.get('tags', [])

    def get_uri(self):
        if self.source is None:
            return theke.uri.build('sword', ['', theke.uri.SWORD_BIBLE, self.reference])
        elif self.source == 'Theke':
            return theke.uri.build('theke', [self.reference])
        else:
            return theke.uri.build('sword', ['', theke.uri.SWORD_BIBLE, self.reference], {'source': self.source})

    def get_repr(self):
        return self.reference

    def get_short_repr(self):
        return self.reference

class BiblicalReference(Reference):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bookName, self.chapter, self.verse = parse_biblical_reference(self.reference)

    def get_repr(self):
        if self.verse == 0:
            return "{} {}".format(self.bookName, self.chapter)
        else:
            return "{} {}:{}".format(self.bookName, self.chapter, self.verse)

    def get_short_repr(self):
        return "{} {}".format(self.bookName, self.chapter)