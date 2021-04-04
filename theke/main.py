import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio
from gi.repository import Gtk

import theke.gui.mainwindow
import theke.uri

class ThekeApp(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self,
                                 application_id="com.github.a2ohm.theke",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)

        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self) 

    def do_activate(self):
        if not self.window:
            self.window = theke.gui.mainwindow.ThekeWindow(application=self, title="Theke")

        self.window.show_all()

        # Load some default text
        uri = theke.uri.ThekeURI("theke:///welcome.html")
        self.window.load_uri(uri)

        # Show something in the status bar
        context_id = self.window.statusbar.get_context_id("main")
        self.window.statusbar.push(context_id, "{}".format(uri))