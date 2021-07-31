import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject

import logging
logger = logging.getLogger(__name__)

class ThekeSourcesBar(GObject.Object):
    __gsignals__ = {
        'source-requested': (GObject.SIGNAL_RUN_FIRST, None,
                      (str,))
        }

    def __init__(self, builder, *args, **kwargs) -> None:
        logger.debug("ThekeSourcesBar - Create a new instance")

        super().__init__(*args, **kwargs)

        self.sourcesBar_box = builder.get_object("sourcesBar_Box")
        self.addSource_button = builder.get_object("sourcesBar_addButton")
        self.listOfButtons = builder.get_object("sourcesBar_listOfButtons")

        self.addSource_button.connect("clicked", self.handle_addSource_clicked)

        self.sourcesMenu = Gtk.Menu()

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
            self.sourcesMenu = Gtk.Menu()

            for source in availableSources:
                menu_source = Gtk.MenuItem("{}".format(source))
                menu_source.connect('activate', self.handle_sourceItem_activate)

                self.sourcesMenu.append(menu_source)
                menu_source.show()

    def updateSources(self, sources):
        self.listOfButtons.foreach(lambda y: self.listOfButtons.remove(y))

        for source in sources:
            button = Gtk.Button(label=source, use_underline=False)
            button.show_all()

            self.listOfButtons.add(button)

    def handle_addSource_clicked(self, button):
        self.sourcesMenu.popup_at_widget(button, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)

    def handle_sourceItem_activate(self, menu_item):
        self.emit("source-requested", menu_item.get_label())