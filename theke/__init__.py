"""
Some constants
"""

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

import os
from gi.repository import GLib

# URI
URI_WELCOME = "theke:/app/welcome"

# Valid types of documents
TYPE_UNKNOWN = 0
TYPE_BIBLE = 1
TYPE_BOOK = 2
TYPE_INAPP = 3
TYPE_WEBPAGE = 4

# Testament
BIBLE_OT = 1
BIBLE_NT = 2

# Errors
class NavigationErrors:
    EXTERNAL_SOURCE_INACCESSIBLE = 0
    DOCUMENT_UNKNOWN = 1

# Paths
PATH_ROOT = os.path.join(GLib.get_user_data_dir(), 'theke')
PATH_DATA = os.path.join(PATH_ROOT, 'data')
PATH_EXTERNAL = os.path.join(PATH_ROOT, 'external')
PATH_CACHE = os.path.join(PATH_ROOT, 'cache')

PATH_SETTINGS_FILE = os.path.join(PATH_ROOT, 'theke.conf')

PATH_CUSTOM_CSS = './assets/css/custom.css'