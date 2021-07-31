import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

import logging
logger = logging.getLogger(__name__)

class ThekeSourcesBar():
    def __init__(self, builder) -> None:
        self.sourcesBar_box = builder.get_object("sourcesBar_Box")
        self.addSource_button = builder.get_object("sourcesBar_addButton")

        self.addSource_button.connect("clicked", self.handle_addButton_clicked)

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
                # menu_source.connect('activate', self.handle_menu_copy_uri_to_clipboard)

                self.sourcesMenu.append(menu_source)
                menu_source.show()

    def handle_addButton_clicked(self, button):
        self.sourcesMenu.popup_at_widget(button, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)

    # def show_sources_menu(self, button, sources):
    #     sourcesMenu = Gtk.Menu()

    #     for source in sources:
    #         menu_source = Gtk.MenuItem("{}".format(source))
    #         # menu_source.connect('activate', self.handle_menu_copy_uri_to_clipboard)

    #         sourcesMenu.append(menu_source)
    #         menu_source.show()

    #     sourcesMenu.popup_at_widget(button, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)