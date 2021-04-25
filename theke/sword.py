import Sword
import re

MODTYPE_BIBLES = Sword.SWMgr().MODTYPE_BIBLES
MODTYPE_GENBOOKS = Sword.SWMgr().MODTYPE_GENBOOKS

pattern_paragraph_range = re.compile(r'^(\d+) to (\d+)$')
library = Sword.SWMgr(Sword.MarkupFilterMgr(Sword.FMT_HTML))
#library = Sword.SWMgr()

class SwordLibrary():
    def __init__(self):
        # self.markup = Sword.MarkupFilterMgr(Sword.FMT_OSIS)
        # self.library = Sword.SWMgr(self.markup)
        #self.library = Sword.SWMgr(Sword.MarkupFilterMgr(Sword.FMT_OSIS))
        pass

    def get_modules(self):
        #return self.library.getModules().items()
        return library.getModules().items()

    def get_module(self, moduleName):
        #return self.library.getModule(moduleName)
        return library.getModule(moduleName)

    def get_book_module(self, moduleName):
        return Sword.SWGenBook_castTo(self.get_module(moduleName))

class SwordBook():
    def __init__(self, moduleName):
        self.moduleName = moduleName
        self.library = SwordLibrary()
        self.mod = self.library.get_book_module(moduleName)
        self.key = Sword.TreeKey_castTo(self.mod.getKey())

    def get_name(self):
        return self.mod.getName()

    def get_description(self):
        return self.mod.getDescription()

    def get_paragraph(self, parID):
        isParagraphFound, text = self.do_get_paragraph(self.key, parID)
        self.do_reset_key(self.key)

        return (isParagraphFound, text)

    def get_paragraph_and_siblings(self, parID):
        isParagraphFound, text = self.do_get_paragraph(self.key, parID, doGetSiblings=True)
        self.do_reset_key(self.key)

        return (isParagraphFound, text)

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

            return (isParagraphFound, text)

        return (isParagraphFound, text)

    def do_reset_key(self, tk):
        while tk.parent():
            pass