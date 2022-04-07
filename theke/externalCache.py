import logging

import os
import re
import yaml
import requests
from bs4 import BeautifulSoup, SoupStrainer
from bs4.element import NavigableString

import theke

logger = logging.getLogger(__name__)

PATH_SUFFIX_RAW = '_raw'
PATH_SUFFIX_AUTOMATICALLY_CLEANED = '_auto'
PATH_SUFFIX_MANUALLY_CLEANED = ''

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

def layout_h2_cb(soup, tag, params):
    new_tag = soup.new_tag('h2')
    new_tag.string = tag.get_text(strip = True)
    tag.replace_with(new_tag)
    return new_tag

def layout_h3_cb(soup, tag, params):
    new_tag = soup.new_tag('h3')
    new_tag.string = tag.get_text(strip = True)
    tag.replace_with(new_tag)
    return new_tag

def layout_p_cb(soup, tag, params):
    tag.name = 'p'
    tag.insert_after('\n')
    return tag

def layout_numbering(soup, tag, params):
    """Add anchor to identify paragraph or section numbering
    """
    text = tag.get_text(strip = True)
    pattern_numbering = re.compile(params['pattern'])

    match_numbering = pattern_numbering.match(text)

    if match_numbering:
        # If the tag content match the numbering pattern,
        # then add an anchor
        anchorTag = soup.new_tag('span')
        anchorTag.string = "{}.".format(match_numbering.group('number'))
        anchorTag['id'] = match_numbering.group('number')
        anchorTag['class'] = params['class']

        tag.string = pattern_numbering.sub(' \g<text>', text)
        tag.string.insert_before(anchorTag)
        
###

# Layout rules will be applied in this order
layout_rules_callbacks = [
    ('h2', layout_h2_cb),
    ('h3', layout_h3_cb),
    ('p', layout_p_cb)
]

def _build_clean_document(sourceName, path_rawDocument = None):
    """Build a clean document from a raw one
    """
    if path_rawDocument is None:
        path_rawDocument = _get_source_file_path(sourceName, PATH_SUFFIX_RAW)
    
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
        content.name = "main"
        remove_empty_tags(content)

    else:
        logger.debug("Use cleaning rules from %s", path_sourceDefinition)

        # Get the main content
        content_tag = soup.new_tag('main')
        content = soup.select_one(cleaning_rules['content']['selector']).wrap(content_tag)

        remove_empty_tags(content)

        # Apply cleaning rules (version 1)...
        # ... remove some tags
        for rule in cleaning_rules.get('remove', []):
            logger.debug("... remove tag: %s", rule)
            for tag in content.select(rule):
                tag.decompose()

        # ... unwrap some tags
        for rule in cleaning_rules.get('unwrap', []):
            logger.debug("... unwrap tag: %s", rule)
            for tag in content.select(rule):
                tag.unwrap()

        # ... apply layout rules
        for layout, callback in layout_rules_callbacks:
            rules = cleaning_rules['layouts'].get(layout, None)

            if rules:
                logger.debug("... apply layout: %s", layout)

                # In the layout rules, it is valid to give one selector ...
                #   selector: p[align=left]
                # ... or a list of them
                #   selectors:
                #       - p[align=left]
                #       - p[align=right]
                selectors = rules.get('selectors', None) or [rules.get('selector', None)]

                for selector in selectors:
                    for tag in content.select(selector):
                        new_tag = callback(soup, tag, rules)

                        # If specified, add an anchor to the numbering
                        if 'numbering' in rules.keys():
                            layout_numbering(soup, new_tag, rules['numbering'])

    # Save the clean document
    path_cleanDocument = _get_source_file_path(sourceName, PATH_SUFFIX_AUTOMATICALLY_CLEANED)
    with open(path_cleanDocument, 'w') as cleanFile:
        cleanFile.write(str(content))

if __name__ == "__main__":
    class theke:
        PATH_CACHE = "/home/antoine/.local/share/theke/cache"
        PATH_EXTERNAL = "/home/antoine/.local/share/theke/external"

    logging.basicConfig(level=logging.DEBUG)

    sourceName = "2016_amoris laetitia"
    path_rawDocument = "/home/antoine/.local/share/theke/cache/2016_amoris laetitia/2016_amoris laetitia_raw.html"
    _build_clean_document(sourceName, path_rawDocument)
