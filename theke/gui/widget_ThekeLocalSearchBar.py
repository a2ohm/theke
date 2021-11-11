from gi.repository import Gtk
from gi.repository import GObject

@Gtk.Template.from_file('./theke/gui/templates/ThekeLocalSearchBar.glade')
class ThekeLocalSearchBar(Gtk.Revealer):
    __gtype_name__ = "ThekeLocalSearchBar"

    search_mode_active = GObject.Property(type=bool, default=False)
    search_entry = GObject.Property(type=str, default="")

    _search_bar = Gtk.Template.Child()

    def finish_setup(self) -> None:
        self.connect("notify::search-mode-active", self._search_mode_active_cb)

    ### Callbacks  (from glade)
    @Gtk.Template.Callback()
    def _close_button_clicked_cb(self, object) -> None:
        self.props.search_mode_active = False

    @Gtk.Template.Callback()
    def _search_bar_search_changed_cb(self, search_entry) -> None:
        self.props.search_entry = search_entry.get_text()

    ### Others
    def _search_mode_active_cb(self, object, value) -> None:
        if self.props.search_mode_active:
            self.set_reveal_child(True)
            self._search_bar.grab_focus()

        else:
            self.set_reveal_child(False)
    ###
