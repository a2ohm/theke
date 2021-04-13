import Sword

MODTYPE_BIBLES = Sword.SWMgr().MODTYPE_BIBLES
MODTYPE_GENBOOKS = Sword.SWMgr().MODTYPE_GENBOOKS

class SwordLibrary():
    def __init__(self):
        self.library = Sword.SWMgr()