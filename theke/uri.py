import urllib.parse
from collections import namedtuple

validSchemes = ['theke', 'sword']

inAppUriData = namedtuple('inAppUriData',['title','shortTitle','fileName'])

inAppURI = {
    'welcome': inAppUriData('Bienvenue !', 'Accueil', 'welcome.html'),
    'about' : inAppUriData('À propos de Theke', 'À propos', 'about.html'),
}

SWORD_BIBLE = 'bible'
SWORD_BOOK = 'book'

SWORD_SIGNAL = 'signal'

def build(scheme, path, params = {}, fragment=''):
    return ThekeURI(scheme, path, params, fragment)

def parse(uri, isEncoded = True):
    '''Parse an uri and return a ThekeURI instance.

    Valids uri are (for example):
        sword:/bible/John 1:1?source=MorphGNT
        theke:welcome
        theke:/default.css
    '''

    # Parse the uri
    #  /!\ ignore netlock and parameters for last path element
    scheme, _, path, _, query, fragment = urllib.parse.urlparse(uri)

    # Params are queries parsed into a dict
    #   source=MorphGNT&foo=bar --> {'source': 'MorphGNT', 'foo': 'bar'}
    params = {}
    for q in query.split('&'):
        if len(q) > 0:
            name, value = q.split('=')
            params[name] = urllib.parse.unquote(value) if isEncoded else value
    
    # Store everything uncoded
    if isEncoded:
        path = urllib.parse.unquote(path)
        fragment = urllib.parse.unquote(fragment)

    # /!\ If the path begins with a '/', the first element of path is an empty string
    #   /bible/John 1:1 --> ['', 'bible', 'John 1:1']
    path = path.split('/')

    return ThekeURI(scheme, path, params, fragment)

def unparse_params(params, quote = True):
    '''Unparse a params list into a string.
        {'source': 'MorphGNT', 'foo': 'bar'} --> 'source=MorphGNT&foo=bar'
    '''
    if quote:
        return '&'.join([name + '=' + urllib.parse.quote(value) for name, value in params.items()])
    else:
        return '&'.join([name + '=' + value for name, value in params.items()])

def unparse_path(path, quote = False):
    '''Unparse a path list into a string.
        ['', 'bible', 'John 1:1'] --> '/bible/John 1:1'
    '''
    if quote:
        return '/'.join(urllib.parse.quote(p) for p in path)
    else:
        return '/'.join(path)

class ThekeURI:
    def __init__(self, scheme, path, params, fragment, isEncoded = True):
        self.scheme = scheme
        self.path = path
        self.params =  params
        self.fragment = fragment

        if self.scheme not in validSchemes:
            raise ValueError("Unsupported ThekeURI ({})".format(self.scheme))

    def get_decoded_URI(self):
        return urllib.parse.urlunparse(
            (self.scheme, '',
            unparse_path(self.path, quote=False), '',
            unparse_params(self.params, quote=False),
            urllib.parse.unquote(self.fragment))
        )

    def get_encoded_URI(self):
        return urllib.parse.urlunparse(
            (self.scheme, '',
            unparse_path(self.path, quote=True), '',
            unparse_params(self.params, quote=True),
            self.fragment)
        )

    def __repr__(self):
        return self.get_decoded_URI()

    def __eq__(self, other):
        if isinstance(other, ThekeURI):
            if other.get_encoded_URI() == self.get_encoded_URI():
                return True
        elif isinstance(other, str):
            if other == self.get_encoded_URI():
                return True
        return False


if __name__ == "__main__":
    uri1 = parse("sword:bible/John 1:1?source=MorphGNT")
    print(uri1.get_decoded_URI())
    print(uri1.get_encoded_URI())

    uri2 = parse("theke:pomme/poire/abricot/welcome.html")
    print(uri2.get_decoded_URI())
    print(uri2.get_encoded_URI())

    uri3 = parse("sword:bible/John%201%3A1?source=MorphGNT", isEncoded=True)
    print(uri3.get_decoded_URI())
    print(uri3.get_encoded_URI())