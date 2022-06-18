from collections import namedtuple
from typing import Any

import logging
import os
import sqlite3
from sqlite3.dbapi2 import Cursor
import yaml

import Sword
import theke
import theke.sword

logger = logging.getLogger(__name__)

SourceData = namedtuple('SourceData',['name', 'type', 'contentType', 'lang', 'description'])
DocumentData = namedtuple('documentData',['name', 'type'])
ExternalDocumentData = namedtuple('externalDocumentData',['name', 'uri'])

SOURCETYPE_SWORD = 'sword'
SOURCETYPE_EXTERN = 'extern'

NEEDED_API_VERSION = "0.4"
INDEX_PATH = os.path.join(theke.PATH_DATA, 'thekeIndex.db')

class ThekeIndex:
    """Helper to use the index of Theke
    """
    def __init__(self) -> None:
        logger.debug("ThekeIndex - Create a new instance")
        logger.debug("ThekeIndex - Connect to the database: %s", INDEX_PATH)
        self.con = sqlite3.connect(INDEX_PATH)

    def execute(self, sql, parameters = ()) -> Cursor:
        """Execute a sql query
        """

        return self.con.execute(sql, parameters)

    def execute_returning_id(self, sql, parameters = ()) -> Any:
        """Insert an entry and return the row id
        """

        cur = self.con.cursor()
        cur.execute(sql, parameters)
        #self.con.commit()

        return cur.lastrowid

    def commit(self) -> None:
        """Commit modifications
        """
        self.con.commit()

    def get_from_header(self, key, default = None) -> str:
        """Return a value from the header"""

        # The header table hasn't always existed
        doHeaderExists = self.con.execute("""SELECT name FROM sqlite_master
            WHERE type='table' AND name='header';""").fetchone()

        if doHeaderExists is not None:
            rawValue = self.con.execute("""SELECT value
                FROM header
                WHERE key=?;""",
                (key,)).fetchone()

            if rawValue is not None:
                return rawValue[0]

        return default

    def get_api_version(self) -> str:
        """Return the API version of the index from the header table
        """

        return self.get_from_header('api_version', '0')

    def get_biblical_book_names(self, bookName) -> Any:
        """From a name of a biblical book, return all other names
        """

        bookId = self.get_document_id(bookName)
        rawNames = self.con.execute("""SELECT name, isShortName
            FROM biblicalBookNames
            WHERE id_document=?;""",
            (bookId,)).fetchall()

        return {'names': [n[0] for n in rawNames if not n[1]],
                'shortnames': [n[0] for n in rawNames if n[1]]}

    def get_biblical_book_nbOfChapters(self, documentName) -> int:
        """Return the number of chapters in the biblical book given its name
        """

        rawNbOfChapters = self.con.execute("""SELECT nbOfChapters
            FROM biblicalBookData
            INNER JOIN documentNaming ON biblicalBookData.id_document = documentNaming.id_document
            WHERE documentNaming.name=?;""",
            (documentName,)).fetchone()

        return -1 if rawNbOfChapters is None else rawNbOfChapters[0]
    
    def get_biblical_book_testament(self, documentName) -> int:
        """Return the testamet id of a biblical book given its name
        """

        rawTestament = self.con.execute("""SELECT testament
            FROM biblicalBookData
            INNER JOIN documentNaming ON biblicalBookData.id_document = documentNaming.id_document
            WHERE documentNaming.name=?;""",
            (documentName,)).fetchone()

        return -1 if rawTestament is None else rawTestament[0]

    def get_document_id(self, documentName) -> int:
        """Return the id of document given its name
        """

        rawId = self.con.execute("""SELECT id_document
            FROM documentNaming
            WHERE name=?;""",
            (documentName,)).fetchone()

        return -1 if rawId is None else rawId[0]

    def get_document_names(self, documentName) -> Any:
        """From a name of a document, return all other names
        """

        documentId = self.get_document_id(documentName)
        rawNames = self.con.execute("""SELECT name, abbreviation
            FROM documentNames
            WHERE id_document=?;""",
            (documentId,)).fetchall()

        return {'names': [n[0] for n in rawNames],
                'shortnames': [n[1] for n in rawNames if n[1] != ""]}

    def get_document_type(self, documentName) -> int:
        """Return the type of a document given its name
        """

        rawTypes = self.con.execute("""SELECT type
            FROM documents
            INNER JOIN documentNaming ON documents.id = documentNaming.id_document
            WHERE documentNaming.name=?;""",
            (documentName,)).fetchone()

        return -1 if rawTypes is None else rawTypes[0]

    def get_edition_id(self, editionName) -> int:
        """Return the id of an edition given its name
        """

        rawId = self.con.execute("""SELECT id
            FROM editions
            WHERE name=?;""",
            (editionName,)).fetchone()

        return -1 if rawId is None else rawId[0]

    def get_source_data(self, sourceName) -> SourceData:
        """Return all data about a source
        """

        rawSourceData = self.con.execute("""SELECT sources.name, sources.type, sources.contentType, sources.lang, sourceDescriptions.description
            FROM sources
            LEFT JOIN sourceDescriptions ON sources.id = sourceDescriptions.id_source
            WHERE sources.name =?;""",
            (sourceName,)).fetchone()

        return SourceData._make(rawSourceData)

    def get_source_version(self, sourceName) -> str:
        """Return the version a source
        """

        rawVersion = self.con.execute("""SELECT version
            FROM sources
            WHERE name=?;""",
            (sourceName,)).fetchone()

        return '0' if rawVersion is None else rawVersion[0]

    def get_source_type(self, sourceName) -> str:
        """Return the type of a source
        """

        rawType = self.con.execute("""SELECT type
            FROM sources
            WHERE name=?;""",
            (sourceName,)).fetchone()

        return None if rawType is None else rawType[0]

    def get_source_uri(self, sourceName) -> str:
        """Return the uri of a source
        """

        rawUri = self.con.execute("""SELECT uri
            FROM sources
            WHERE name=?;""",
            (sourceName,)).fetchone()

        return None if rawUri is None else rawUri[0]

    def list_sources(self, sourceType = None, contentType = None):
        """List sources

        @param sourceType: SOURCETYPE_SWORD
        @param contentType: MODTYPE_BIBLES, MODTYPE_GENBOOKS
        """
        if sourceType is None and contentType is None:
            rawSourcesData = self.con.execute("""SELECT sources.name, sources.type, sources.contentType, sourceDescriptions.description
                FROM sources
                LEFT JOIN sourceDescriptions ON sources.id = sourceDescriptions.id_source;""")

        elif sourceType is None:
            rawSourcesData = self.con.execute("""SELECT sources.name, sources.type, sources.contentType, sourceDescriptions.description
                FROM sources
                LEFT JOIN sourceDescriptions ON sources.id = sourceDescriptions.id_source
                WHERE sources.contentType=?;""",
                (contentType,))

        elif contentType is None:
            rawSourcesData = self.con.execute("""SELECT sources.name, sources.type, sources.contentType, sourceDescriptions.description
                FROM sources
                LEFT JOIN sourceDescriptions ON sources.id = sourceDescriptions.id_source
                WHERE sources.type=?;""",
                (sourceType,))

        else:
            rawSourcesData = self.con.execute("""SELECT sources.name, sources.type, sources.contentType, sources.lang, sourceDescriptions.description
                FROM sources
                LEFT JOIN sourceDescriptions ON sources.id = sourceDescriptions.id_source
                WHERE sources.type =? AND sources.contentType=?;""",
                (sourceType, contentType))

        for rawSourceData in rawSourcesData:
            yield SourceData._make(rawSourceData)

    def list_documents(self):
        """List all documents
        """

        rawDocumentsData = self.con.execute("""SELECT documentNaming.name, documents.type
                FROM documentNaming
                INNER JOIN documents ON documentNaming.id_document = documents.id;""")

        for rawDocumentData in rawDocumentsData:
            yield DocumentData._make(rawDocumentData)

    def list_documents_by_type(self, documentType):
        """List documents by type

        @param documentType: theke.TYPE_BOOK, theke.TYPE_BIBLE
        """

        rawDocumentsData = self.con.execute("""SELECT documentNaming.name, documents.type
                FROM documentNaming
                INNER JOIN documents ON documentNaming.id_document = documents.id
                WHERE documents.type = ?;""",
                (documentType,))

        for rawDocumentData in rawDocumentsData:
            yield DocumentData._make(rawDocumentData)

    def list_external_documents(self):
        """List external documents
        """

        rawDocumentsData = self.con.execute("""SELECT documentNames.name, sources.uri
                FROM documentNames
                INNER JOIN link_document_source ON link_document_source.id_document = documentNames.id_document
                INNER JOIN sources ON sources.id = link_document_source.id_source
                WHERE sources.type = ?;""",
                (SOURCETYPE_EXTERN,))

        for rawDocumentData in rawDocumentsData:
            yield ExternalDocumentData._make(rawDocumentData)

    def list_document_sources(self, documentName) -> Any:
        """List sources where a document can be found
        """

        documentId = self.get_document_id(documentName)

        rawSourcesData = self.con.execute("""SELECT sources.name, sources.type, sources.contentType, sources.lang, sourceDescriptions.description
            FROM sources
            LEFT JOIN sourceDescriptions ON sources.id = sourceDescriptions.id_source
            INNER JOIN link_document_source ON link_document_source.id_source = sources.id
            WHERE link_document_source.id_document = ?;""",
            (documentId,)).fetchall()

        for rawSourceData in rawSourcesData:
            yield SourceData._make(rawSourceData)

class ThekeIndexBuilder:
    """Helper the build the index of Theke
    """
    def __init__(self) -> None:
        logger.debug("ThekeIndexBuilder - Create a new instance")
        self.index = ThekeIndex()

        currentApiVersion = self.index.get_api_version()

        if currentApiVersion >= NEEDED_API_VERSION:
            return

        logger.debug("ThekeIndexBuilder - Initiate the database from scratch")

        # Header
        self.index.execute("""DROP TABLE IF EXISTS header""")
        self.index.execute("""CREATE TABLE IF NOT EXISTS header (
            key text NOT NULL,
            value text NOT NULL
            );""")

        self.index.execute("""INSERT INTO header (key, value) VALUES(?, ?);""",
            ("api_version", NEEDED_API_VERSION))

        self.index.commit()

        # Documents
        self.index.execute("""CREATE TABLE IF NOT EXISTS documents (
            id integer PRIMARY KEY,
            type integer NOT NULL
            );""")

        #   - document naming
        self.index.execute("""CREATE TABLE IF NOT EXISTS documentNaming (
            id_document integer NOT NULL,
            name text NOT NULL,
            FOREIGN KEY(id_document) REFERENCES documents(id) ON DELETE CASCADE
            );""")

        #   - document names
        self.index.execute("""CREATE TABLE IF NOT EXISTS documentNames (
            id_document integer NOT NULL,
            name text NOT NULL,
            abbreviation text DEFAULT "",
            lang text NOT NULL,
            FOREIGN KEY(id_document) REFERENCES documents(id) ON DELETE CASCADE
            );""")

        #   - document descriptions
        self.index.execute("""CREATE TABLE IF NOT EXISTS documentDescriptions (
            id_document integer NOT NULL,
            description text NOT NULL,
            lang text NOT NULL,
            FOREIGN KEY(id_document) REFERENCES documents(id) ON DELETE CASCADE
            );""")

        # Biblical documents
        #   - book names
        self.index.execute("""CREATE TABLE IF NOT EXISTS biblicalBookNames (
            id_document integer NOT NULL,
            name text NOT NULL,
            isShortname integer NOT NULL DEFAULT 0,
            lang text NOT NULL,
            norm text DEFAULT ""
            );""")

        #   - book data
        self.index.execute("""DROP TABLE IF EXISTS biblicalBookData""")
        self.index.execute("""CREATE TABLE IF NOT EXISTS biblicalBookData (
            id_document integer NOT NULL,
            nbOfChapters integer NOT NULL,
            testament integer NOT NULL,
            FOREIGN KEY(id_document) REFERENCES documents(id) ON DELETE CASCADE
            );""")

        # ... sources
        self.index.execute("""DROP TABLE IF EXISTS sources""")
        self.index.execute("""CREATE TABLE IF NOT EXISTS sources (
            id integer PRIMARY KEY,
            name text UNIQUE NOT NULL,
            type text NOT NULL,
            contentType text NOT NULL,
            version text DEFAULT "0",
            lang text NOT NULL,
            uri text DEFAULT ""
            );""")

        # ... sourceDescriptions
        self.index.execute("""CREATE TABLE IF NOT EXISTS sourceDescriptions (
            id_source integer NOT NULL,
            description text NOT NULL,
            lang text DEFAULT "en",
            FOREIGN KEY(id_source) REFERENCES sources(id) ON DELETE CASCADE
            );""")

        # ... link_document_source
        self.index.execute("""CREATE TABLE IF NOT EXISTS link_document_source (
            id_document integer NOT NULL,
            id_source integer NOT NULL,
            uri_document text NOT NULL DEFAULT "",
            FOREIGN KEY(id_document) REFERENCES documents(id) ON DELETE CASCADE
            FOREIGN KEY(id_source) REFERENCES sources(id) ON DELETE CASCADE
            );""")

    ### Index building

    def build(self, force = False) -> None:
        """Build the index.
        """
        self.index_sword_modules(force)
        self.index_external_sources(force)

    def index_sword_modules(self, force = False) -> None:
        """Index sword modules.
        """
        logger.debug("ThekeIndexBuilder − Index sword modules")
        swordLibrary = theke.sword.SwordLibrary()

        self.index_sword_biblical_book_names()

        # Index each sword module
        for moduleName, mod in swordLibrary.get_modules():
            if force or (mod.get_version() > self.index.get_source_version(moduleName)):
                self.index_sword_module(mod)

    def index_external_sources(self, force = False) -> None:
        """Index external sources
        """
        logger.debug("ThekeIndexBuilder − Index external sources")

        for externalFilename in os.listdir(theke.PATH_EXTERNAL):
            if externalFilename.endswith('.yaml'):
                externalSourceName = externalFilename[:-5]
                externalPath = os.path.join(theke.PATH_EXTERNAL, externalFilename)
                externalData = yaml.safe_load(open(externalPath, 'r'))

                if force or (str(externalData['version']) > self.index.get_source_version(externalSourceName)):
                    self.index_external_source(externalSourceName, externalData)

    ### Index sword modules

    def index_sword_module(self, mod) -> None:
        """Index a sword module
        """

        logger.debug("ThekeIndexBuilder - Index %s", mod.get_name())

        # Add the module to the index
        sourceId = self.add_source(mod.get_name(), SOURCETYPE_SWORD, mod.get_type(),
            mod.get_version(), mod.get_lang())

        if sourceId is None:
            raise sqlite3.Error("Fails to index the module {}".format(mod.get_name()))

        # Add the module description to the index
        self.index.execute_returning_id("""INSERT INTO sourceDescriptions (id_source, description)
                VALUES(?, ?);
                """,
            (sourceId, mod.get_description()))

        self.index.commit()

        # Next indexing steps depend of the module type
        if mod.get_type() == theke.sword.MODTYPE_BIBLES:
            self.index_sword_biblical_module(sourceId, mod)

        elif mod.get_type() == theke.sword.MODTYPE_GENBOOKS:
            self.index_sword_book_module(sourceId, mod)

        else:
            logger.debug("ThekeIndexBuilder - Unknown type (%s) of %s", mod.get_type(), mod.get_name())

    def index_sword_biblical_book_names(self) -> None:
        """Index sword biblical book names.

        Sword use some names to designate biblibal books.
        Index them once for all.
        """

        if self.index.get_from_header('are_sword_biblical_books_indexed', "no") == "yes":
            logger.debug("ThekeIndexBuilder − Index sword biblical book names [skip]")
            return

        logger.debug("ThekeIndexBuilder − Index sword biblical book names")

        # Index names used by sword for biblical books
        vk = Sword.VerseKey()

        for itestament in [theke.BIBLE_OT, theke.BIBLE_NT]:
            vk.setTestament(itestament)

            for ibook in range(1, vk.getBookMax() +1):
                vk.setBook(ibook)

                # Create a new biblical book entry
                documentId = self.index.execute_returning_id("""INSERT INTO documents  (type)
                    VALUES(?);""", (theke.TYPE_BIBLE,))

                # Index the biblical book name
                self.index_biblical_book_name(documentId, vk.getBookName(), "en", "sword", doCommit = False)

                # Index the number of chapters and the testament
                self.index.execute("""INSERT OR IGNORE INTO biblicalBookData (id_document, nbOfChapters, testament)
                    VALUES(?, ?, ?);""",
                    (documentId, vk.getChapterMax(), itestament))

        self.index.execute("""INSERT INTO header (key, value) VALUES(?, ?);""",
            ("are_sword_biblical_books_indexed", "yes"))

        self.index.commit()

    def index_sword_biblical_module(self, sourceId, mod) -> None:
        """Index a sword biblical module
        """

        logger.debug("ThekeIndexBuilder - Index %s as a Bible (id: %s)", mod.get_name(), sourceId)

        # Index each of the biblical books of this module
        # TODO: Y a-t-il une façon plus propre de faire la même chose ?
        vk = Sword.VerseKey()

        for itestament in [1, 2]:
            vk.setTestament(itestament)

            for ibook in range(1, vk.getBookMax() +1):
                vk.setBook(ibook)
                if mod.has_entry(vk):
                    bookId = self.index.get_document_id(vk.getBookName())
                    self.link_biblical_book(vk.getBookName(), bookId, sourceId, doCommit=False)

        self.index.commit()

    def index_sword_book_module(self, sourceId, mod) -> None:
        """Index a sword book module
        """
        logger.debug("ThekeIndexBuilder - Index %s as a book (id: %s)", mod.get_name(), sourceId)

        # TODO: boucler sur les titres des livres contenus dans ce module.
        self.index_document(mod.get_name(), mod.get_short_repr(), theke.TYPE_BOOK, None, mod.get_lang(), sourceId, "", doCommit=True)

    ### Index exernal source

    def index_external_source(self, sourceName, data) -> None:
        """Index an external source
        """
        logger.debug("ThekeIndexBuilder - Index %s as an external source", sourceName)

        # Add the external source to the index
        sourceId = self.add_source(sourceName, SOURCETYPE_EXTERN, "",
            data['version'], data['lang'], data['uri'])

        if sourceId is None:
            raise sqlite3.Error("Fails to index the external source {}".format(sourceName))

        # Add the module description to the index
        self.index.execute_returning_id("""INSERT INTO sourceDescriptions (id_source, description)
                VALUES(?, ?);
                """,
            (sourceId, data['description']))

        # Index the document
        self.index_document(data['name'], data['shortname'], theke.TYPE_BOOK, data.get('description', None), data['lang'], sourceId, data['uri'])

    ### Index documents

    def index_biblical_book_name(self, documentId, name, lang, norm = "", isShortName = False, doCommit = True) -> None:
        """Index a biblical book name

        @param name: (str) name of the biblical book
        """

        self.index.execute("""INSERT INTO documentNaming (id_document, name)
            VALUES(?, ?);""",
            (documentId, name))

        if isShortName:
            # and index its name as a short name
            self.index.execute("""INSERT INTO biblicalBookNames (id_document, name, norm, lang, isShortName)
                VALUES(?, ?, ?);""",
                (documentId, name, norm, lang, True))
        else:
            # and index its name
            self.index.execute("""INSERT INTO biblicalBookNames (id_document, name, norm, lang)
                VALUES(?, ?, ?, ?);""",
                (documentId, name, norm, lang))

        if doCommit:
            self.index.commit()

        return documentId

    def link_biblical_book(self, uri, documentId, sourceId, doCommit = True) -> None:
        """Link a source to a biblical book

        @param uri: (str) id to get this book from the source (for sword modules, this is the sword book name)
        @param bookId: (int) id of the biblical book
        @param sourceId: (int) id of the source
        """

        self.index.execute("""INSERT OR IGNORE INTO link_document_source (id_document, id_source, uri_document)
                VALUES(?, ?, ?);""",
            (documentId, sourceId, uri))

        if doCommit:
            self.index.commit()

    def index_document(self, name, shortname, type, description, lang, sourceId, uri, doCommit = True) -> None:
        """Index a document

        @param name: (str) name of the document
        @param shortName: (str) shortname of the document (eg. abbreviation of its title)
        @param sourceId: (int) id of the source
        """
        # Is this document already registered?
        documentId = self.index.get_document_id(name)

        if documentId < 0:
            # No, so create a new document entry
            documentId = self.index.execute_returning_id("""INSERT INTO documents (type) VALUES(?);""", (type,))

            self.index.execute("""INSERT INTO documentNaming (id_document, name)
                    VALUES(?, ?);""",
                    (documentId, name))

            if shortname is not None:
                # and index its name
                self.index.execute("""INSERT INTO documentNames (id_document, name, abbreviation, lang)
                    VALUES(?, ?, ?, ?);""",
                    (documentId, name, shortname, lang))

            else:
                self.index.execute("""INSERT INTO documentNames (id_document, name, lang)
                    VALUES(?, ?, ?);""",
                    (documentId, name, lang))

        # Index its description
        # TODO: indexer correctement la langue de la description
        if description is not None:
            self.index.execute("""INSERT OR IGNORE INTO documentDescriptions (id_document, description, lang)
                    VALUES(?, ?, ?);""",
                (documentId, description, ''))

        self.index.execute("""INSERT OR IGNORE INTO link_document_source (id_document, id_source, uri_document)
                VALUES(?, ?, ?);""",
            (documentId, sourceId, uri))

        if doCommit:
            self.index.commit()

    ### Helpers
    def add_source(self, name, sourceType, contentType, version, lang, uri = '') -> Any:
        """Add a source to the index.

        Note. This can be done in on sql query using the ON CONFLICT syntax. But this is not
                compatible with versions of sqlite earlier than 3.24.0.

                INSERT INTO sources (name, type, contentType, version, lang, uri)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(name)
                DO UPDATE SET version=excluded.version;
        """
        # Does the source already exist?
        rawSourceId = self.index.execute("""SELECT id
            FROM sources
            WHERE name=?;""",
            (name,)).fetchone()

        if rawSourceId is not None:
            print('Update the source version ...')
            return self.index.execute_returning_id("""UPDATE sources
                SET version = ?
                WHERE id = ?;""",
            (version, rawSourceId[0]))

        # Add the module to the index
        return self.index.execute_returning_id("""INSERT INTO sources (name, type, contentType, version, lang, uri)
                VALUES(?, ?, ?, ?, ?, ?);""",
            (name, sourceType, contentType, version, lang, uri))
