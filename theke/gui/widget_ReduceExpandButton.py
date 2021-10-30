from gi.repository import Gtk
from gi.repository import GObject

import logging
logger = logging.getLogger(__name__)

@Gtk.Template.from_file('./theke/gui/templates/ReduceExpandButton.glade')
class ReduceExpandButton(Gtk.Button):
    __gtype_name__ = "ReduceExpandButton"

    orientation = GObject.Property(type=int, default=1)

    ORIENTATION_UP = 1
    ORIENTATION_DOWN = -1

    ORIENTATION_RIGHT = 2
    ORIENTATION_LEFT = -2

    ICON_NAMES = {
        ORIENTATION_UP: "pan-up-symbolic",
        ORIENTATION_DOWN: "pan-down-symbolic",
        ORIENTATION_RIGHT: "pan-end-symbolic",
        ORIENTATION_LEFT: "pan-start-symbolic"
    }

    _icon = Gtk.Template.Child()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.connect("notify::orientation", self.update_icon_cb)

    def finish_setup(self, orientation = None) -> None:
        self.props.orientation = orientation or self.ORIENTATION_UP

    ### Callbacks

    def update_icon_cb(self, object, params):
        """Update the icon orientation"""
        self._icon.set_from_icon_name(self.ICON_NAMES[self.props.orientation], Gtk.IconSize.BUTTON)

    ###

    def switch(self):
        self.props.orientation = -self.props.orientation
