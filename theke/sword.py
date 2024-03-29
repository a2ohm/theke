import logging
import threading
import re

from bs4 import BeautifulSoup

import Sword

from gi.repository import GLib

logger = logging.getLogger(__name__)

MODTYPE_BIBLES = Sword.SWMgr().MODTYPE_BIBLES
MODTYPE_GENBOOKS = Sword.SWMgr().MODTYPE_GENBOOKS

FMT_HTML = Sword.FMT_HTML
FMT_PLAIN = Sword.FMT_PLAIN
FMT_OSIS = Sword.FMT_OSIS

MARKUP = {"2TGreek": FMT_OSIS, "MorphGNT": FMT_HTML, "OSHB": FMT_HTML}

pattern_paragraph_range = re.compile(r'^(\d+) to (\d+)$')

class SwordLibrary():
    def __init__(self, markup = Sword.FMT_PLAIN):
        logger.debug("SwordLibrary - Create a new instance")
        self.markup = Sword.MarkupFilterMgr(markup)
        self.markup.thisown = False

        self.mgr = Sword.SWMgr(self.markup)

    def get_modules(self):
        """Return iterator through available modules
        """
        for moduleName in self.mgr.getModules():
            yield str(moduleName), SwordModule(str(moduleName), self.mgr)

    def get_module(self, moduleName):
        """Return a module given its name
        """
        return SwordModule(moduleName, self.mgr)

    def get_bible_module(self, moduleName):
        """Return a biblical module given its name
        """
        self.mgr.setGlobalOption("Strong's Numbers", "On")
        self.mgr.setGlobalOption("Cross-references", "Off")
        self.mgr.setGlobalOption("Lemmas", "On")
        self.mgr.setGlobalOption("Morphological Tags", "On")
        self.mgr.setGlobalOption("Hebrew Vowel Points", "On")

        return SwordBible(moduleName, self.mgr)

    def get_book_module(self, moduleName):
        """Return a general book module given its name
        """
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
        """Return the name of the module
        """
        return self.mod.getName()

    def get_description(self):
        """Return the description of the module
        """
        return self.mod.getDescription()

    def get_global_option_filter(self):
        """Return a list of global option filter
        """
        return [str(value) for key, value in self.mod.getConfigMap().items() if str(key) == "GlobalOptionFilter"]

    def get_lang(self):
        """Return the language of the module
        """
        return self.mod.getConfigEntry("Lang")

    def get_repr(self):
        """Return a string reprsentation of the module
        """
        return self.mod.getName()

    def get_short_repr(self):
        """Return a short string representation of the module
        """
        abbr = self.mod.getConfigEntry("Abbreviation")
        return abbr if abbr is not None else self.mod.getName()

    def get_type(self):
        """Return the type of the module
        """
        return self.mod.getType()

    def get_version(self):
        """Return the version of the module
        """
        return self.mod.getConfigEntry("Version")

    def has_entry(self, key):
        """True if key is valid for this module
        """
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
            verses.append(self.clean_verse(str(self.mod.renderText())))
            self.key.increment()

            if self.key.getChapter() != chapter:
                break

        return verses
    
    def clean_verse(self, rawVerse) -> str:
        """Remove unwanted tags that break the display of a verse

        For exemple, in swod modules, the last verse of the last chapter
        of each biblical book ends with something like:
            <chapter eID="gen4852" osisID="Acts.28"/> <div eID="gen3852" osisID="Acts" type="book"/>
        """
        v = BeautifulSoup(rawVerse, 'html.parser')
        for tag in v(['div', 'chapter']):
            # Remove tags
            tag.decompose()

        return v.prettify()

class SwordBook(SwordModule):
    def __init__(self, *argv, **kwargs):
        logger.debug("SwordBook - Create a new instance")

        super().__init__(*argv, **kwargs)

        self.mod = Sword.SWGenBook_castTo(self.mod)
        self.key = Sword.TreeKey_castTo(self.mod.getKey())

    def get_paragraph(self, parID):
        """Return a paragraph given its id
        """
        isParagraphFound, text = self.do_get_paragraph(self.key, parID)
        self.do_reset_key(self.key)

        return text if isParagraphFound else None

    def get_paragraph_and_siblings(self, parID):
        """Return a paragraph with its surrounding given its id
        """
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
    """Do a asynchronous search in a biblical module
    """
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
