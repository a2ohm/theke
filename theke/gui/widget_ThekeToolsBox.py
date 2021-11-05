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

    __gsignals__ = {
        'save': (GObject.SignalFlags.RUN_LAST | GObject.SignalFlags.ACTION, None, ())
        }

    isReduce = GObject.Property(type=bool, default=False)

    _toolsBox_reduceExpand_button = Gtk.Template.Child()
    _toolsBox_tools = Gtk.Template.Child()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # self.toolViewBox = builder.get_object("toolsView_Box")
        # self.toolView_tools = builder.get_object("toolsView_tools")

        # self.word_label = builder.get_object("toolsView_word")
        # self.lemma_box = builder.get_object("toolsView_lemma")
        # self.lemma_label = builder.get_object("toolsView_lemmaText")
        # self.strong_label = builder.get_object("toolsView_strongText")
        # self.search_button = builder.get_object("toolsView_searchButton")

        # # MorphoView
        # self.morphView = ThekeMorphoView(builder)

        # # dicoView
        # self.dicoView = builder.get_object("myDicoView")

        # # TODO: Créer un nouveau signal attaché à la ToolView
        # # GObject.signal_new(signal_name, type, flags, return_type, param_types)

        # #self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        # #self.add_events(Gdk.EventMask.ALL_EVENTS_MASK)
        # print(self.get_events())

        # # # SET ACCELERATORS (keyboard shortcuts)
        # # accelerators = Gtk.AccelGroup()
        # # self.add_accel_group(accelerators)

        # # # ... Ctrl+s: save modifications in the personal dictionary
        # # key, mod = Gtk.accelerator_parse('<Control>s')
        # # self.add_accelerator('save', accelerators, key, mod, Gtk.AccelFlags.VISIBLE)

    def finish_setup(self) -> None:
        # Setup the expand/reduce button
        self._toolsBox_reduceExpand_button.finish_setup(orientation = self._toolsBox_reduceExpand_button.ORIENTATION_DOWN)

    ### Callbacks (from glade)
    @Gtk.Template.Callback()
    def _toolsBox_reduceExpand_button_clicked_cb(self, button) -> None:
        if self.props.isReduce:
            self.expand()
        else:
            self.reduce()
    ###

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

    ### Signal handlers

    def do_save(self) -> None:
        print("foo")
        if self.dicoView.has_focus():
            self.dicoView.myDico_do_save(force = True)

    def save(self) -> None:
        print("bar")
