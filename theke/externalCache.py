import logging

import os
import yaml
import requests
from bs4 import BeautifulSoup, SoupStrainer
from bs4.element import NavigableString

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
    if path_rawDocument is None:
        path_rawDocument = get_source_file_path(sourceName, PATH_SUFFIX_RAW)
    
    logger.debug("Clean: %s", path_rawDocument)

    # Parse the document from the raw source
    with open(path_rawDocument, 'r') as rawFile:
        soup = BeautifulSoup(rawFile, 'html.parser', parse_only = SoupStrainer("body"))

    def remove_empty_tags(tag):
        """Recursively remove empty tags"""
        if isinstance(tag, NavigableString):
            return

        if tag.get_text(strip=True) == '':
            tag.decompose()
            return

        for childTag in tag.children:
            remove_empty_tags(childTag)

    # Load cleaning rules from the source definition
    path_sourceDefinition = _get_source_definition_path(sourceName)
    externalData = yaml.safe_load(open(path_sourceDefinition, 'r'))
    cleaning_rules = externalData.get('cleaning_rules', None)

    if cleaning_rules is None:
        logger.debug("No cleaning rules in %s", path_sourceDefinition)

        # Get the default main content
        content = soup.body
        remove_empty_tags(content)

    else:
        logger.debug("Use cleaning rules from %s", path_sourceDefinition)

        # Get the main content
        content = soup.select_one(cleaning_rules['content']['selector'])
        remove_empty_tags(content)

        # Apply cleaning rules (version 1)...
        # ... remove some tags
        for rule in cleaning_rules['remove']:
            logger.debug("... remove tag: %s", rule)
            for tag in content.select(rule):
                tag.decompose()

        # ... apply layout rules
        for layout in cleaning_rules['layouts']:
            logger.debug("... apply layout: %s", layout)
            for tag in content.select(cleaning_rules['layouts'][layout]['selector']):
                new_tag = soup.new_tag(layout)
                new_tag.string = tag.get_text(strip = True)
                tag.replace_with(new_tag)

    # Save the clean document
    path_cleanDocument = get_source_file_path(sourceName)
    with open(path_cleanDocument, 'w') as cleanFile:
        cleanFile.write(str(content))

def _get_source_definition_path(sourceName) -> str:
    return os.path.join(theke.PATH_EXTERNAL, "{}.yaml".format(sourceName))

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
        PATH_EXTERNAL = "/home/antoine/.local/share/theke/external"

    logging.basicConfig(level=logging.DEBUG)

    sourceName = "2016_amoris laetitia"
    path_rawDocument = "/home/antoine/.local/share/theke/cache/2016_amoris laetitia/2016_amoris laetitia_raw.html"
    _build_clean_document(sourceName, path_rawDocument)
