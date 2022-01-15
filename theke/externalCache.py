import logging

import os
import requests
from bs4 import BeautifulSoup

import theke

logger = logging.getLogger(__name__)

PATH_SUFFIX_RAW = '_raw'
PATH_SUFFIX_CLEAN = ''

def is_source_cached(sourceName) -> bool:
    """Return true if a source is cached

    Notice. By default, the cache is in ~/.local/share/theke/cache/.
    """

    if os.path.isfile(get_source_file_path(sourceName, PATH_SUFFIX_RAW)):
        logger.debug("Source found in the cache: %s", sourceName)
        return True

    logger.debug("Source not cached: %s", sourceName)
    return False

def is_cache_cleaned(sourceName) -> bool:
    """Return true if a clean version of the cache exist
    """

    if os.path.isfile(get_source_file_path(sourceName)):
        logger.debug("Clean source found in the cache: %s", sourceName)
        return True

    logger.debug("Source not cleaned: %s", sourceName)
    return False

def cache_document_from_external_source(sourceName, contentUri) -> None:
    """Download and cache the document designated by an external source
    """
    logger.debug("Cache a document from an external source: %s [%s]", sourceName, contentUri)

    path_source = _get_source_path(sourceName)
    path_rawDocument = get_source_file_path(sourceName, PATH_SUFFIX_RAW)

    if not os.path.isdir(path_source):
        os.mkdir(path_source)

    # Get the raw document from the external source
    # and save it to a file
    # cf. https://docs.python-requests.org/en/latest/user/quickstart/#raw-response-content

    r = requests.get(contentUri, stream=True)

    with open(path_rawDocument, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

def get_document(sourceName) -> str:
    """Return the cached document designated by an external source
    """
    logger.debug("Load a document from cache (source = %s)", sourceName)
    return None

###

def _build_clean_document(sourceName, path_rawDocument = None):
    """Build a clean document from a raw one
    """
    path_cleanDocument = get_source_file_path(sourceName)

    if path_rawDocument is None:
        path_rawDocument = get_source_file_path(sourceName, PATH_SUFFIX_RAW)

    with open(path_rawDocument, 'r') as rawFile:
        soup = BeautifulSoup(rawFile, 'html.parser')

    script_content = "body"
    clean_content = soup.select_one(script_content)

    # # Clean things
    # script_content = "div.documento div.text:nth-child(2)"
    # script_h1 = "p[align=center]:nth-child(1)"
    # script_h2 = "p[align=center]:nth-child(n+1)"

    # tags_to_unwrap = ["font"]
    
    # # Get the main content
    # clean_content = soup.select_one(script_content)

    # # Unwrap some tags
    # for tag in clean_content(tags_to_unwrap):
    #     tag.unwrap()

    # # Format the main title
    # tag = clean_content.select_one(script_h1)
    # tag.name = "h1"
    # del tag['align']

    # # Format titles
    # for tag in clean_content.select(script_h2):
    #     if tag.get_text().strip() == '':
    #         tag.decompose()
    #     else:
    #         tag.name = "h2"
    #         del tag['align']

    # Save the clean document
    with open(path_cleanDocument, 'w') as cleanFile:
        cleanFile.write(str(clean_content)) #.prettify()

def _get_source_path(sourceName) -> str:
    return os.path.join(theke.PATH_CACHE, sourceName)

def get_source_file_path(sourceName, suffix = '', relative = False) -> str:
    """Return the absolute path to a source file from the cache

    @param sourceName: (str) name of the source
    @param suffix: (str)    '' --> clean version of the source
                            '_raw' --> raw version of the source
    @param relative: (bool) return the relative path from theke.PATH_CACHE
    """
    if relative:
        return os.path.join(sourceName, "{}{}.html".format(sourceName, suffix))
    else:
        return os.path.join(_get_source_path(sourceName), "{}{}.html".format(sourceName, suffix))

if __name__ == "__main__":
    class theke:
        PATH_CACHE = "/home/antoine/.local/share/theke/cache"

    sourceName = "2016_amoris laetitia"
    path_rawDocument = "/home/antoine/.local/share/theke/cache/2016_amoris laetitia/2016_amoris laetitia_raw.html"
    _build_clean_document(sourceName, path_rawDocument)
