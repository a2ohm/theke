import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import GLib

import os
import theke
import theke.gui.mainwindow
import theke.index
import theke.navigator
import theke.sword
import theke.templates
import theke.uri

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

        # Create some directories
        for path in [theke.PATH_ROOT, theke.PATH_DATA, theke.PATH_EXTERNAL]:
            if not os.path.isdir(path):
                logger.debug("ThekeApp − Make dir : %s", path)
                os.mkdir(path)

        # Index sword modules
        indexBuilder = theke.index.ThekeIndexBuilder()
        indexBuilder.build(force = False)

    def do_activate(self):
        """Shows the default first window of the application (like a new document).
        This corresponds to the application being launched by the desktop environment
        """
        logger.debug("ThekeApp - Do activate")

        if not self.window:
            logger.debug("ThekeApp - Create a new window")
            self.window = theke.gui.mainwindow.ThekeWindow(navigator = self.navigator, application=self, title="Theke")

        self.window.show_all()

        # From the index ...
        thekeIndex = theke.index.ThekeIndex()

        # ... load the list of modules
        bible_mods = thekeIndex.list_sources(sourceType = theke.index.SOURCETYPE_SWORD, contentType = theke.sword.MODTYPE_BIBLES)
        book_mods = thekeIndex.list_sources(sourceType = theke.index.SOURCETYPE_SWORD, contentType = theke.sword.MODTYPE_GENBOOKS)

        # ... populate the gotobar autocompletion list
        for documentData in thekeIndex.list_documents():
            self.window.gotobar.autoCompletionlist.append((documentData.name, 'powder blue'))

        # Register application screens in the GotoBar
        # for inAppUriKey in theke.uri.inAppURI.keys():
        #     self.window.gotobar.autoCompletionlist.append((inAppUriKey, 'sandy brown'))

        # Build templates
        theke.templates.build_template('welcome', {'BibleMods': bible_mods})
        theke.templates.build_template('modules', {'BibleMods': bible_mods, 'BookMods' : book_mods})

        # Load the main screen
        uri = theke.uri.parse(theke.URI_WELCOME, isEncoded=True)
        self.navigator.goto_uri(uri)
