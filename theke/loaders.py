import Sword
import theke.uri
import theke.sword
import theke.reference

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

def format_sword_syntax(text):
    '''Format rendered text from sword into a theke comprehensible syntax
    '''
    return text.replace("title", "h2")

def load_sword(uri):
    '''Load an sword document given its uri and return it as a html string.

    @param uri: uri of the sword document (eg. sword:/bible/John 1:1?source=MorphGNT)
    '''

    if uri.path[1] == theke.uri.SWORD_BIBLE:
        return load_sword_bible(uri)
    elif uri.path[1] == theke.uri.SWORD_BOOK:
        return load_sword_book(uri)

def load_sword_book(uri):
    """Load a sword book.

    @param uri: a theke.uri matching "sword:/book/moduleName/parID"
        moduleName (mandatory): a valid sword book name (eg. VeritatisSplendor)
        parID: a paragraph id matching any osisID of the the sword book.
    """
    if len(uri.path) == 3:
        moduleName = uri.path[2]
        parID = 'Couverture'
        
        mod = theke.sword.SwordBook(moduleName)
        text = mod.get_paragraph(parID)
    elif len(uri.path) > 3:
        moduleName = uri.path[2]
        parID = uri.path[3]

        mod = theke.sword.SwordBook(moduleName)
        text = mod.get_paragraph_and_siblings(parID)
    else:
        raise ValueError("Invalid uri for a Sword Book: {}".format(uri.get_decoded_URI()))

    if text is None:
        text = """<p>Ce texte n'a pas été trouvé.</p>
        <p>uri : {}</p>""".format(uri.get_decoded_URI())
    else:
        text = format_sword_syntax(text)

    return book_template.format(
        title = mod.get_name(),
        mod_name = mod.get_name(),
        mod_description = mod.get_description(),
        text = text)

def load_sword_bible(uri):
    # TODO: theke.reference parses a reference directly from an uri
    br = theke.reference.BiblicalReference(uri.path[2], source = uri.params.get('source', sword_default_module))
    moduleName = br.source
    bookName = br.bookName
    chapter = br.chapter

    mod = theke.sword.SwordBible(moduleName)
    verse = mod.get_chapter(bookName, chapter)

    # Format the html page
    return bible_template.format(
        title = moduleName,
        mod_name = mod.get_name(),
        mod_description = mod.get_description(),
        text = verse)