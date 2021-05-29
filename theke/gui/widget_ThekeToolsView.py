import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

from theke.gui.widget_ThekeMorphoView import ThekeMorphoView

class ThekeToolsView():
    """In the main window, the ToolsView gathers:
        - the MorphoView
    """
    def __init__(self, builder) -> None:
        self.toolViewBox = builder.get_object("toolsViewBox")
        self.reduceExpand_button = builder.get_object("toolsView_reduceExpand_button")
        self.reduceExpand_image = builder.get_object("toolsView_reduceExpand_image")

        self.word_label = builder.get_object("toolsView_word")
        self.lemma_box = builder.get_object("toolsView_lemma")
        self.lemma_label = builder.get_object("toolsView_lemmaText")
        self.strong_label = builder.get_object("toolsView_strongText")
        self.search_button = builder.get_object("toolsView_searchButton")

        self.isReduce = False
        
        # MorphoView
        self.morphView = ThekeMorphoView(builder)

        self.reduceExpand_button.connect("clicked", self.handle_reduceExpand_button_clicked)

    def search_button_connect(self, callback):
        self.search_button.connect("clicked", callback)

    def set_lemma(self, lemma):
        if lemma:
            self.lemma_label.set_label(lemma)
            self.lemma_label.show()
        else:
            self.lemma_label.hide()

    def set_morph(self, word, morph):
        self.word_label.set_label(word)
        self.morphView.set_morph(word, morph)

    def set_strongs(self, strongs):
        if strongs:
            self.strong_label.set_label(strongs)
            self.search_button.set_sensitive(True)
            self.strong_label.show()
        else:
            self.search_button.set_sensitive(False)
            self.strong_label.hide()

    def hide(self):
        self.toolViewBox.hide()

    def show(self):
        self.toolViewBox.show()
        if self.isReduce:
            self.expand()

    def reduce(self):
        self.isReduce = True
        self.morphView.hide()
        self.reduceExpand_image.set_from_icon_name("go-up-symbolic", Gtk.IconSize.BUTTON)
    
    def expand(self):
        self.isReduce = False
        self.morphView.show()
        self.reduceExpand_image.set_from_icon_name("go-down-symbolic", Gtk.IconSize.BUTTON)

    def handle_reduceExpand_button_clicked(self, button):
        if self.isReduce:
            self.expand()
        else:
            self.reduce()