import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject

import re

import theke.uri
import theke.sword
import theke.templates
import theke.reference

# Config
# ... for sword
sword_default_module = "MorphGNT"

def format_sword_syntax(text):
    '''Format rendered text from sword into a theke comprehensible syntax
    '''
    return text.replace("title", "h2")

class ThekeNavigator(GObject.Object):
    """Load content and provide metadata.

    The ThekeNavigator loads any data requested by the webview.
    It provides metadata about the current view (eg. to be used in the UI).
    Outside of the webview workflow, it has to be called to open an uri or a reference.
    """

    __gsignals__ = {
        'click_on_word': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,))
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.webview = None

        self._uri = None
        self._ref = None

        self._title = "Title"
        self._shortTitle = "ShortTitle"

        self._toc = None

        self._isMorphAvailable = False
        self._word = None
        self._lemma = None
        self._morph = '-'

    def register_webview(self, webview):
        self.webview = webview

    def goto_uri(self, uri, reload = False):
        """Ask the webview to load a given uri.

        Notice: all uri requests must go through the webview,
                even if it is then handled by this class.

        @parm uri: (string or ThekeUri)
        """
        if reload or uri != self._uri:
            if isinstance(uri, str):
                self.webview.load_uri(uri)
            elif isinstance(uri, theke.uri.ThekeURI):
                self.webview.load_uri(uri.get_encoded_URI())
            else:
                raise ValueError('This is not an uri: {}.'.format(uri))

        self.webview.grab_focus()

    def goto_ref(self, ref):
        """Ask the webview to load a given reference.
        """
        self.goto_uri(ref.get_uri())

    def load_theke_uri(self, uri, request):
        """Return a stream to the file pointed by the theke uri.
        Case 1. The uri gives a path to a file
            eg. uri = theke:/default.css

        Case 2. The uri gives an alias
            eg. uri = theke:welcome

        @param uri: (ThekeUri)
        @param request: a WebKit2.URISchemeRequest
        """
        if uri.path[0] == '':
            # Case 1.
            f = Gio.File.new_for_path('./assets' + '/'.join(uri.path))
            request.finish(f.read(), -1, None)

        else:
            # Case 2.
            inAppUriData = theke.uri.inAppURI[uri.path[0]]

            self._uri = uri
            self._title = inAppUriData.title
            self._shortTitle = inAppUriData.shortTitle
            self._toc = None
            self._ref = None
            self._isMorphAvailable = False
            self.set_property("morph", "-")

            f = Gio.File.new_for_path('./assets/{}'.format(inAppUriData.fileName))
            request.finish(f.read(), -1, 'text/html; charset=utf-8')

    def load_sword_uri(self, uri, request):
        '''Load an sword document given its uri and return it as a html string.

        @param uri: (ThekeUri) uri of the sword document (eg. sword:/bible/John 1:1?source=MorphGNT)
        @param request: (WebKit2.URISchemeRequest)
        '''
        if uri.path[1] == theke.uri.SWORD_BIBLE:
            html = self.load_sword_bible(uri)

        elif uri.path[1] == theke.uri.SWORD_BOOK:
            html = self.load_sword_book(uri)

        elif uri.path[1] == theke.uri.SWORD_SIGNAL:
            if uri.path[2] == 'click_on_word':
                self.emit("click_on_word", uri)
                html = ""

        else:
            raise ValueError('Unknown sword book type: {}.'.format(uri.path[1]))

        html_bytes = GLib.Bytes.new(html.encode('utf-8'))
        tmp_stream_in = Gio.MemoryInputStream.new_from_bytes(html_bytes)

        request.finish(tmp_stream_in, -1, 'text/html; charset=utf-8')

    def load_sword_bible(self, uri):
        ref = theke.reference.get_reference_from_uri(uri, defaultSource = sword_default_module)
        mod = theke.sword.SwordBible(ref.source)

        if self._ref is None or ref.bookName != self._ref.bookName:
            self._toc = mod.get_TOC(ref.bookName)
        
        self._uri = uri
        self._ref = ref
        self._title = ref.get_repr()
        self._shortTitle = ref.get_short_repr()
        self._isMorphAvailable = "OSISMorph" in mod.get_global_option_filter()
        self.set_property("morph", "-")

        return theke.templates.render('bible', {
            'lang': mod.get_lang(),
            'ref': ref,
            'verses': mod.get_chapter(ref.bookName, ref.chapter)
            })

    def load_sword_book(self, uri):
        """Load a sword book.

        @param uri: (ThekeUri) a theke.uri matching "sword:/book/moduleName/parID"
            moduleName (mandatory): a valid sword book name (eg. VeritatisSplendor)
            parID: a paragraph id matching any osisID of the the sword book.
        @param request: (WebKit2.URISchemeRequest)
        """
        if len(uri.path) == 3:
            moduleName = uri.path[2]
            parID = 'Couverture'
            
            mod = theke.sword.SwordBook(moduleName)
            text = mod.get_paragraph(parID)

            self._shortTitle = '{}'.format(mod.get_short_repr())
        elif len(uri.path) > 3:
            moduleName = uri.path[2]
            parID = uri.path[3]

            mod = theke.sword.SwordBook(moduleName)
            text = mod.get_paragraph_and_siblings(parID)

            self._shortTitle = '{} {}'.format(mod.get_short_repr(), parID)
        else:
            raise ValueError("Invalid uri for a Sword Book: {}".format(uri.get_decoded_URI()))

        if text is None:
            text = """<p>Ce texte n'a pas été trouvé.</p>
            <p>uri : {}</p>""".format(uri.get_decoded_URI())
        else:
            text = format_sword_syntax(text)

        self._uri = uri
        self._ref = None
        self._toc = None
        self._title = mod.get_name()
        self._isMorphAvailable = False
        self.set_property("morph", "-")

        return theke.templates.render('book', {
            'title': mod.get_name(),
            'mod_name': mod.get_name(),
            'mod_description': mod.get_description(),
            'text': text})

    def register_web_uri(self, uri):
        self._uri = uri
        self._ref = None

        self._title = self.webview.get_title()
        self._shortTitle = uri.netlock

        self._toc = None

        self._isMorphAvailable = False
        self._morph = "-"

    def do_click_on_word(self, uri):
        """Do what should be do when a new word is selected in the webview
        Action(s):
            - update morphological data
        """
        pattern_signal_clickOnWord = re.compile(r'(lemma.Strong:(?P<lemma>\w+))?(strong:(?P<strong>\w\d+))?')
        match_signal_clickOnWors = pattern_signal_clickOnWord.match(uri.params.get('lemma', ''))

        self.set_property("lemma", match_signal_clickOnWors.group('lemma'))
        self.set_property("morph", uri.params.get('morph', '-'))
        self.set_property("word", uri.params.get('word', '?'))

    
    # PUBLIC PROPERTIES
    # TODO: simplifier (https://python-gtk-3-tutorial.readthedocs.io/en/latest/objects.html#properties)
    @GObject.Property
    def uri(self):
        """The current uri"""
        return self._uri

    @GObject.Property
    def isMorphAvailable(self):
        return self._isMorphAvailable

    @GObject.Property
    def lemma(self):
        """The lemma of a selected word"""
        return self._lemma

    @lemma.setter
    def lemma(self, lemma):
        self._lemma = lemma

    @GObject.Property
    def morph(self):
        """The morph of a selected word"""
        return self._morph

    @morph.setter
    def morph(self, morph):
        self._morph = morph

    @GObject.Property
    def ref(self):
        """The current ref"""
        return self._ref

    @GObject.Property
    def shortTitle(self):
        """The short title of the current uri"""
        return self._shortTitle

    @GObject.Property
    def title(self):
        """The title of the current uri"""
        return self._title

    @GObject.Property
    def toc(self):
        """The table of content of the current uri"""
        return self._toc

    @GObject.Property
    def word(self):
        """The selected word"""
        return self._word

    @word.setter
    def word(self, word):
        self._word = word

    