import gi
from collections import deque

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango

MAX_NUMBER_OF_BUTTONS = 6

class ThekeHistoryBar(Gtk.ButtonBox):
    def __init__(self, navigator, *args, **kwargs):
        Gtk.Box.__init__(self, orientation = Gtk.Orientation.HORIZONTAL, *args, **kwargs)
        self.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        self.set_homogeneous(False)

        self.navigator = navigator
        self.history = deque()

        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        # Menu appearing right clicking on a button
        self.button_right_click_menu = Gtk.Menu()
        self.menu_copy_uri_to_clipboard = Gtk.MenuItem("Copier l'uri")
        self.menu_copy_uri_to_clipboard.connect('activate', self.handle_menu_copy_uri_to_clipboard)

        self.button_right_click_menu.append(self.menu_copy_uri_to_clipboard)
        self.menu_copy_uri_to_clipboard.show()

    def add_uri_to_history(self, label, uri):
        try:
            historyIndex = self.history.index((label, uri))

            # The visited uri is already in the history,
            # move its button at the end of the bar
            if historyIndex < MAX_NUMBER_OF_BUTTONS-1:
                # Rotate to.
                del self.history[historyIndex]
                self.history.append((label, uri))
                self.reorder_child(self.get_children()[historyIndex], -1)

        except ValueError:
            # This uri does not exist in the history
            if len(self.history) >= MAX_NUMBER_OF_BUTTONS:
                self.history.popleft()
                self.remove(self.get_children()[0])

            self.history.append((label, uri))
            button = Gtk.Button(label=label, use_underline=False)
            button.set_tooltip_text(str(uri))
            button.uri = uri

            button.connect('button-release-event', self.on_button_clicked)
            button.show_all()

            self.pack_start(button, False, False, 0)         

    def on_button_clicked(self, button, event):
        if event.type == Gdk.EventType.BUTTON_RELEASE:
            if event.button == 1: # Left click
                self.navigator.goto_uri(button.uri)
                return True
            elif event.button == 3: # Right click
                self.button_right_click_menu.popup_at_widget(button, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)
                self.menu_copy_uri_to_clipboard.uri = button.uri
                return True
            else:
                return False
        return False

    def handle_menu_copy_uri_to_clipboard(self, menu_item):
        self.clipboard.set_text(menu_item.uri.get_encoded_URI(), -1)

