import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio
from gi.repository import Gtk

import theke.sword
import theke.uri
import theke.templates
import theke.gui.mainwindow

class ThekeApp(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self,
                                 application_id="com.github.a2ohm.theke",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)

        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        self.SwordLibrary = theke.sword.SwordLibrary()

    def do_activate(self):
        if not self.window:
            self.window = theke.gui.mainwindow.ThekeWindow(application=self, title="Theke")

        self.window.show_all()
        self.load_main_screen()

    def load_main_screen(self):
        modules = [{'name': modName, 'type': mod.getType(), 'description': mod.getDescription()}
            for modName, mod in self.SwordLibrary.getModules(theke.sword.MODTYPE_BIBLES).items()]
        
        theke.templates.build_template('welcome', {'BibleMods': modules})

        # Load the main screen
        uri = theke.uri.ThekeURI("theke:///welcome.html")
        self.window.load_uri(uri)