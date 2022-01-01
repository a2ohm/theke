import logging
logger = logging.getLogger(__name__)

def is_source_cached(sourceName) -> bool:
    """Return true if a source is cached

    Notice. By default, the cache is in ~/.local/share/theke/cache/.
    """
    logger.debug("This source is not cached: %s", sourceName)
    return False

def cache_document_from_external_source(sourceName, contentUri) -> None:
    """Download and cache the document designated by an external source
    """
    logger.debug("Cache a document from an external source: %s [%s]", sourceName, contentUri)
    return True

def get_document(sourceName) -> str:
    """Return the cached document designated by an external source
    """
    logger.debug("Load a document from cache (source = %s)", sourceName)
    return None