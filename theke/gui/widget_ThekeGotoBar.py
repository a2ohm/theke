from gi.repository import Gtk

class ThekeGotoBar(Gtk.SearchEntry):
    def __init__(self, *args, **kwargs):
        Gtk.SearchEntry.__init__(self, *args, **kwargs)

        self.set_placeholder_text('Ouvrir un document')

        # Set the icon
        #   go-next: right arrow
        self.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "go-next")

        # Set the autocompletion
        #   0: name of the document
        #   1: color name use as background color
        self.autoCompletion = Gtk.EntryCompletion()
        self.autoCompletionlist = Gtk.ListStore(str, str)
        self.autoCompletion.set_model(self.autoCompletionlist)
        self.autoCompletion.set_text_column(0)

        renderer = self.autoCompletion.get_cells()[0]
        self.autoCompletion.add_attribute(renderer, 'background', 1)

        self.set_completion(self.autoCompletion)