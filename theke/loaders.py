import Sword

# Config
# ... for assets
assets_path = './assets/'

# ... for sword
sword_default_module = "MorphGNT"



def load_asset(uri):
        '''Load an asset (html page stored in the assets directory) given its uri
        and return it as a html string.

        @param uri: uri of the asset (eg. theke:///welcome.html)
        '''
        with open(assets_path + '/'.join(uri.path)) as f:
            html = f.read()

        return html

def load_sword(uri):
    '''Load an sword document given its uri and return it as a html string.

    @param uri: uri of the sword document (eg. sword:///bible/John 1:1?source=MorphGNT)
    '''

    # key: Bible key extracted from the uri (eg. John 1:1)
    key = uri.path[1]
    # moduleName: a valid Sword module name (eg. MorphGNT)
    moduleName = uri.params.get('source', sword_default_module)
    
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
    chapter = vk.getChapter()

    verse = "<sup>{}</sup>".format(vk.getVerse())
    verse += str(mod.renderText())
    vk.increment()

    while vk.getChapter() == chapter:
        verse += " <sup>{}</sup>".format(vk.getVerse())
        verse += str(mod.renderText())
        vk.increment()

    # Format the html page
    return "<h1>{mod_name}</h1><p>{mod_description}</p><p>{text}</p>".format(
        mod_name = mod.getName(),
        mod_description = mod.getDescription(),
        text = verse)