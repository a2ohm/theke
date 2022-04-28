import urllib.parse
from collections import namedtuple

webpageSchemes = ['http', 'https']
validSchemes = ['theke', 'http', 'https']

inAppUriData = namedtuple('inAppUriData',['title','shortTitle','fileName'])

inAppURI = {
    'about' : inAppUriData('À propos de Theke', 'À propos', 'about.html'),
    'external_documents' : inAppUriData('Liste des documents externes', 'Documents externes', 'external_documents.html'),
    'help' : inAppUriData('Aide', 'Aide', 'help.html'),
    'logbook' : inAppUriData('Carnet de bord', 'Carnet de bord', 'logbook.html'),
    'modules' : inAppUriData('Liste des modules installés', 'Modules', 'modules.html'),
    'test' : inAppUriData('⚠️ Zone de test ⚠️', 'Test', 'test.html'),
    'welcome': inAppUriData('Bienvenue !', 'Accueil', 'welcome.html'),
}

# Uri segments
SEGM_APP = 'app'
SEGM_DOC = 'doc'

SEGM_ASSETS = 'assets'

SEGM_BIBLE = 'bible'
SEGM_BOOK = 'book'

SEGM_SIGNAL = 'signal'

class comparison():
    """Byte masks for uri comparison
    """
    NOTHING_IN_COMMON = 0 << 0

    SAME_SCHEME = 1 << 4
    SAME_NETLOCK = 1 << 3
    SAME_PATH = 1 << 2
    SAME_PARAMS = 1 << 1
    SAME_FRAGMENT = 1 << 0

    SAME_URI = SAME_SCHEME | SAME_NETLOCK | SAME_PATH | SAME_PARAMS | SAME_FRAGMENT

    # Some mask
    DIFFER_BY_FRAGMENT = SAME_SCHEME | SAME_NETLOCK | SAME_PATH | SAME_PARAMS

def build(scheme, path, params = None, fragment='', sources = None):
    """Build an uri from seperate elements.

    @param scheme: (str) eg. 'sword', 'theke'
    @param path: (list) eg. ['/', 'bible', 'John 1:1']
    @param params: (dict)
    @param fragment
    @param sources: (list) eg. ['MorphGNT', 'FreCrampon']

    Sources are added to params.
    """

    if params is None:
        params = {}

    if sources is not None:
        params.update({'sources': ";".join(sources)})

    return ThekeURI(scheme, '', path, params, fragment)

def parse(uri):
    '''Parse an uri and return a ThekeURI instance.

    Valids uri are (for example):
        theke:/app/welcome
        theke:/app/assets/css/default.css
        theke:/doc/bible/John 1:1?sources=MorphGNT
    '''

    # Parse the uri
    #  /!\ ignore parameters for last path element
    scheme, netlock, path, _, query, fragment = urllib.parse.urlparse(uri)

    # Params are queries parsed into a dict
    #   source=MorphGNT&foo=bar --> {'source': 'MorphGNT', 'foo': 'bar'}
    params = {}
    for q in query.split('&'):
        if len(q) > 0:
            name, value = q.split('=')
            params[name] = urllib.parse.unquote(value)
    
    # Store everything without %xx escape equivalent
    path = urllib.parse.unquote(path)
    fragment = urllib.parse.unquote(fragment)

    # /!\ If the path begins with a '/', the first element of path is an empty string
    #   /bible/John 1:1 --> ['', 'bible', 'John 1:1']
    path = path.split('/')

    return ThekeURI(scheme, netlock, path, params, fragment)

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
    def __init__(self, scheme, netlock, path, params, fragment):
        self.scheme = scheme
        self.netlock = netlock
        self.path = path
        self.params =  params
        self.fragment = fragment

        if self.scheme not in validSchemes:
            raise ValueError("Unsupported ThekeURI ({})".format(self.scheme))

    def get_decoded_URI(self):
        return urllib.parse.urlunparse(
            (self.scheme, self.netlock,
            unparse_path(self.path, quote=False), '',
            unparse_params(self.params, quote=False),
            urllib.parse.unquote(self.fragment))
        )

    def get_encoded_URI(self):
        return urllib.parse.urlunparse(
            (self.scheme, self.netlock,
            unparse_path(self.path, quote=True), '',
            unparse_params(self.params, quote=True),
            self.fragment)
        )

    def __repr__(self):
        return self.get_decoded_URI()

    def __and__(self, other) -> int:
        if isinstance(other, ThekeURI):
            # This is two ThekeUri
            return (comparison.SAME_SCHEME * (self.scheme == other.scheme)
                | comparison.SAME_NETLOCK * (self.netlock == other.netlock)
                | comparison.SAME_PATH * (self.path == other.path)
                | comparison.SAME_PARAMS * (self.params == other.params)
                | comparison.SAME_FRAGMENT * (self.fragment == other.fragment))

        elif isinstance(other, str) and other == self.get_encoded_URI():
            return comparison.SAME_URI

        else:
            return comparison.NOTHING_IN_COMMON
    
    def __eq__(self, other):
        if isinstance(other, ThekeURI):
            if other.get_encoded_URI() == self.get_encoded_URI():
                return True
        elif isinstance(other, str):
            if other == self.get_encoded_URI():
                return True
        return False

if __name__ == "__main__":
    uri1 = parse("theke:/doc/bible/John 1:1?source=MorphGNT")
    print(uri1.get_decoded_URI())
    print(uri1.get_encoded_URI())

    uri2 = parse("theke:/doc/pomme/poire/abricot/welcome.html")
    print(uri2.get_decoded_URI())
    print(uri2.get_encoded_URI())

    uri3 = parse("theke:/doc/bible/John%201%3A1?source=MorphGNT")
    print(uri3.get_decoded_URI())
    print(uri3.get_encoded_URI())
