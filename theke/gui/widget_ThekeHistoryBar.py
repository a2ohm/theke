import gi
from collections import OrderedDict

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango

MAX_NUMBER_OF_BUTTONS = 6

import theke.uri

home_uri = theke.uri.parse('theke:welcome', isEncoded=True)

class ThekeHistoryBar(Gtk.ButtonBox):
    def __init__(self, on_button_clicked_callback, *args, **kwargs):
        Gtk.Box.__init__(self, orientation = Gtk.Orientation.HORIZONTAL, *args, **kwargs)
        self.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        self.set_homogeneous(False)

        self.on_button_clicked = on_button_clicked_callback

        self.history = OrderedDict()

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        # Menu appearing right clicking on a button
        self.button_right_click_menu = Gtk.Menu()
        self.menu_copy_uri_to_clipboard = Gtk.MenuItem("Copier l'uri")
        self.menu_copy_uri_to_clipboard.connect('activate', self.handle_menu_copy_uri_to_clipboard)

        self.button_right_click_menu.append(self.menu_copy_uri_to_clipboard)
        self.menu_copy_uri_to_clipboard.show()

        # Add the home button at the beginning
        home_icon = Gtk.Image()
        home_icon.set_from_stock(Gtk.STOCK_HOME, Gtk.IconSize.BUTTON)
        button = Gtk.Button(image = home_icon, use_underline=False)

        button.set_tooltip_text(theke.uri.inAppURI['welcome'].shortTitle)
        button.uri = home_uri

        button.connect('clicked', self.on_button_clicked)
        button.show_all()

        self.pack_start(button, False, False, 0)

    def add_uri_to_history(self, label, uri):
        """Add an uri to the HistoryBar.

        @param label: (string) label to print in the HistoryBar
        @param uri: (ThekeUri) Uri of the new item
        """
        if uri == home_uri:
            # The home uri is not added to the history as it is alway here.
            return            

        try:
            historyIndex = list(self.history.keys()).index(label)
            button = self.get_children()[historyIndex+1]

            # The visited uri is already in the history,
            # move its button at the end of the bar
            self.history.move_to_end(label)
            self.reorder_child(button, -1)

            # Update the uri
            # (necessary if, for example, sources changed)
            self.history[label] = uri
            button.uri = uri
            button.set_tooltip_text(str(uri))

        except ValueError:
            # This uri does not exist in the history
            if len(self.history) >= MAX_NUMBER_OF_BUTTONS:
                self.history.popitem(last=False)
                self.remove(self.get_children()[1])

            self.history[label] = uri
            
            button = Gtk.Button(label=label, use_underline=False)
            button.set_tooltip_text(str(uri))
            button.uri = uri

            button.connect('button-release-event', self.on_button_release)
            button.connect('clicked', self.on_button_clicked)
            button.show_all()

            self.pack_start(button, False, False, 0)         

    def on_button_release(self, button, event):
        if event.type == Gdk.EventType.BUTTON_RELEASE:
            if event.button == 3: # Right click
                self.button_right_click_menu.popup_at_widget(button, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)
                self.menu_copy_uri_to_clipboard.uri = button.uri
                return True
            else:
                return False
        return False

    def handle_menu_copy_uri_to_clipboard(self, menu_item):
        self.clipboard.set_text(menu_item.uri.get_encoded_URI(), -1)

