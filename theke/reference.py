import theke.uri

def get_standard_reference(rawReference):
    '''Try to standadize a reference.
    If it is biblical reference, return it in a valid OSIS format.

    @param rawReference: raw reference (string)
    @return: standardized reference.
    '''
    return rawReference

class reference():
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
            return theke.uri.build('theke', ['', theke.uri.inAppURI[self.reference]])
        else:
            return theke.uri.build('sword', ['', theke.uri.SWORD_BIBLE, self.reference], {'source': self.source})

