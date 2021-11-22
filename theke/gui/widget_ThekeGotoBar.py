from gi.repository import Gtk

@Gtk.Template.from_file('./theke/gui/templates/ThekeGotoBar.glade')
class ThekeGotoBar(Gtk.SearchEntry):
    __gtype_name__ = "ThekeGotoBar"

    def __init__(self):
        super().__init__()

        # Set the autocompletion
        #   0: name of the document
        #   1: color name use as background color
        self._entryCompletion = Gtk.EntryCompletion()
        self._autoCompletionlist = Gtk.ListStore(str, str)
        self._entryCompletion.set_model(self._autoCompletionlist)
        self._entryCompletion.set_text_column(0)

        renderer = self._entryCompletion.get_cells()[0]
        self._entryCompletion.add_attribute(renderer, 'background', 1)

        self.set_completion(self._entryCompletion)

        self._entryCompletion.connect("match-selected", self._entryCompletion_match_selected_cb)

    ### Callbacks
    def _entryCompletion_match_selected_cb(self, entry_completion, model, iter):
        # TODO: give name to column (and dont use a numerical value)
        # Update the text in the GotoBar
        self.set_text("{} ".format(model.get_value(iter, 0)))

        # Move the cursor to the end
        self.set_position(-1)
        return True
    ###

    def append(self, data):
        """Append date to the autocompletion list
        """
        self._autoCompletionlist.append(data)
