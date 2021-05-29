from theke.gui.widget_ThekeMorphoView import ThekeMorphoView

class ThekeToolsView():
    """In the main window, the ToolsView gathers:
        - the MorphoView
    """
    def __init__(self, builder) -> None:
        self.toolViewBox = builder.get_object("toolsViewBox")
        
        # MorphoView
        self.morphView = ThekeMorphoView(builder)

        _morphoView_box = builder.get_object("morphoView_box")
        _morphoView_box.pack_start(self.morphView, True, True, 0)

    def search_button_connect(self, callback):
        self.morphView.search_button_connect(callback)

    def set_lemma(self, lemma):
        self.morphView.set_lemma(lemma)

    def set_morph(self, word, morph):
        self.morphView.set_morph(word, morph)

    def set_strongs(self, strongs):
        self.morphView.set_strongs(strongs)

    def hide(self):
        self.toolViewBox.hide()

    def show(self):
        self.toolViewBox.show()