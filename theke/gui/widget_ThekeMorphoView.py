from gi.repository import Gtk

import theke.morphology

@Gtk.Template.from_file('./theke/gui/templates/ThekeMorphoView.glade')
class ThekeMorphoView(Gtk.Bin):
    __gtype_name__ = "ThekeMorphoView"

    _rawMorph_label = Gtk.Template.Child()
    _parsedMorph_label = Gtk.Template.Child()

    def set_morph(self, word, morph):
        analysis = theke.morphology.parse(morph)

        if analysis:
            self._rawMorph_label.set_label(morph)
            self._parsedMorph_label.set_label(' / '.join(analysis))
        else:
            self._rawMorph_label.set_label("-")
            self._parsedMorph_label.set_label('')
