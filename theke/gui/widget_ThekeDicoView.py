import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from gi.repository import GObject

from theke.myDico import myDico

class ThekeDicoView(GObject.Object):
    
    hasChangeToSave = GObject.Property(type=int, default=0)
    strongsNb = GObject.Property(type=str, default="")
    lemma = GObject.Property(type=str, default="")

    def __init__(self, builder) -> None:
        super().__init__()

        # Init/Load dictionaries
        self.myDico = myDico()

        # myDicoWidget
        self.myDicoView_label = builder.get_object("myDicoView_label")
        self.myDicoView_textInput = builder.get_object("myDicoView_textInput")
        self.myDicoView_textInput_buffer = self.myDicoView_textInput.get_buffer()
        self.myDicoView_textInput_loaded = ""

        self.myDicoView_textInput_buffer.connect("changed", self.handle_myDico_textInput_changed)
        self.connect("notify::hasChangeToSave", self.handle_myDico_hasChangeToSave)
        self.connect("notify::strongsNb", self.handle_strongsNb_changed)

        # Save changes at least every 10 seconds
        GLib.timeout_add_seconds(10, self.myDico_do_save)

    def load_entry_by_strongs(self, strongsNb) -> None:
        """Load dictionaries entries given a Strongs number.

        @param strongsNb: Strongs number
        """
        # Save the current myDico entry
        self.myDico_do_save(force = self.hasChangeToSave > 1)

        # Dictionaries connected to notify::strongsNb load the entry.
        with self.freeze_notify():
            self.set_property("strongsNb", strongsNb)
            self.set_property("lemma", '')

    def myDico_do_save(self, force = False) -> bool:
        # Wait at least 10 seconds before saving.
        if force or self.hasChangeToSave == 1:
            self.myDico.set_entry(self.strongsNb, self.lemma, self.myDicoView_textInput_buffer.props.text)
            self.myDicoView_textInput_loaded = self.myDicoView_textInput_buffer.props.text
            
            self.set_property("hasChangeToSave", 0)

        elif self.hasChangeToSave > 1:
            self.set_property("hasChangeToSave", 1)

        return True

    def handle_myDico_textInput_changed(self, textBuffer) -> None:
        if textBuffer.props.text != self.myDicoView_textInput_loaded:
            self.set_property("hasChangeToSave", 2)
        else:
            self.set_property("hasChangeToSave", 0)

    def handle_myDico_hasChangeToSave(self, object, param) -> None:
        if self.hasChangeToSave > 0:
            self.myDicoView_label.set_markup("Dictionnaire personnel <b>*</b>")
        else:
            self.myDicoView_label.set_markup("Dictionnaire personnel")

    def handle_strongsNb_changed(self, object, param) -> None:
        myDicoEntry = self.myDico.get_entry(self.strongsNb)

        if myDicoEntry is None:
            self.myDicoView_textInput_loaded = ''
        else:
            self.myDicoView_textInput_loaded = myDicoEntry.definition

        self.myDicoView_textInput_buffer.set_text(self.myDicoView_textInput_loaded)