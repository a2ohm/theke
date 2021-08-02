import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

import theke.uri
import theke.index

# from collections import namedtuple
# tocFields = namedtuple('tocFields',['name','rawUri'])

def get_toc_from_ref(ref):
    #TODO:  /!\ Suppose que la référence est une référence biblique.
    #       Cette fonction devra être adaptée aux livres non bibliques.

    thekeIndex = theke.index.ThekeIndex()
    nbOfChapters = thekeIndex.get_document_nbOfSections(ref.documentName)

    toc = theke.tableofcontent.ThekeTOC()

    for i in range(nbOfChapters):
        uri = theke.uri.build('sword', ['', theke.uri.SWORD_BIBLE, '{} {}'.format(ref.documentName, i+1)], sources = ref.sources)
        toc.append(str(i+1), uri.get_encoded_URI())

    return toc

class ThekeTOC():
    def __init__(self):
        self.toc = Gtk.ListStore(str, str)

    def append(self, name, rawUri):
        self.toc.append((name, rawUri))