from gi.repository import Gio
from gi.repository import GObject

import theke

import logging
logger = logging.getLogger(__name__)

class ThekeDocument(GObject.GObject):
    def __init__(self, ref, handler, toc = None) -> None:
        super().__init__()

        self._ref = ref
        self._handler = handler
        self._toc = toc

    @GObject.Property(
        type=Gio.InputStream, default=None, flags=GObject.ParamFlags.READABLE)
    def inputStream(self):
        """Get an inputStream to read the document from.
        """
        return self._handler.get_input_stream()
    
    @GObject.Property(type=str)
    def availableSources(self):
        """Available sources of the current documment
        """
        return self._ref.availableSources

    @GObject.Property(type=object)
    def ref(self):
        """Get the reference of the document
        """
        return self._ref
    
    @GObject.Property(type=str)
    def section(self):
        """Get the section of the document
        """
        return self._ref.get_section()
    
    @section.setter
    def section(self, section):
        """Set the section of the document
        """
        self._ref.set_section(section)
    
    @GObject.Property(type=object)
    def sources(self):
        """Get the sources of the document
        """
        return self._handler.get_sources()
    
    @GObject.Property(type=str)
    def title(self):
        """Title of the documment
        """
        return self._ref.documentName

    @GObject.Property(type=str)
    def shortTitle(self):
        """Short title of the documment
        """
        return self._ref.get_short_repr()
    
    @GObject.Property(type=object)
    def toc(self):
        """Get the table of contents of the document
        """
        return self._toc
    
    @GObject.Property(type=int)
    def type(self):
        """Get the type of the document
        """
        return self._ref.type

    @GObject.Property(type=str)
    def uri(self):
        """Get the uri of the document
        """
        return self._ref.get_uri()
