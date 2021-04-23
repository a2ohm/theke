import Sword
import theke.uri

# Config
# ... for sword
sword_default_module = "MorphGNT"

# Templates
bible_template = '''<html>
    <head>
        <meta http-equiv="content-type" content="text/html; charset=UTF-8">
        <link rel="stylesheet" href="theke:/default.css" type="text/css">
        <link rel="stylesheet" href="theke:/bible.css" type="text/css">

        <title>{title}</title>
    </head>
    <body>
        <h1>{mod_name}</h1>
        <p>{mod_description}</p>
        <p>{text}</p>
    </body>
</html>
'''

book_template = '''<html>
    <head>
        <meta http-equiv="content-type" content="text/html; charset=UTF-8">
        <link rel="stylesheet" href="theke:/default.css" type="text/css">
        <link rel="stylesheet" href="theke:/book.css" type="text/css">

        <title>{title}</title>
    </head>
    <body>
        <h1>{mod_name}</h1>
        <p>{mod_description}</p>
        {text}
    </body>
</html>
'''

def format_sword_syntax(text, depth):
    '''Format rendered text from sword into a theke comprehensible syntax
    '''
    return text.replace("title", "h{}".format(depth+2))

def load_sword(uri):
    '''Load an sword document given its uri and return it as a html string.

    @param uri: uri of the sword document (eg. sword:/bible/John 1:1?source=MorphGNT)
    '''

    if uri.path[1] == theke.uri.SWORD_BIBLE:
        return load_sword_bible(uri)
    elif uri.path[1] == theke.uri.SWORD_BOOK:
        return load_sword_book(uri)

def load_sword_book(uri):
    # moduleName: a valid Sword module name (eg. MorphGNT)
    moduleName = uri.path[2]

    mgr = Sword.SWMgr()
    mod = mgr.getModule(moduleName)
    tk = Sword.TreeKey_castTo(mod.getKey())

    def getBookText(tk, depth = 0):
        '''Recurrently, dives into a book and returns all of its content.

        @param tk: a Sword.TreeKey
        @param depth: level of the reccurence
        '''
        text = ""
        if tk.firstChild():
            while True:
                text += format_sword_syntax(str(mod.renderText()), depth)
                if tk.hasChildren():
                    text += getBookText(tk, depth + 1)

                if not tk.nextSibling():
                    break

            tk.parent()
        
        return text

    text = getBookText(tk)

    return book_template.format(
        title = mod.getName(),
        mod_name = mod.getName(),
        mod_description = mod.getDescription(),
        text = text)

def load_sword_bible(uri):
    # key: Bible key extracted from the uri (eg. John 1:1)
    key = uri.path[2]
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

    verse = "<sup>{}</sup>{}".format(vk.getVerse(), mod.renderText())
    vk.increment()

    while vk.getChapter() == chapter:
        verse += " <sup>{}</sup>{}".format(vk.getVerse(), mod.renderText())
        vk.increment()

    # Format the html page
    return bible_template.format(
        title = key,
        mod_name = mod.getName(),
        mod_description = mod.getDescription(),
        text = verse)