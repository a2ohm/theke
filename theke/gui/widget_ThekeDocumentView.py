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

    isReduce = GObject.Property(type=bool, default=True)

    _webview_scrolledWindow = Gtk.Template.Child()
    _toc_frame = Gtk.Template.Child()
    _toc_title = Gtk.Template.Child()
    _toc_tocWindow = Gtk.Template.Child()
    _toc_treeView = Gtk.Template.Child()

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

        # self.wgReduceExpandImage = builder.get_object("tocPane_reduceExpand_image")

    def finish_setup(self) -> None:
        # Add the webview into the document view
        # (this cannot be done in Glade)
        self._webview_scrolledWindow.add(self._webview)

        # Setup the table of contents
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Chapitre", renderer, text=0)
        self._toc_treeView.append_column(column)

    def register_navigator(self, navigator):
        self._webview.register_navigator(navigator)
        navigator.register_webview(self._webview)

    ### Callbacks (from glade)
    @Gtk.Template.Callback()
    def ThekeDocumentView_min_position_notify_cb(self, object, param) -> None:
        object.set_position(object.props.min_position)

    @Gtk.Template.Callback()
    def _toc_reduceExpand_button_clicked_cb(self, button) -> None:
        if self.props.isReduce:
            self.expand_toc()
        else:
            self.reduce_toc()

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

    def show_toc(self) -> None:
        """Show the table of content
        """
        self._toc_frame.show()
        if self.props.isReduce:
            self.expand_toc()
    
    def expand_toc(self) -> None:
        """Expand the table of content
        """
        self.props.isReduce = False
        self._toc_tocWindow.show()
        self._toc_title.show()
        #self.wgReduceExpandImage.set_from_icon_name("pan-start-symbolic", Gtk.IconSize.BUTTON)

    def hide_toc(self) -> None:
        """Hide the table of content
        """
        self._toc_frame.hide()
        self.props.isReduce = True

    def reduce_toc(self) -> None:
        """Reduce the table of content
        """
        self.props.isReduce = True
        self._toc_tocWindow.hide()
        self._toc_title.hide()
        #self.wgReduceExpandImage.set_from_icon_name("pan-end-symbolic", Gtk.IconSize.BUTTON)

    def set_title(self, title):
        """Set the title of the table of content
        """
        self._toc_title.set_text(title)

    def set_content(self, content):
        """Set the content of the table of content
        """
        self._toc_treeView.set_model(content)
