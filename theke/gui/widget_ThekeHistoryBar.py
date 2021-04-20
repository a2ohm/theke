import gi
from collections import deque

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import Pango

MAX_NUMBER_OF_BUTTONS = 6

class ThekeHistoryBar(Gtk.ButtonBox):
    def __init__(self, thekeWindow, *args, **kwargs):
        Gtk.Box.__init__(self, orientation = Gtk.Orientation.HORIZONTAL, *args, **kwargs)
        self.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        self.set_homogeneous(False)

        self.thekeWindow = thekeWindow
        self.history = deque()

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

            button.connect('clicked', self.on_button_clicked)
            button.show_all()

            self.pack_start(button, True, True, 0)

            

    def on_button_clicked(self, button):
        self.thekeWindow.load_uri(button.uri)