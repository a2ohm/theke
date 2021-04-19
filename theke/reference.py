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
        # TODO: Ce serait mieux de pouvoir utiliser ThekeURI pour construire proprement une URI
        #       plutot que de la construire ici et de la décomposer dans ThekeURI.

        if self.source is None:
            return theke.uri.parse('sword:/bible/{}'.format(self.reference), isEncoded=False)
        else:
            return theke.uri.parse('sword:/bible/{}?source={}'.format(self.reference, self.source), isEncoded=False)

