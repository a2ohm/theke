import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

import logging
logger = logging.getLogger(__name__)

class ThekeSourcesBar(GObject.Object):
    __gsignals__ = {
        'delete-source': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'source-requested': (GObject.SIGNAL_RUN_FIRST, None, (str,))
        }

    def __init__(self, builder, *args, **kwargs) -> None:
        logger.debug("ThekeSourcesBar - Create a new instance")

        super().__init__(*args, **kwargs)

        self.sourcesBar_box = builder.get_object("sourcesBar_Box")
        self.addSource_button = builder.get_object("sourcesBar_addButton")
        self.listOfButtons = builder.get_object("sourcesBar_listOfButtons")

        self.addSource_button.connect("clicked", self.handle_addSourceButton_clicked)

        # Menu of the add source button
        self.addSourceMenu = None

        # Menu of each source buttons
        self.sourceMenu = Gtk.Menu()
        self.menuItem_deleteSource = Gtk.MenuItem("Supprimer la source")
        self.menuItem_deleteSource.connect('activate', self.handle_sourceItem_delete)
        self.menuItem_deleteSource.show()
        self.sourceMenu.append(self.menuItem_deleteSource)


    def addSource_button_connect(self, callback):
        self.addSource_button.connect("clicked", callback)

    def hide(self):
        self.sourcesBar_box.hide()

    def show(self):
        self.sourcesBar_box.show()

    def updateAvailableSources(self, availableSources):
        if availableSources is None:
            self.hide()

        else:
            self.addSourceMenu = Gtk.Menu()

            for source in availableSources:
                menuItem_source = Gtk.MenuItem("{}".format(source))
                menuItem_source.connect('activate', self.handle_sourceItem_request)

                self.addSourceMenu.append(menuItem_source)
                menuItem_source.show()

    def updateSources(self, sources):
        self.listOfButtons.foreach(lambda y: self.listOfButtons.remove(y))

        for source in sources:
            button = Gtk.Button(label=source, use_underline=False)
            button.connect("clicked", self.handle_sourceButton_clicked)
            button.show_all()

            self.listOfButtons.add(button)

    def handle_addSourceButton_clicked(self, button):
        self.addSourceMenu.popup_at_widget(button, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)

    def handle_sourceButton_clicked(self, button):
        self.sourceMenu.popup_at_widget(button, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)
        self.menuItem_deleteSource.sourceName = button.get_label()

    def handle_sourceItem_delete(self, menu_item):
        self.emit("delete-source", menu_item.sourceName)

    def handle_sourceItem_request(self, menu_item):
        self.emit("source-requested", menu_item.get_label())