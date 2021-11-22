import logging

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
        self.wgTocWindow = builder.get_object("tocPane_tocWindow")
        self.wgToc = builder.get_object("tocPane_toc")
        self.wgReduceExpandButton = builder.get_object("tocPane_reduceExpand_button")
        self.wgReduceExpandImage = builder.get_object("tocPane_reduceExpand_image")

        self.isReduce = True

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Chapitre", renderer, text=0)
        self.wgToc.append_column(column)

        self.wgToc.get_selection().connect("changed", self.handle_selection_changed)
        self.wgReduceExpandButton.connect("clicked", self.handle_reduceExpand_button_clicked)

    def show(self) -> None:
        """Show the table of content
        """
        self.wgFrame.show()
        if self.isReduce:
            self.expand()
    
    def expand(self) -> None:
        """Expand the table of content
        """
        self.isReduce = False
        self.wgTocWindow.show()
        self.wgTitle.show()
        self.wgReduceExpandImage.set_from_icon_name("pan-start-symbolic", Gtk.IconSize.BUTTON)

    def hide(self) -> None:
        """Hide the table of content
        """
        self.wgFrame.hide()
        self.isReduce = True

    def reduce(self) -> None:
        """Reduce the table of content
        """
        self.isReduce = True
        self.wgTocWindow.hide()
        self.wgTitle.hide()
        self.wgReduceExpandImage.set_from_icon_name("pan-end-symbolic", Gtk.IconSize.BUTTON)

    def set_title(self, title):
        """Set the title of the table of content
        """
        self.wgTitle.set_text(title)

    def set_content(self, content):
        """Set the content of the table of content
        """
        self.wgToc.set_model(content)

    def handle_reduceExpand_button_clicked(self, button) -> None:
        if self.isReduce:
            self.expand()
        else:
            self.reduce()

    def handle_selection_changed(self, tree_selection):
        self.emit("selection-changed", tree_selection)