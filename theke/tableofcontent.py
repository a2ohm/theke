import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

# from collections import namedtuple
# tocFields = namedtuple('tocFields',['name','rawUri'])

class ThekeTOC():
    def __init__(self):
        self.toc = Gtk.ListStore(str, str)

    def append(self, name, rawUri):
        self.toc.append((name, rawUri))