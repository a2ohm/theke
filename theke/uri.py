import re
from urllib.parse import unquote, quote

class ThekeURI:
    def __init__(self, URI, isRaw = False):
        if isRaw:
            self.prefix, self.path, self.params = self.parse_URI(unquote(URI))
        else:
            self.prefix, self.path, self.params = self.parse_URI(URI)

        validPrefix = ['theke:///', 'sword:///', 'file:///']

        if self.prefix not in validPrefix:
            raise ValueError("Unsupported ThekeURI ({})".format(self.prefix))

    def parse_URI(self, URI):
        """Parse the URI.
        @return: prefix, path, parameters
        """
        reURI = re.compile(r"^(\w+:\/\/\/)([^\?]+)(\?(.+))?$")
        m = reURI.match(URI)

        if m:
            if m.group(3) is not None:
                # Parse parameters in a dict (m.group(4))
                params = {}
                for p in m.group(4).split('&'):
                    name, value = p.split('=')
                    params[name] = value
                return m.group(1), m.group(2).split('/'), params

            else:
                return m.group(1), m.group(2).split('/'), {}
        else:
            raise ValueError("Invalid ThekeURI ({})".format(URI))

    def get_decoded_URI(self):
        if len(self.params) > 0:
            return self.prefix + '/'.join(self.path) + '?' + '&'.join([name + '=' + value for name, value in self.params.items()])
        else:
            return self.prefix + '/'.join(self.path)

    def get_coded_URI(self):
        if len(self.params) > 0:
            return self.prefix + quote('/'.join(self.path)) + '?' + '&'.join([name + '=' + quote(value) for name, value in self.params.items()])
        else:
            return self.prefix + quote('/'.join(self.path))

    def __repr__(self):
        return self.get_decoded_URI()


if __name__ == "__main__":
    uri1 = ThekeURI("sword:///bible/John 1:1?source=MorphGNT")
    print(uri1.get_decoded_URI())
    print(uri1.get_coded_URI())

    uri2 = ThekeURI("theke:///pomme/poire/abricot/welcome.html")
    print(uri2.get_decoded_URI())
    print(uri2.get_coded_URI())

    uri3 = ThekeURI("sword:///bible/John%201%3A1?source=MorphGNT", isRaw=True)
    print(uri3.get_decoded_URI())
    print(uri3.get_coded_URI())