import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk


class ThekeMorphoView(Gtk.Box):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

        hbox = Gtk.Box()
        hbox.set_homogeneous(False)
        
        label = Gtk.Label(label="Morphologie : ")
        hbox.pack_start(label, False, True, 1)

        self.label_morph_val = Gtk.Label(label="")
        hbox.pack_start(self.label_morph_val, False, True, 0)

        self.pack_start(hbox, True, True, 0)