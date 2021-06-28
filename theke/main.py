import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import GLib

import Sword

import theke.sword
import theke.uri
import theke.templates
import theke.navigator
import theke.gui.mainwindow

import logging
logger = logging.getLogger(__name__)

class ThekeApp(Gtk.Application):
    def __init__(self):
        logger.debug("ThekeApp - Create a new instance")

        Gtk.Application.__init__(self,
                                 application_id="com.github.a2ohm.theke",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)

        self.add_main_option(
            "debug",
            ord("d"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Print debug messages",
            None,
        )

        self.window = None
        self.navigator = theke.navigator.ThekeNavigator()

    def do_startup(self):
        """Sets up the application when it first starts
        """
        logger.debug("ThekeApp - Do startup")

        Gtk.Application.do_startup(self)

        self.SwordLibrary = theke.sword.SwordLibrary()

    def do_activate(self):
        """Shows the default first window of the application (like a new document).
        This corresponds to the application being launched by the desktop environment
        """
        logger.debug("ThekeApp - Do activate")

        if not self.window:
            logger.debug("ThekeApp - Create a new window")
            self.window = theke.gui.mainwindow.ThekeWindow(navigator = self.navigator, application=self, title="Theke")

        self.window.show_all()

        # Parse Sword modules
        bible_mods = []

        for mod_name, mod in self.SwordLibrary.get_modules():
            if mod.get_type() == theke.sword.MODTYPE_BIBLES:
                bible_mods.append({'name': mod_name, 'type': mod.get_type(), 'description': mod.get_description()})
                
                # Register books present in this Bible source into the GotoBar
                # TODO: Y a-t-il une façon plus propre de faire la même chose ?
                vk = Sword.VerseKey()
                
                for itestament in [1, 2]:
                    vk.setTestament(itestament)
                    for ibook in range(1, vk.getBookMax() +1):
                        vk.setBook(ibook)
                        if mod.has_entry(vk):
                            self.window.gotobar.autoCompletionlist.append((vk.getBookName(), mod.get_name(), 'powder blue'))

            elif mod.get_type() == theke.sword.MODTYPE_GENBOOKS:
                # Only works for gen books
                #tkey = Sword.TreeKey_castTo(mod.getKey())
                pass     

        # Register application screens in the GotoBar
        for inAppUriKey in theke.uri.inAppURI.keys():
            self.window.gotobar.autoCompletionlist.append((inAppUriKey, 'Theke', 'sandy brown'))

        # Build templates
        theke.templates.build_template('welcome', {'BibleMods': bible_mods})
        theke.templates.build_template('modules', {'BibleMods': bible_mods})

        # Load the main screen
        uri = theke.uri.parse("theke:welcome", isEncoded=True)
        self.navigator.goto_uri(uri)