from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import GLib

import os
import yaml
import theke
import theke.index
import theke.sword
import theke.templates
import theke.uri

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
        self._navigator = None
        self._settings = None

        self._defaultUri = theke.URI_WELCOME

    def do_startup(self):
        """Sets up the application when it first starts
        """
        logger.debug("ThekeApp - Do startup")

        Gtk.Application.do_startup(self)

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

        # Index sword modules
        indexBuilder = theke.index.ThekeIndexBuilder()
        indexBuilder.build(force = False)

    def do_activate(self):
        """Shows the default first window of the application (like a new document).
        This corresponds to the application being launched by the desktop environment
        """
        logger.debug("ThekeApp - Do activate")

        if not self._window:
            import theke.gui.mainWindow
            import theke.navigator

            logger.debug("ThekeApp - Create a new window")

            # Load settings
            self._settings = yaml.safe_load(open(theke.PATH_SETTINGS_FILE, 'r'))
            # Set the navigator
            self._navigator = theke.navigator.ThekeNavigator(self._settings or {})

            self._window = theke.gui.mainWindow.ThekeWindow(navigator = self._navigator)
            self._window.set_application(self)

            # From the index ...
            thekeIndex = theke.index.ThekeIndex()

            # ... load the list of modules
            # TODO: pour l'usage qui en est fait, il serait préférable de créer la fonction
            #       thekeIndex.list_sword_modules()
            bible_mods = thekeIndex.list_sources(sourceType = theke.index.SOURCETYPE_SWORD, contentType = theke.sword.MODTYPE_BIBLES)
            book_mods = thekeIndex.list_sources(sourceType = theke.index.SOURCETYPE_SWORD, contentType = theke.sword.MODTYPE_GENBOOKS)

            # ... load the list of external documents
            external_docs = thekeIndex.list_external_documents()

            # ... populate the gotobar autocompletion list
            for documentData in thekeIndex.list_documents_by_type(theke.TYPE_BIBLE):
                self._window._ThekeGotoBar.append((documentData.name, 'powder blue'))

            for documentData in thekeIndex.list_documents_by_type(theke.TYPE_BOOK):
                self._window._ThekeGotoBar.append((documentData.name, 'white smoke'))

            # Register application screens in the GotoBar
            # for inAppUriKey in theke.uri.inAppURI.keys():
            #     self.window.gotobar.append((inAppUriKey, 'sandy brown'))

            # Build templates
            theke.templates.build_template('welcome', {'BibleMods': bible_mods})
            theke.templates.build_template('modules', {'BibleMods': bible_mods, 'BookMods' : book_mods})
            theke.templates.build_template('external_documents', {'ExternalDocs': external_docs})

        # Load the given uri
        uri = theke.uri.parse(self._defaultUri)
        self._navigator.goto_uri(uri)

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
