import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

import theke.morphology


class ThekeMorphoView(Gtk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, margin_left=10, margin_right=10, **kwargs)

        self.set_label("Morphologie")
        self.set_label_align(0.02, 0.5)

        hbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_start=10, margin_bottom=5)
        hbox.set_homogeneous(False)

        self.label_morph_raw = Gtk.Label(label="-", xalign=0)
        hbox.pack_start(self.label_morph_raw, False, False, 0)

        self.label_morph_parsed = Gtk.Label(xalign=0, margin_left=10)
        hbox.pack_start(self.label_morph_parsed, False, False, 0)

        self.add(hbox)

    def set_morph(self, morph):
        analysis = theke.morphology.parse(morph)

        if analysis:
            self.label_morph_raw.set_label(morph)
            self.label_morph_parsed.set_label(analysis)
        else:
            self.label_morph_raw.set_label("-")
            self.label_morph_parsed.set_label('')