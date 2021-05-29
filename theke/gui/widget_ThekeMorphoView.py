import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

import theke.morphology


class ThekeMorphoView():
    def __init__(self, builder):
        self.morphoView_frame = builder.get_object("morphoView_frame")

        # #####
        # TODO: Déplacer tout ce qui suit dans le fichier glade
        hbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_start=10, margin_bottom=5)
        hbox.set_homogeneous(False)

        self.label_morph_raw = Gtk.Label(label="-", xalign=0)
        self.label_morph_raw.set_selectable(True)
        hbox.pack_start(self.label_morph_raw, False, False, 0)

        self.label_morph_parsed = Gtk.Label(xalign=0, margin_left=10)
        hbox.pack_start(self.label_morph_parsed, False, False, 0)

        self.morphoView_frame.add(hbox)
        self.morphoView_frame.show_all()
        # #####

    def set_morph(self, word, morph):
        analysis = theke.morphology.parse(morph)

        if analysis:
            self.label_morph_raw.set_label(morph)
            self.label_morph_parsed.set_label(' / '.join(analysis))
        else:
            self.label_morph_raw.set_label("-")
            self.label_morph_parsed.set_label('')

    def hide(self):
        self.morphoView_frame.hide()

    def show(self):
        self.morphoView_frame.show()