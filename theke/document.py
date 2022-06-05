from gi.repository import Gio
from gi.repository import GObject

import logging
logger = logging.getLogger(__name__)

class ThekeDocument():
    def __init__(self, ref, handler) -> None:
        self._ref = ref
        self._handler = handler

    @GObject.Property(
        type=Gio.InputStream, default=None, flags=GObject.ParamFlags.READABLE)
    def inputStream(self):
        """Get an inputStream to read the document from.
        """
        return self._handler.get_input_stream()

class FileHandler():
    def __init__(self, filePath) -> None:
        self._filePath = filePath

    def get_input_stream(self):
        return Gio.File.new_for_path(self._filePath)
