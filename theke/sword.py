import Sword
import re

MODTYPE_BIBLES = Sword.SWMgr().MODTYPE_BIBLES
MODTYPE_GENBOOKS = Sword.SWMgr().MODTYPE_GENBOOKS

pattern_paragraph_range = re.compile(r'^(\d+) to (\d+)$')

class SwordLibrary():
    def __init__(self):
        self.library = Sword.SWMgr()

    def get_modules(self):
        return self.library.getModules().items()

    def get_module(self, moduleName):
        return self.library.getModule(moduleName)

    def get_book_module(self, moduleName):
        return Sword.SWGenBook_castTo(self.get_module(moduleName))

class SwordBook():
    def __init__(self, moduleName):
        self.moduleName = moduleName
        self.library = SwordLibrary()
        self.mod = self.library.get_book_module(moduleName)

    def get_name(self):
        return self.mod.getName()

    def get_description(self):
        return self.mod.getDescription()

    def get_paragraph(self, parID):
        return self.do_get_paragraph(Sword.TreeKey_castTo(self.mod.getKey()), parID)

    def get_paragraph_and_siblings(self, parID):
        return self.do_get_paragraph(Sword.TreeKey_castTo(self.mod.getKey()), parID, doGetSiblings=True)

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
                        return self.do_get_paragraph(tk, parID, doGetSiblings=True)

                # Look if sectionName matches a paragraph pattern
                # (paragraph number, eg. osisID="1" for paragraph number 1)
                elif sectionName == parID:
                    print("FIND paragraph §{}".format(parID))
                    if doGetSiblings:
                        isParagraphFound = True
                    else:
                        return (True, self.mod.renderText())

                elif tk.hasChildren():
                    isParagraphFound, text = self.do_get_paragraph(tk, parID, doGetSiblings=True)
                    if isParagraphFound:
                        return (isParagraphFound, text)

                if not tk.nextSibling():
                    break

            tk.parent()
            return (isParagraphFound, text)

        return (isParagraphFound, text)