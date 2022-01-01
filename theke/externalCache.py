import logging

import os
import requests

import theke

logger = logging.getLogger(__name__)

def is_source_cached(sourceName) -> bool:
    """Return true if a source is cached

    Notice. By default, the cache is in ~/.local/share/theke/cache/.
    """

    if os.path.isfile(_get_document_path(sourceName)):
        logger.debug("Source found in the cache: %s", sourceName)
        return True

    logger.debug("Source not cached: %s", sourceName)
    return False

def cache_document_from_external_source(sourceName, contentUri) -> None:
    """Download and cache the document designated by an external source
    """
    logger.debug("Cache a document from an external source: %s [%s]", sourceName, contentUri)

    path_source = _get_source_path(sourceName)
    path_rawDocument = _get_document_path(sourceName, '_raw')

    if not os.path.isdir(path_source):
        os.mkdir(path_source)

    # Get the raw document from the external source
    # and save it to a file
    # cf. https://docs.python-requests.org/en/latest/user/quickstart/#raw-response-content

    r = requests.get(contentUri, stream=True)

    with open(path_rawDocument, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

    # Build a clean document from the raw one
    _build_clean_document(sourceName, path_rawDocument)

def get_document(sourceName) -> str:
    """Return the cached document designated by an external source
    """
    logger.debug("Load a document from cache (source = %s)", sourceName)
    return None

###

def _build_clean_document(sourceName, path_rawDocument):
    """Build a clean document from a raw one
    """
    path_cleanDocument = _get_document_path(sourceName)

    with open(path_rawDocument, 'r') as rawFile:
        with open(path_cleanDocument, 'w') as cleanFile:
            # Clean with BeautifulSoup
            pass

def _get_source_path(sourceName) -> str:
    return os.path.join(theke.PATH_CACHE, sourceName)

def _get_document_path(sourceName, suffix = '') -> str:
    return os.path.join(_get_source_path(sourceName), "{}{}.html".format(sourceName, suffix))
