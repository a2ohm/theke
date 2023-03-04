from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject

import os
import yaml
import theke
import theke.gui.mainWindow
import theke.navigator
import theke.sword
import theke.templates
import theke.uri

from theke.archivist import ThekeArchivist
from theke.librarian import ThekeLibrarian

import logging
logger = logging.getLogger(__name__)

class ThekeApp(Gtk.Application):
    def __init__(self, *args, **kwargs):
        logger.debug("ThekeApp - Create a new instance")

        super().__init__(*args,
                        application_id="com.github.a2ohm.theke",
                        flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
                        **kwargs)

        self.add_main_option(
            "debug",
            ord("d"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Print debug messages",
            None,
        )

        self.add_main_option(
            "uri",
            ord("u"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.STRING,
            "Open this uri",
            "URI",
        )

        self.add_main_option(
            GLib.OPTION_REMAINING,
            0,
            GLib.OptionFlags.NONE,
            GLib.OptionArg.STRING_ARRAY,
            "Open this uri",
            "URI",
        )

        self._window = None
        self._archivist = None
        self._librarian = None

        self._settings = {}

        self._defaultUri = theke.URI_WELCOME

    @GObject.Property(
        type=ThekeArchivist, flags=GObject.ParamFlags.READABLE)
    def archivist(self):
        """Get application-wide archivist.
        """
        return self._archivist
    
    @GObject.Property(
        type=ThekeLibrarian, flags=GObject.ParamFlags.READABLE)
    def librarian(self):
        """Get application-wide librarian.
        """
        return self._librarian

    @GObject.Property(
        type=object, flags=GObject.ParamFlags.READABLE)
    def settings(self):
        """Get application-wide settings.
        """
        return self._settings

    def do_startup(self):
        """Sets the application up when it is started for the first time
        """
        logger.debug("ThekeApp - Do startup")

        Gtk.Application.do_startup(self)

        # Load settings
        self._settings = yaml.safe_load(open(theke.PATH_SETTINGS_FILE, 'r'))

        # Create some directories
        for path in [theke.PATH_ROOT, theke.PATH_DATA, theke.PATH_EXTERNAL, theke.PATH_CACHE]:
            if not os.path.isdir(path):
                logger.debug("ThekeApp − Make dir : %s", path)
                os.mkdir(path)
        
        # Create some files (eg. theke.conf, custom.css)
        for path in [theke.PATH_SETTINGS_FILE, theke.PATH_CUSTOM_CSS]:
            if not os.path.isfile(path):
                with open(path, 'w') as f:
                    pass

        # Init the archivist and the librarian
        self._archivist = ThekeArchivist()
        self._librarian = ThekeLibrarian(self._archivist)

        # Update the index
        self._archivist.update_index()

        # Build/Update templates
        bible_mods = self._archivist.list_sword_sources(contentType = theke.sword.MODTYPE_BIBLES)
        book_mods = self._archivist.list_sword_sources(contentType = theke.sword.MODTYPE_GENBOOKS)
        external_docs = self._archivist.list_external_documents()

        theke.templates.build_template('welcome', {'BibleMods': bible_mods})
        theke.templates.build_template('modules', {'BibleMods': bible_mods, 'BookMods' : book_mods})
        theke.templates.build_template('external_documents', {'ExternalDocs': external_docs})

    def do_activate(self):
        """Shows the default first window of the application (like a new document).
        This corresponds to the application being launched by the desktop environment
        """
        logger.debug("ThekeApp - Do activate")

        if not self._window:
            import theke.gui.mainWindow
            import theke.navigator

            logger.debug("ThekeApp - Create a new window")

            self._window = theke.gui.mainWindow.ThekeWindow(self)
            self._window.set_application(self)

            # Register application screens in the GotoBar
            # for inAppUriKey in theke.uri.inAppURI.keys():
            #     self.window.gotobar.append((inAppUriKey, 'sandy brown'))

        # Load the given uri
        uri = theke.uri.parse(self._defaultUri)
        self._window.open_uri(uri)

        self._window.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        # convert GVariantDict -> GVariant -> dict
        options = options.end().unpack()

        if "uri" in options:
            # Start Theke with this uri
            logger.debug("Uri read from the command line: %s", options["uri"])
            self._defaultUri = options["uri"]

        if GLib.OPTION_REMAINING in options:
            # Open the first uri
            logger.debug("Uri read from the command line: %s", options[GLib.OPTION_REMAINING][0])
            self._defaultUri = options[GLib.OPTION_REMAINING][0]

        self.activate()
        return 0
