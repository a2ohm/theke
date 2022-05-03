from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

import logging
logger = logging.getLogger(__name__)

LANG_FLAGS = {
    'fr': '🇫🇷️',
    'grc': '🇬🇷️',
    'hbo' : '🇮🇱️',
    'la' : '🇻🇦️',
}

@Gtk.Template.from_file('./theke/gui/templates/ThekeSourcesBar.glade')
class ThekeSourcesBar(Gtk.Revealer):
    __gtype_name__ = "ThekeSourcesBar"

    __gsignals__ = {
        'delete-source': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'source-requested': (GObject.SIGNAL_RUN_FIRST, None, (str,))
        }

    _addSource_button: Gtk.Button = Gtk.Template.Child()
    _listOfButtons: Gtk.ButtonBox = Gtk.Template.Child()

    def __init__(self, *args, **kwargs) -> None:
        logger.debug("ThekeSourcesBar - Create a new instance")

        super().__init__(*args, **kwargs)

        # Menu of the add source button
        self.addSourceMenu = None

        # Menu of each source buttons
        self.sourceMenu = Gtk.Menu()
        self.menuItem_deleteSource = Gtk.MenuItem("Supprimer la source")
        self.menuItem_deleteSource.connect('activate', self.handle_sourceItem_delete)
        self.menuItem_deleteSource.show()
        self.sourceMenu.append(self.menuItem_deleteSource)

    def addSource_button_connect(self, callback):
        self._addSource_button.connect("clicked", callback)

    def updateAvailableSources(self, availableSources):
        if availableSources:
            self.addSourceMenu = Gtk.Menu()

            for sourceName in sorted(availableSources):
                source = availableSources[sourceName]

                menuItem_source = Gtk.MenuItem("{} {}".format(LANG_FLAGS.get(source.lang, ''), source.name))
                menuItem_source.sourceName = sourceName
                menuItem_source.connect('activate', self.handle_sourceItem_request)

                self.addSourceMenu.append(menuItem_source)
                menuItem_source.show()

        else:
            self.set_reveal_child(False)

    def updateSources(self, sources):
        if sources:
            self._listOfButtons.foreach(lambda y: self._listOfButtons.remove(y))

            for source in sources:
                button = Gtk.Button(label=source.name, use_underline=False)
                button.connect("clicked", self.handle_sourceButton_clicked)
                button.show_all()

                self._listOfButtons.add(button)

        else:
            self.set_reveal_child(False)

    def handle_sourceButton_clicked(self, button):
        self.sourceMenu.popup_at_widget(button, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)
        self.menuItem_deleteSource.sourceName = button.get_label()

    def handle_sourceItem_delete(self, menu_item):
        self.emit("delete-source", menu_item.sourceName)

    def handle_sourceItem_request(self, menu_item):
        self.emit("source-requested", menu_item.sourceName)
    
    @Gtk.Template.Callback()
    def _addSource_button_clicked_cb(self, button):
        self.addSourceMenu.popup_at_widget(button, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)
