import gi

gi.require_version('Gtk', '3.0')

from gi.repository import GLib

import Sword

import threading
import re

import theke.uri
import theke.tableofcontent

import logging
logger = logging.getLogger(__name__)

MODTYPE_BIBLES = Sword.SWMgr().MODTYPE_BIBLES
MODTYPE_GENBOOKS = Sword.SWMgr().MODTYPE_GENBOOKS

FMT_HTML = Sword.FMT_HTML
FMT_PLAIN = Sword.FMT_PLAIN

MARKUP = {"MorphGNT": FMT_HTML, "OSHB": FMT_HTML}

pattern_paragraph_range = re.compile(r'^(\d+) to (\d+)$')

class SwordLibrary():
    def __init__(self, markup = Sword.FMT_PLAIN):
        logger.debug("SwordLibrary - Create a new instance")
        self.markup = Sword.MarkupFilterMgr(markup)
        self.markup.thisown = False

        self.mgr = Sword.SWMgr(self.markup)

    def get_modules(self):
        for moduleName in self.mgr.getModules():
            yield str(moduleName), SwordModule(str(moduleName), self.mgr)

    def get_module(self, moduleName):
        return SwordModule(moduleName, self.mgr)

    def get_bible_module(self, moduleName):
        self.mgr.setGlobalOption("Strong's Numbers", "On")
        self.mgr.setGlobalOption("Cross-references", "Off")
        self.mgr.setGlobalOption("Lemmas", "On")
        self.mgr.setGlobalOption("Morphological Tags", "On")
        self.mgr.setGlobalOption("Hebrew Vowel Points", "On")

        return SwordBible(moduleName, self.mgr)

    def get_book_module(self, moduleName):
        return SwordBook(moduleName, self.mgr)

class SwordModule():
    def __init__(self, moduleName, mgr):
        self.moduleName = moduleName
        self.mod = mgr.getModule(moduleName)

        # Trick: keep a reference to the SwordManager
        #        otherwise, the Sword library crashes
        self.mgr = mgr

        if not self.mod:
            raise ValueError("Unknown module: {}.".format(moduleName))

    def get_name(self):
        return self.mod.getName()

    def get_description(self):
        return self.mod.getDescription()

    def get_global_option_filter(self):
        return [str(value) for key, value in self.mod.getConfigMap().items() if str(key) == "GlobalOptionFilter"]

    def get_lang(self):
        return self.mod.getConfigEntry("Lang")

    def get_repr(self):
        return self.mod.getName()

    def get_short_repr(self):
        return self.mod.getName()

    def get_type(self):
        return self.mod.getType()

    def get_version(self):
        return self.mod.getConfigEntry("Version")

    def has_entry(self, key):
        return self.mod.hasEntry(key)

class SwordBible(SwordModule):
    def __init__(self, *argv, **kwargs):
        logger.debug("SwordBible - Create a new instance")

        super().__init__(*argv, **kwargs)

        self.key = Sword.VerseKey_castTo(self.mod.getKey())
        self.key.setPersist(True)
        self.key.setVersificationSystem(self.mod.getConfigEntry("Versification"))

    def get_verse(self, bookName, chapter, verse):
        """
        @param bookName: (string)
        @param chapter: (int)
        @param verse: (int)
        """
        self.key.setBookName(bookName)
        self.key.setChapter(chapter)
        self.key.setVerse(verse)
        
        self.mod.setKey(self.key)
        
        return self.mod.renderText()

    def get_chapter(self, bookName, chapter):
        """
        @param bookName: (string)
        @param chapter: (int)
        """
        self.key.setBookName(bookName)
        self.key.setChapter(chapter)
        self.key.setVerse(1)
        
        self.mod.setKey(self.key)

        verses = []

        while True:
            verses.append(self.mod.renderText())
            self.key.increment()

            if self.key.getChapter() != chapter:
                break

        return verses

class SwordBook(SwordModule):
    def __init__(self, *argv, **kwargs):
        logger.debug("SwordBook - Create a new instance")

        super().__init__(*argv, **kwargs)

        self.mod = Sword.SWGenBook_castTo(self.mod)
        self.key = Sword.TreeKey_castTo(self.mod.getKey())

    def get_short_repr(self):
        abbr = self.mod.getConfigEntry("Abbreviation")
        return abbr if abbr is not None else self.mod.getName()

    def get_paragraph(self, parID):
        isParagraphFound, text = self.do_get_paragraph(self.key, parID)
        self.do_reset_key(self.key)

        return text if isParagraphFound else None

    def get_paragraph_and_siblings(self, parID):
        isParagraphFound, text = self.do_get_paragraph(self.key, parID, doGetSiblings=True)
        self.do_reset_key(self.key)

        return text if isParagraphFound else None

    def do_get_paragraph(self, tk, parID, doGetSiblings = False):
        '''Return paragraph given its ID

        @param tk: a Sword.TreeKey of the module
        @param parID: (string) id of the paragraph
        '''
        text = ""
        isParagraphFound = False

        if tk.firstChild():
            while True:
                # Each section has a name (= osisID)
                sectionName = tk.getLocalName()
                text += str(self.mod.renderText())

                # Look if sectionName matches a paragraph range pattern
                # (eg. osisId="1-5" for a section containing paragraphs from 1 to 5)
                match_paragraph_range = pattern_paragraph_range.match(sectionName)

                if parID.isdigit() and match_paragraph_range is not None:
                    start = int(match_paragraph_range.group(1))
                    end = int(match_paragraph_range.group(2))

                    if start <= int(parID) <= end and tk.hasChildren():
                        isParagraphFound, parText = self.do_get_paragraph(tk, parID, doGetSiblings=True)
                        return (isParagraphFound, text + parText)

                # Look if sectionName matches a paragraph pattern
                # (paragraph number, eg. osisID="1" for paragraph number 1)
                elif sectionName == parID:
                    if doGetSiblings:
                        isParagraphFound = True
                    else:
                        return (True, str(self.mod.renderText()))

                elif tk.hasChildren():
                    isParagraphFound, text = self.do_get_paragraph(tk, parID, doGetSiblings=True)
                    if isParagraphFound:
                        return (isParagraphFound, text)

                if not tk.nextSibling():
                    break
            
            tk.parent()
            return (isParagraphFound, text)

        return (isParagraphFound, text)

    def do_reset_key(self, tk):
        while tk.parent():
            pass

def bibleSearch_keyword_async(moduleName, keyword, callback):
    mod = SwordLibrary().get_bible_module(moduleName)
    
    def do_search():
        rawResults = mod.mod.doSearch(keyword)
        
        # rawResults cannot be pass to callback (weird bug)
        # so it is copied in a dictionnary
        # In addition, results are sort by book
        results = {}
        for _ in range(rawResults.getCount()):
            bookName = str(Sword.VerseKey_castTo(rawResults.getElement()).getBookName())
            results[bookName] = results.get(bookName, []) + [str(rawResults.getText())]
            #results.append(rawResults.getText())
            rawResults.increment()

        GLib.idle_add(callback, results)

    thread = threading.Thread(target=do_search, daemon=True)
    thread.start()