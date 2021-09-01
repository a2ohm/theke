"""
Some constants
"""

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

# Paths
PATH_ROOT = os.path.join(GLib.get_user_data_dir(), 'theke')
PATH_DATA = os.path.join(PATH_ROOT, 'data')
PATH_EXTERNAL = os.path.join(PATH_ROOT, 'external')
