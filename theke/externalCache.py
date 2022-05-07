import logging

import os
import re
import yaml
import requests
import soupsieve
from bs4 import BeautifulSoup, SoupStrainer
from bs4.element import NavigableString

import theke

logger = logging.getLogger(__name__)

PATH_SUFFIX_RAW = '_raw'
PATH_SUFFIX_AUTOMATICALLY_CLEANED = '_auto'
PATH_SUFFIX_MANUALLY_CLEANED = ''

CLEANING_RULES_API_VERSION = 2

def _get_source_definition_path(sourceName) -> str:
    return os.path.join(theke.PATH_EXTERNAL, "{}.yaml".format(sourceName))

def _get_source_path(sourceName) -> str:
    return os.path.join(theke.PATH_CACHE, sourceName)

def _get_source_file_path(sourceName, suffix = '', relative = False) -> str:
    """Return the path to a source file from the cache

    @param sourceName: (str) name of the source
    @param suffix: (str)    '' --> clean version of the source
                            '_raw' --> raw version of the source
    @param relative: (bool) return the relative path from theke.PATH_CACHE
    """
    if relative:
        return os.path.join(sourceName, "{}{}.html".format(sourceName, suffix))
    else:
        return os.path.join(_get_source_path(sourceName), "{}{}.html".format(sourceName, suffix))

def get_best_source_file_path(sourceName, relative = False) -> str:
    """Return the path to to best source file from the cache
    
    A source can exist in different version in the cache
    (from the best to the worst)
    - manually cleaned: the cleaning was manually improved
    - automatically cleaned: the source was automatically cleaned
            according to cleaning rules from the definition file
    """
    if os.path.isfile(_get_source_file_path(sourceName, PATH_SUFFIX_MANUALLY_CLEANED)):
        return _get_source_file_path(sourceName, PATH_SUFFIX_MANUALLY_CLEANED, relative)

    if os.path.isfile(_get_source_file_path(sourceName, PATH_SUFFIX_AUTOMATICALLY_CLEANED)):
        return _get_source_file_path(sourceName, PATH_SUFFIX_AUTOMATICALLY_CLEANED, relative)

    else:
        logger.error("No source file found for %s", sourceName)

def is_source_cached(sourceName) -> bool:
    """Return true if a source is cached

    Notice. By default, the cache is in ~/.local/share/theke/cache/.
    """

    if os.path.isfile(_get_source_file_path(sourceName, PATH_SUFFIX_RAW)):
        logger.debug("Raw source found in the cache: %s", sourceName)
        return True

    logger.debug("Source not cached: %s", sourceName)
    return False

def is_cache_cleaned(sourceName) -> bool:
    """Return true if a clean version of the cache exist
    """

    if os.path.isfile(_get_source_file_path(sourceName, PATH_SUFFIX_MANUALLY_CLEANED)):
        logger.debug("Manually cleaned source found in the cache: %s", sourceName)
        return True

    if os.path.isfile(_get_source_file_path(sourceName, PATH_SUFFIX_AUTOMATICALLY_CLEANED)):
        logger.debug("Automatically cleaned source found in the cache: %s", sourceName)
        return True

    logger.debug("Source not cleaned: %s", sourceName)
    return False

def cache_document_from_external_source(sourceName, contentUri) -> bool:
    """Download and cache the document designated by an external source
    """
    logger.debug("Cache a document from an external source: %s [%s]", sourceName, contentUri)

    path_source = _get_source_path(sourceName)
    path_rawDocument = _get_source_file_path(sourceName, PATH_SUFFIX_RAW)

    if not os.path.isdir(path_source):
        os.mkdir(path_source)

    # Get the raw document from the external source
    # and save it to a file
    # cf. https://docs.python-requests.org/en/latest/user/quickstart/#raw-response-content

    try:
        r = requests.get(contentUri, stream=True, timeout=1)

        with open(path_rawDocument, 'w', encoding="utf-8") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk.decode(r.encoding, 'replace'))

        return True
    
    except requests.ConnectTimeout:
        logger.debug("External source inaccessible, check your internet connection")
        return False
    
    except requests.ConnectionError:
        logger.debug("External source inaccessible, check your internet connection")
        return False

### Layout formatter callbacks

def layout_header_cb(tag, cleanSoup):
    """Layout the header
    """
    new_tag = cleanSoup.new_tag('header')
    content_tag = cleanSoup.new_tag('p')
    content_tag.append(tag.get_text(" ", strip = True))
    new_tag.append(content_tag)

    cleanSoup.main.append(new_tag)
    new_tag.insert_after('\n')

    return new_tag

def layout_hn_cb(tagName, tag, cleanSoup):
    """Layout for titles
    @param tagName: (str) 'h1', 'h2', ...
    """
    new_tag = cleanSoup.new_tag(tagName)
    new_tag.append(tag.get_text(" ", strip = True))

    cleanSoup.main.append(new_tag)
    new_tag.insert_after('\n')

    return new_tag

def layout_h2_cb(tag, cleanSoup):
    return layout_hn_cb('h2', tag, cleanSoup)

def layout_h3_cb(tag, cleanSoup):
    return layout_hn_cb('h3', tag, cleanSoup)

def layout_h4_cb(tag, cleanSoup):
    return layout_hn_cb('h4', tag, cleanSoup)

def layout_p_cb(tag, cleanSoup) -> None:
    new_tag = cleanSoup.new_tag('p')
    new_tag.extend(tag)

    cleanSoup.main.append(new_tag)
    new_tag.insert_after('\n')

    return new_tag

def layout_numbering(soup, tag, params):
    """Add anchor to identify paragraph or section numbering
    """
    pattern_numbering = re.compile(params['pattern'])

    for part in tag.descendants:
        text = part.get_text(" ", strip = True)
        
        match_numbering = pattern_numbering.match(text)

        if match_numbering:
            # If the tag content match the numbering pattern,
            # then add an anchor
            anchorTag = soup.new_tag('span')
            anchorTag.string = "{}.".format(match_numbering.group('number'))
            anchorTag['id'] = match_numbering.group('number')
            anchorTag['class'] = params['class']

            part.replace_with(anchorTag)
            anchorTag.insert_after(pattern_numbering.sub(' \g<text>', text))
            break
        
###

layout_rules_callbacks = {
    'h2': layout_h2_cb,
    'h3': layout_h3_cb,
    'h4': layout_h4_cb,
    'p': layout_p_cb,
    'header': layout_header_cb,
}

def _build_clean_document(sourceName, path_rawDocument = None):
    """Build a clean document from a raw one
    """
    if path_rawDocument is None:
        path_rawDocument = _get_source_file_path(sourceName, PATH_SUFFIX_RAW)
    
    logger.debug("Clean: %s", path_rawDocument)

    # Parse the document from the raw source
    with open(path_rawDocument, 'r') as rawFile:
        rawSoup = BeautifulSoup(rawFile, 'html.parser', parse_only = SoupStrainer("body"))

    # Init the clean document
    cleanSoup = BeautifulSoup('<main></main>', 'html.parser')

    def remove_empty_tags(tag):
        """Recursively remove empty tags"""
        if isinstance(tag, NavigableString):
            return

        if tag.get_text(strip=True) == '':
            tag.decompose()
            return

        for childTag in tag.children:
            remove_empty_tags(childTag)

    def build_clean_tags(tag) -> None:
        """Recursively apply cleaning rules
        """
        if isinstance(tag, NavigableString):
            return

        # Skip empty tags
        if tag.get_text(strip=True) == '':
            return
        
        # Go deeper in the tree
        for childTag in tag.children:
            build_clean_tags(childTag)

        # Check if the tag still have content
        if tag.get_text(strip=True) == '':
            return

        # Check if this tag should be removed
        for selector in cleaning_rules.get('remove', []):
            if soupsieve.match(selector, tag):
                # Note: the tag is not decomposed in order not to disturb
                #       css selectors used in cleaning rules
                tag.clear()
                return

        # Check if this tag matches a cleaning rule
        for rule in cleaning_rules.get('layouts', {}):
            layout = rule.get('name', None)
            options = rule.get('options', {})

            selectors = options.get('selectors', None) or [options.get('selector', '')]

            for selector in selectors:
                if soupsieve.match(selector, tag) and layout in layout_rules_callbacks:
                    # The tag match a cleaning rule
                    # Applies the rule
                    clean_tag = layout_rules_callbacks[layout](tag, cleanSoup)

                    # If specified, add an anchor to the numbering
                    if 'numbering' in options:
                        layout_numbering(cleanSoup, clean_tag, options['numbering'])
                    
                    # Destroy the tag so it will not be parsed another time
                    tag.clear()

                    return

    # Load cleaning rules from the source definition
    path_sourceDefinition = _get_source_definition_path(sourceName)
    externalData = yaml.safe_load(open(path_sourceDefinition, 'r'))
    cleaning_rules = externalData.get('cleaning_rules', None)

    if cleaning_rules is None:
        logger.debug("No cleaning rules in %s", path_sourceDefinition)

        # Get the default main content
        content = rawSoup.body
        remove_empty_tags(content)

        cleanSoup.append(content)
    
    elif cleaning_rules.get('api_version', 0) != CLEANING_RULES_API_VERSION:
        logger.debug("Cleaning rules set with a different api version (rules: %s / needed: %s)",
            cleaning_rules.get('api_version', 0), CLEANING_RULES_API_VERSION)

        # Get the default main content
        content = rawSoup.body
        remove_empty_tags(content)

        cleanSoup.append(content)

    else:
        logger.debug("Use cleaning rules from %s", path_sourceDefinition)

        # Get the main content
        content = rawSoup.select_one(cleaning_rules['content']['selector'])
        build_clean_tags(content)

    # Save the clean document
    path_cleanDocument = _get_source_file_path(sourceName, PATH_SUFFIX_AUTOMATICALLY_CLEANED)
    with open(path_cleanDocument, 'w') as cleanFile:
        cleanFile.write(str(cleanSoup))

if __name__ == "__main__":
    class theke:
        PATH_CACHE = "/home/antoine/.local/share/theke/cache"
        PATH_EXTERNAL = "/home/antoine/.local/share/theke/external"

    logging.basicConfig(level=logging.DEBUG)

    sourceName = "François_amoris laetitia_2016"
    path_rawDocument = "/home/antoine/.local/share/theke/cache/François_amoris laetitia_2016/François_amoris laetitia_2016_raw.html"
    _build_clean_document(sourceName, path_rawDocument)
