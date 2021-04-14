import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk

class ThekeGotoBar(Gtk.SearchEntry):
    def __init__(self, *args, **kwargs):
        Gtk.SearchEntry.__init__(self, *args, **kwargs)

        # Set the icon
        #   go-next: right arrow
        self.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "go-next")

        # Set the autocompletion
        self.autoCompletion = Gtk.EntryCompletion()
        self.autoCompletionlist = Gtk.ListStore(str, str, str)
        self.autoCompletion.set_model(self.autoCompletionlist)
        self.autoCompletion.set_text_column(0)

        renderer = Gtk.CellRendererText()
        self.autoCompletion.pack_start (renderer, True)
        self.autoCompletion.add_attribute(renderer, 'text', 1)
        self.autoCompletion.add_attribute(renderer, 'background', 2)

        self.set_completion(self.autoCompletion)