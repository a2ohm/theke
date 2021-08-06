import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

import theke.uri
import theke.index

# from collections import namedtuple
# tocFields = namedtuple('tocFields',['name','rawUri'])

BIBLE_TOC_TYPE = 1

def get_toc_BIBLE(ref):
    #TODO:  /!\ Suppose que la référence est une référence biblique.
    #       Cette fonction devra être adaptée aux livres non bibliques.

    thekeIndex = theke.index.ThekeIndex()
    nbOfChapters = thekeIndex.get_document_nbOfSections(ref.documentTitle)

    toc = ThekeTOC(type_of_toc = BIBLE_TOC_TYPE)

    for i in range(1, nbOfChapters + 1):
        #uri = theke.uri.build('sword', ['', theke.uri.SWORD_BIBLE, '{} {}'.format(ref.documentTitle, i+1)], sources = ref.sources)
        #toc.append(str(i+1), uri.get_encoded_URI())
        toc.append(str(i), i)

    return toc

class ThekeTOC():
    def __init__(self, type_of_toc = 0) -> None:
        if type_of_toc == BIBLE_TOC_TYPE:
            self.toc = Gtk.ListStore(str, int)
        else:
            raise("Unknown type of TOC")

        self.type = type_of_toc

    def append(self, label, data) -> None:
        """Append an entry to the table of content
        
        @param label: name of the entry
        @param data: data needed to jump to this entry (section number, uri, ...)
        """
        self.toc.append((label, data))