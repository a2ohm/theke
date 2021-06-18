import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

from theke.gui.widget_ThekeMorphoView import ThekeMorphoView
from theke.gui.widget_ThekeDicoView import ThekeDicoView

class ThekeToolsView():
    """In the main window, the ToolsView gathers:
        - the MorphoView
    """
    def __init__(self, builder) -> None:
        self.toolViewBox = builder.get_object("toolsView_Box")
        self.toolView_tools = builder.get_object("toolsView_tools")
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

        # dicoView
        self.dicoView = ThekeDicoView(builder)

        self.reduceExpand_button.connect("clicked", self.handle_reduceExpand_button_clicked)

    def search_button_connect(self, callback):
        self.search_button.connect("clicked", callback)

    def set_lemma(self, lemma):
        if lemma:
            self.lemma_label.set_label(lemma)
            self.lemma_box.show()
        else:
            self.lemma_box.hide()

    def set_morph(self, word, morph):
        self.word_label.set_label(word)
        self.morphView.set_morph(word, morph)

    def set_strongs(self, strongs):
        if strongs:
            self.strong_label.set_label(strongs)
            self.search_button.set_sensitive(True)
            self.strong_label.show()

            self.dicoView.load_entry_by_strongs(strongs)
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
        self.toolView_tools.hide()
        self.reduceExpand_image.set_from_icon_name("go-up-symbolic", Gtk.IconSize.BUTTON)
    
    def expand(self):
        self.isReduce = False
        self.toolView_tools.show()
        self.reduceExpand_image.set_from_icon_name("go-down-symbolic", Gtk.IconSize.BUTTON)

    def handle_reduceExpand_button_clicked(self, button):
        if self.isReduce:
            self.expand()
        else:
            self.reduce()