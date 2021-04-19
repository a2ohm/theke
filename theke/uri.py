import re
import urllib.parse

from urllib.parse import unquote, quote

validSchemes = ['theke', 'sword']

inAppURI = {
    'Bienvenue': 'welcome.html',
    'À propos': 'about.html'
}

def parse(uri, isEncoded = True):
    scheme, _, path, _, query, fragment = urllib.parse.urlparse(uri)

    if scheme not in validSchemes:
        raise ValueError("Unsupported ThekeURI ({})".format(scheme))

    params = {}
    for q in query.split('&'):
        if len(q) > 0:
            name, value = q.split('=')
            params[name] = urllib.parse.unquote(value) if isEncoded else value
    
    if isEncoded:
        path = urllib.parse.unquote(path)
        fragment = urllib.parse.unquote(fragment)

    return ThekeURI(scheme, path.split('/'), params, fragment)

def build(scheme, path, params = {}, fragment=''):
    return ThekeURI(scheme, path, params, fragment)

class ThekeURI:
    def __init__(self, scheme, path, params, fragment, isEncoded = True):
        self.scheme = scheme
        self.path = path
        self.params =  params
        self.fragment = fragment

        if self.scheme not in validSchemes:
            raise ValueError("Unsupported ThekeURI ({})".format(self.scheme))

    def unparse_params(self, params, quote = True):
        if quote:
            return '&'.join([name + '=' + urllib.parse.quote(value) for name, value in params.items()])
        else:
            return '&'.join([name + '=' + value for name, value in params.items()])

    def unparse_path(self, path, quote = False):
        if quote:
            return '/'.join(urllib.parse.quote(p) for p in path)
        else:
            return '/'.join(path)

    def get_decoded_URI(self):
        return urllib.parse.urlunparse(
            (self.scheme, '',
            self.unparse_path(self.path, quote=True), '',
            self.unparse_params(self.params, quote=True),
            urllib.parse.unquote(self.fragment))
        )

    def get_coded_URI(self):
        return urllib.parse.urlunparse(
            (self.scheme, '',
            self.unparse_path(self.path, quote=False), '',
            self.unparse_params(self.params, quote=False),
            self.fragment)
        )

    def __repr__(self):
        return self.get_decoded_URI()


if __name__ == "__main__":
    uri1 = parse("sword:bible/John 1:1?source=MorphGNT")
    print(uri1.get_decoded_URI())
    print(uri1.get_coded_URI())

    uri2 = parse("theke:pomme/poire/abricot/welcome.html")
    print(uri2.get_decoded_URI())
    print(uri2.get_coded_URI())

    uri3 = parse("sword:bible/John%201%3A1?source=MorphGNT", isEncoded=True)
    print(uri3.get_decoded_URI())
    print(uri3.get_coded_URI())