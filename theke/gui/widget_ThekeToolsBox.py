from gi.repository import Gtk
from gi.repository import GObject

from theke.gui.widget_ThekeMorphoView import ThekeMorphoView
from theke.gui.widget_ThekeDicoView import ThekeDicoView
from theke.gui.widget_ReduceExpandButton import ReduceExpandButton

@Gtk.Template.from_file('./theke/gui/templates/ThekeToolsBox.glade')
class ThekeToolsBox(Gtk.Box):
    """In the main window, the ToolsBox gathers:
        - the MorphoView
        - the dicoView
    """
    __gtype_name__ = "ThekeToolsBox"

    isReduce = GObject.Property(type=bool, default=False)

    _toolsBox_search_button = Gtk.Template.Child()
    _toolsBox_reduceExpand_button = Gtk.Template.Child()
    _toolsBox_tools = Gtk.Template.Child()

    _toolsBox_word_label = Gtk.Template.Child()
    _toolsBox_lemma_box = Gtk.Template.Child()
    _toolsBox_lemma_label = Gtk.Template.Child()

    _toolsBox_strong_label = Gtk.Template.Child()

    _toolsBox_morphoView = Gtk.Template.Child()
    _toolsBox_dicoView = Gtk.Template.Child()

    def __init__(self) -> None:
        super().__init__()

        # Setup the expand/reduce button
        self._toolsBox_reduceExpand_button.set_orientation(self._toolsBox_reduceExpand_button.ORIENTATION_DOWN)

    ### Callbacks (from glade)
    @Gtk.Template.Callback()
    def _toolsBox_reduceExpand_button_clicked_cb(self, button) -> None:
        if self.props.isReduce:
            self.expand()
        else:
            self.reduce()

    @Gtk.Template.Callback()
    def _toolsBox_tools_max_position_notify_cb(self, object, param) -> None:
        object.set_position(object.props.max_position)
    ###

    def search_button_connect(self, callback):
        self._toolsBox_search_button.connect("clicked", callback)

    def set_lemma(self, lemma):
        if lemma:
            self._toolsBox_lemma_label.set_label(lemma)
            self._toolsBox_lemma_box.show()
        else:
            self._toolsBox_lemma_box.hide()

    def set_morph(self, word, morph):
        self._toolsBox_word_label.set_label(word)
        self._toolsBox_morphoView.set_morph(word, morph)

    def set_strongs(self, strongs):
        if strongs:
            self._toolsBox_strong_label.set_label(strongs)
            self._toolsBox_search_button.set_sensitive(True)
            self._toolsBox_strong_label.show()

            self._toolsBox_dicoView.load_entry_by_strongs(strongs)
        else:
            self._toolsBox_search_button.set_sensitive(False)
            self._toolsBox_strong_label.hide()

    ### Widget like functions

    def show(self):
        if self.isReduce:
            self.expand()
        super().show()

    def reduce(self):
        self.props.isReduce = True
        self._toolsBox_tools.hide()
        self._toolsBox_reduceExpand_button.switch()

    def expand(self):
        self.props.isReduce = False
        self._toolsBox_tools.show()
        self._toolsBox_reduceExpand_button.switch()
