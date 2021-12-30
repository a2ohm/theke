from gi.repository import Gtk
from gi.repository import GObject

@Gtk.Template.from_file('./theke/gui/templates/ThekeLocalSearchBar.glade')
class ThekeLocalSearchBar(Gtk.Revealer):
    __gtype_name__ = "ThekeLocalSearchBar"

    __gsignals__ = {
        'search-next-match': (GObject.SIGNAL_RUN_LAST | GObject.SIGNAL_ACTION, None,
                      ()),
        'search-previous-match': (GObject.SIGNAL_RUN_LAST | GObject.SIGNAL_ACTION, None,
                      ()),
        }

    search_mode_active = GObject.Property(type=bool, default=False)
    search_entry = GObject.Property(type=str, default="")

    _search_bar = Gtk.Template.Child()

    def __init__(self) -> None:
        super().__init__()

        self.connect("notify::search-mode-active", self._search_mode_active_cb)
        self._search_bar.connect("next-match", lambda x: self.emit("search-next-match"))
        self._search_bar.connect("previous-match", lambda x: self.emit("search-previous-match"))

    ### Callbacks  (from glade)
    @Gtk.Template.Callback()
    def _close_button_clicked_cb(self, object) -> None:
        self.props.search_mode_active = False

    @Gtk.Template.Callback()
    def _search_bar_search_changed_cb(self, search_entry) -> None:
        self.props.search_entry = search_entry.get_text()

    @Gtk.Template.Callback()
    def _search_next_button_clicked_cb(self, button) -> None:
        self.emit("search-next-match")

    @Gtk.Template.Callback()
    def _search_previous_button_clicked_cb(self, button) -> None:
        self.emit("search-previous-match")

    ### Others
    def _search_mode_active_cb(self, object, value) -> None:
        if self.props.search_mode_active:
            self.set_reveal_child(True)
            self._search_bar.grab_focus()

        else:
            self.set_reveal_child(False)
    ###
