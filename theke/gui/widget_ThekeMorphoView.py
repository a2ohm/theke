from gi.repository import Gtk

import theke.morphology


class ThekeMorphoView():
    def __init__(self, builder):
        self.morphoView_frame = builder.get_object("morphoView_frame")
        self.label_morph_raw = builder.get_object("morphoView_rawMorph")
        self.label_morph_parsed = builder.get_object("morphoView_parsedMorph")

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