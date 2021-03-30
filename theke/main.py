import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio
from gi.repository import Gtk

import Sword
import theke.gui.mainwindow

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
        html = self.get_sword_text("John 1:1", "MorphGNT")
        self.window.load_html(html)

        

    def get_sword_text(self, key, moduleName):
        """Get some text from sword and return it as a html string.
        
        @param key: Bible key (eg. John 1:1)
        @param moduleName: a valid Sword module name (eg.MorphGNT)
        @return: text in a html string
        """
        
        markup = Sword.MarkupFilterMgr(Sword.FMT_OSIS)
        markup.thisown = False

        mgr = Sword.SWMgr(markup)
        mgr.setGlobalOption("Strong's Numbers", "Off")
        mgr.setGlobalOption("Cross-references", "Off")
        mgr.setGlobalOption("Lemmas", "Off")
        mgr.setGlobalOption("Morphological Tags", "Off")

        mod = mgr.getModule(moduleName)

        vk = Sword.VerseKey(key)
        vk.setPersist(True)

        mod.setKey(vk)

        verse = str(mod.renderText())
        vk.increment()

        while vk.getChapter() == 1:
            verse += " " + str(mod.renderText())
            vk.increment()

        # Format the html page
        return "<h1>{mod_name}</h1><p>{mod_description}</p><p>{text}</p>".format(
            mod_name = mod.getName(),
            mod_description = mod.getDescription(),
            text = verse)