import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio
from gi.repository import Gtk

import Sword

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

        # Parse Sword modules
        bible_mods = []

        for mod_name, mod in self.SwordLibrary.get_modules():
            if mod.getType() == theke.sword.MODTYPE_BIBLES:
                bible_mods.append({'name': mod_name, 'type': mod.getType(), 'description': mod.getDescription()})
                
                # Register books present in this Bible source into the GotoBar
                # TODO: Y a-t-il une façon plus propre de faire la même chose ?
                vk = Sword.VerseKey()
                
                for itestament in [1, 2]:
                    vk.setTestament(itestament)
                    for ibook in range(1, vk.getBookMax() +1):
                        vk.setBook(ibook)
                        if mod.hasEntry(vk):
                            self.window.gotobar.autoCompletionlist.append((vk.getBookName(), mod.getName(), 'powder blue'))

            elif mod.getType() == theke.sword.MODTYPE_GENBOOKS:
                # Only works for gen books
                #tkey = Sword.TreeKey_castTo(mod.getKey())
                pass     

        # Register application screens in the GotoBar
        screens = [('Bienvenue', 'welcome'), ('À propos', 'about')]
        for s in screens:
            self.window.gotobar.autoCompletionlist.append((s[0], 'Theke', 'sandy brown'))

        # Build templates
        theke.templates.build_template('welcome', {'BibleMods': bible_mods})

        # Load the main screen
        uri = theke.uri.ThekeURI("theke:///welcome.html")
        self.window.load_uri(uri)