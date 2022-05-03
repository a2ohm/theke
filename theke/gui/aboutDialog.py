from gi.repository import Gtk


@Gtk.Template.from_file('./theke/gui/aboutDialog.glade')
class AboutDialog(Gtk.AboutDialog):
    """About dialog"""

    __gtype_name__ = 'AboutDialog'

    def __init__(self):
        super().__init__()
