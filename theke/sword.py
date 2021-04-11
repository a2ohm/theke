import Sword

MODTYPE_BIBLES = Sword.SWMgr().MODTYPE_BIBLES
MODTYPE_GENBOOKS = Sword.SWMgr().MODTYPE_GENBOOKS

class SwordLibrary():
    def __init__(self):
        self.library = Sword.SWMgr()

    def getModules(self, modType = MODTYPE_BIBLES):
        modules = {}

        for modName, mod in self.library.getModules().items():
            if mod.getType() == modType:
                modules[str(modName)] = mod

        return modules