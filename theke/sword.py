import Sword
import re

MODTYPE_BIBLES = Sword.SWMgr().MODTYPE_BIBLES
MODTYPE_GENBOOKS = Sword.SWMgr().MODTYPE_GENBOOKS

pattern_paragraph_range = re.compile(r'^(\d+) to (\d+)$')

class SwordLibrary():
    def __init__(self, markup = Sword.FMT_HTML):
        self.markup = Sword.MarkupFilterMgr(markup)
        self.markup.thisown = False

        self.mgr = Sword.SWMgr(self.markup)

    def get_modules(self):
        return self.mgr.getModules().items()

    def get_module(self, moduleName):
        return self.mgr.getModule(moduleName)

    def get_book_module(self, moduleName):
        return Sword.SWGenBook_castTo(self.get_module(moduleName))

class SwordModule():
    def __init__(self, moduleName):
        self.moduleName = moduleName
        self.library = SwordLibrary()
        self.mod = self.library.get_module(moduleName)

        if not self.mod:
            raise ValueError("Unknown module: {}.".format(moduleName))

    def get_name(self):
        return self.mod.getName()

    def get_description(self):
        return self.mod.getDescription()

class SwordBible(SwordModule):
    def __init__(self, moduleName):
        super().__init__(moduleName)

        self.key = Sword.VerseKey_castTo(self.mod.getKey())
        self.key.setPersist(True)
        self.key.setVersificationSystem(self.mod.getConfigEntry("Versification"))

        self.library.mgr.setGlobalOption("Strong's Numbers", "Off")
        self.library.mgr.setGlobalOption("Cross-references", "Off")
        self.library.mgr.setGlobalOption("Lemmas", "Off")
        self.library.mgr.setGlobalOption("Morphological Tags", "On")
        self.library.mgr.setGlobalOption("Hebrew Vowel Points", "On")

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

        verse = ""

        while True:
            verse += "<sup>{}</sup>{}".format(self.key.getVerse(), self.mod.renderText())
            self.key.increment()

            if self.key.getChapter() != chapter:
                break

        return verse

class SwordBook(SwordModule):
    def __init__(self, moduleName):
        super().__init__(moduleName)

        self.key = Sword.TreeKey_castTo(self.mod.getKey())

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