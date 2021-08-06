import logging
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import GObject

logger = logging.getLogger(__name__)

class ThekeTableOfContent(GObject.Object):
    __gsignals__ = {
        'selection-changed': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,))
        }

    def __init__(self, builder, *args, **kwargs) -> None:
        logger.debug("ThekeTableOfContent - Create a new instance")

        super().__init__(*args, **kwargs)

        self.wgFrame = builder.get_object("tocPane_frame")
        self.wgTitle = builder.get_object("tocPane_title")
        self.wgToc = builder.get_object("tocPane_toc")

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Chapitre", renderer, text=0)
        self.wgToc.append_column(column)

        self.wgToc.get_selection().connect("changed", self.handle_selection_changed)

    def hide(self) -> None:
        """Hide the table of content
        """
        self.wgFrame.hide()

    def show(self) -> None:
        """Show the table of content
        """
        self.wgFrame.show()

    def set_title(self, title):
        """Set the title of the table of content
        """
        self.wgTitle.set_text(title)

    def set_content(self, content):
        """Set the content of the table of content
        """
        self.wgToc.set_model(content)

    def handle_selection_changed(self, tree_selection):
        self.emit("selection-changed", tree_selection)