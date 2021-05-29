import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

import theke.morphology


class ThekeMorphoView(Gtk.Frame):
    def __init__(self, builder, *args, **kwargs):
        super().__init__(*args, margin_left=10, margin_right=10, **kwargs)

        self.word_label = builder.get_object("morphoView_word")
        self.lemma_box = builder.get_object("morphoView_lemma")
        self.lemma_label = builder.get_object("morphoView_lemmaText")
        self.strong_label = builder.get_object("morphoView_strongText")
        self.search_button = builder.get_object("morphoView_searchButton")

        # #####
        # TODO: Déplacer tout ce qui suit dans le fichier glade
        self.set_label("Morphologie")
        self.set_label_align(0.02, 0.5)

        hbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_start=10, margin_bottom=5)
        hbox.set_homogeneous(False)

        self.label_morph_raw = Gtk.Label(label="-", xalign=0)
        self.label_morph_raw.set_selectable(True)
        hbox.pack_start(self.label_morph_raw, False, False, 0)

        self.label_morph_parsed = Gtk.Label(xalign=0, margin_left=10)
        hbox.pack_start(self.label_morph_parsed, False, False, 0)

        self.add(hbox)
        self.show_all()
        # #####

    def set_morph(self, word, morph):
        analysis = theke.morphology.parse(morph)

        self.word_label.set_label(word)

        if analysis:
            self.label_morph_raw.set_label(morph)
            self.label_morph_parsed.set_label(' / '.join(analysis))
        else:
            self.label_morph_raw.set_label("-")
            self.label_morph_parsed.set_label('')
    
    def set_lemma(self, lemma):
        if lemma:
            self.lemma_label.set_label(lemma)
            self.lemma_label.show()
        else:
            self.lemma_label.hide()

    def set_strongs(self, strongs):
        if strongs:
            self.strong_label.set_label(strongs)
            self.search_button.set_sensitive(True)
            self.strong_label.show()
        else:
            self.search_button.set_sensitive(False)
            self.strong_label.hide()

    def search_button_connect(self, callback):
        self.search_button.connect("clicked", callback)