from gi.repository import Gtk
from gi.repository import GObject

import logging
logger = logging.getLogger(__name__)

from theke.gui.widget_ThekeWebView import ThekeWebView

@Gtk.Template.from_file('./theke/gui/templates/ThekeDocumentView.glade')
class ThekeDocumentView(Gtk.Paned):
    __gtype_name__ = "ThekeDocumentView"

    __gsignals__ = {
        'toc-selection-changed': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,)),
        'document-load-changed': (GObject.SIGNAL_RUN_LAST, None,
                      (object, object)),
        'webview-mouse-target-changed': (GObject.SIGNAL_RUN_LAST, None,
                      (object, object, int)),
        }

    _webview_scrolledWindow = Gtk.Template.Child()

    def __init__(self, *args, **kwargs) -> None:
        logger.debug("ThekeDocumentView - Create a new instance")

        super().__init__(*args, **kwargs)

        self._navigator = None
        self._webview = ThekeWebView()

        self._setup_view()
        self._setup_callbacks()

    def _setup_view(self) -> None:
        pass

    def _setup_callbacks(self) -> None:
        #   ... document view
        # ... document view > webview: where the document is displayed
        self._webview.connect("load_changed", self._document_load_changed_cb)
        self._webview.connect("mouse-target-changed", self._webview_mouse_target_changed_cb)

        # self.wgFrame = builder.get_object("tocPane_frame")
        # self.wgTitle = builder.get_object("tocPane_title")
        # self.wgTocWindow = builder.get_object("tocPane_tocWindow")
        # self.wgToc = builder.get_object("tocPane_toc")
        # self.wgReduceExpandButton = builder.get_object("tocPane_reduceExpand_button")
        # self.wgReduceExpandImage = builder.get_object("tocPane_reduceExpand_image")

        # self.isReduce = True

        # renderer = Gtk.CellRendererText()
        # column = Gtk.TreeViewColumn("Chapitre", renderer, text=0)
        # self.wgToc.append_column(column)

        # self.wgToc.get_selection().connect("changed", self.handle_selection_changed)
        # self.wgReduceExpandButton.connect("clicked", self.handle_reduceExpand_button_clicked)

    def finish_setup(self) -> None:
        self._webview_scrolledWindow.add(self._webview)

    def register_navigator(self, navigator):
        self._webview.register_navigator(navigator)
        navigator.register_webview(self._webview)

    ### Callbacks (from glade)
    @Gtk.Template.Callback()
    def _toc_treeSelection_changed_cb(self, tree_selection):
        self.emit("toc-selection-changed", tree_selection)

    ### Others
    def _document_load_changed_cb(self, web_view, load_event):
        self.emit("document-load-changed", web_view, load_event)

    def _webview_mouse_target_changed_cb(self, web_view, hit_test_result, modifiers):
        self.emit("webview-mouse-target-changed", web_view, hit_test_result, modifiers)

    ###

    def grabe_focus(self) -> None:
        self._webview.grab_focus()

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
