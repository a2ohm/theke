from collections import namedtuple
from typing import Any

import logging
import sqlite3
from sqlite3.dbapi2 import Cursor

import Sword
import theke
import theke.sword

logger = logging.getLogger(__name__)

SourceData = namedtuple('SourceData',['name', 'type', 'contentType', 'description'])
DocumentData = namedtuple('documentData',['name', 'type'])

SOURCETYPE_SWORD = 'sword'

INDEX_PATH = 'data/thekeIndex.db'

class ThekeIndex:
    def __init__(self) -> None:
        logger.debug("ThekeIndex - Create a new instance")
        logger.debug("ThekeIndex - Connect to the database")
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

    def get_document_id(self, documentName) -> int:
        """Return the id of document given its name
        """

        rawId = self.con.execute("""SELECT id_document
            FROM documentNames
            WHERE name=?;""",
            (documentName,)).fetchone()

        return -1 if rawId is None else rawId[0]

    def get_document_nbOfSections(self, documentName) -> int:
        """Return the number of sections of document given its name

         - For a biblical book, this is the number of chapters.
        """

        rawNbOfSections = self.con.execute("""SELECT nbOfSections
            FROM documents
            INNER JOIN documentNames ON documents.id = documentNames.id_document
            WHERE documentNames.name=?;""",
            (documentName,)).fetchone()

        return -1 if rawNbOfSections is None else rawNbOfSections[0]

    def get_document_type(self, documentName) -> int:
        """Return the type of a document given its name
        """

        rawTypes = self.con.execute("""SELECT type
            FROM documents
            INNER JOIN documentNames ON documents.id = documentNames.id_document
            WHERE documentNames.name=?;""",
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

    def get_source_version(self, sourceName) -> str:
        """Return the version a source
        """

        rawVersion = self.con.execute("""SELECT version
            FROM sources
            WHERE name=?;""",
            (sourceName,)).fetchone()

        return '0' if rawVersion is None else rawVersion[0]

    def list_sources(self, sourceType = None, contentType = None):
        """List sources
        
        @param sourceType: SOURCETYPE_SWORD
        @param contentType: MODTYPE_BIBLES, MODTYPE_GENBOOKS
        """
        if sourceType is None and contentType is None:
            rawSourcesData = self.con.execute("""SELECT sources.name, sources.type, sources.contentType, sourceDescriptions.description
                FROM sources
                INNER JOIN sourceDescriptions ON sources.id = sourceDescriptions.id_source;""")

        elif sourceType is None:
            rawSourcesData = self.con.execute("""SELECT sources.name, sources.type, sources.contentType, sourceDescriptions.description
                FROM sources
                INNER JOIN sourceDescriptions ON sources.id = sourceDescriptions.id_source
                WHERE sources.contentType=?;""",
                (contentType,))

        elif contentType is None:
            rawSourcesData = self.con.execute("""SELECT sources.name, sources.type, sources.contentType, sourceDescriptions.description
                FROM sources
                INNER JOIN sourceDescriptions ON sources.id = sourceDescriptions.id_source
                WHERE sources.type=?;""",
                (sourceType,))

        else:
            rawSourcesData = self.con.execute("""SELECT sources.name, sources.type, sources.contentType, sourceDescriptions.description
                FROM sources
                INNER JOIN sourceDescriptions ON sources.id = sourceDescriptions.id_source
                WHERE sources.type =? AND sources.contentType=?;""",
                (sourceType, contentType))

        for rawSourceData in rawSourcesData:
            yield SourceData._make(rawSourceData)

    def list_documents(self):
        """List all documents
        """

        rawDocumentsData = self.con.execute("""SELECT documentNames.name, documents.type
                FROM documentNames
                INNER JOIN documents ON documentNames.id_document = documents.id;""")

        for rawDocumentData in rawDocumentsData:
            yield DocumentData._make(rawDocumentData)

    def list_document_sources(self, documentName) -> Any:
        """List sources where a document can be found
        """

        documentId = self.get_document_id(documentName)
        rawDocumentSources = self.con.execute("""SELECT sources.name
            FROM sources
            INNER JOIN link_document_source ON link_document_source.id_source = sources.id
            WHERE link_document_source.id_document = ?;""",
            (documentId,)).fetchall()

        return [rawDocumentSource[0] for rawDocumentSource in rawDocumentSources]

class ThekeIndexBuilder:
    def __init__(self) -> None:
        logger.debug("ThekeIndexBuilder - Create a new instance")
        self.index = ThekeIndex()

        logger.debug("ThekeIndexBuilder - Initiate the database (if necessary)")
        # ... documents
        self.index.execute("""CREATE TABLE IF NOT EXISTS documents (
            id integer PRIMARY KEY,
            type integer NOT NULL,
            nbOfSections DEFAULT 0
            );""")

        # ... documentDescriptions
        self.index.execute("""CREATE TABLE IF NOT EXISTS documentDescriptions (
            id_document integer NOT NULL,
            description text NOT NULL,
            lang text NOT NULL,
            FOREIGN KEY(id_document) REFERENCES documents(id) ON DELETE CASCADE
            );""")

        # ... sources
        self.index.execute("""CREATE TABLE IF NOT EXISTS sources (
            id integer PRIMARY KEY,
            name text UNIQUE NOT NULL,
            type text NOT NULL,
            contentType text NOT NULL,
            version text DEFAULT "0"
            );""")

        # ... sourceDescriptions
        self.index.execute("""CREATE TABLE IF NOT EXISTS sourceDescriptions (
            id_source integer NOT NULL,
            description text NOT NULL,
            lang text DEFAULT "en",
            FOREIGN KEY(id_source) REFERENCES sources(id) ON DELETE CASCADE
            );""")

        # ... editions
        self.index.execute("""CREATE TABLE IF NOT EXISTS editions (
            id integer PRIMARY KEY,
            name text UNIQUE NOT NULL,
            shortname text NOT NULL,
            lang text NOT NULL
            );""")

        # documentsNames
        self.index.execute("""CREATE TABLE IF NOT EXISTS documentNames (
            id_document integer NOT NULL,
            id_edition integer NOT NULL,
            name text NOT NULL,
            isShortname integer NOT NULL DEFAULT 0,
            FOREIGN KEY(id_document) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY(id_edition) REFERENCES editions(id) ON DELETE CASCADE
            );""")

        # ... link_document_source
        self.index.execute("""CREATE TABLE IF NOT EXISTS link_document_source (
            id_document integer NOT NULL,
            id_source integer NOT NULL,
            FOREIGN KEY(id_document) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY(id_source) REFERENCES sources(id) ON DELETE CASCADE
            );""")

    def build(self, force = False) -> None:
        """Build the index.
        """
        swordLibrary = theke.sword.SwordLibrary()

        self.index.execute("""INSERT OR IGNORE INTO editions (name, shortname, lang)
                VALUES(?, ?, ?);""",
            ("sword", "sword", ""))

        swordEditionId = self.index.get_edition_id("sword")

        for moduleName, mod in swordLibrary.get_modules():
            if force or (mod.get_version() > self.index.get_source_version(moduleName)):
                self.index_sword_module(swordEditionId, mod)

    def index_sword_module(self, swordEditionId, mod) -> None:
        """Index a sword module
        """

        logger.debug("ThekeIndexBuilder - Index %s", mod.get_name())

        # Add the module in the index
        sourceId = self.index.execute_returning_id("""INSERT INTO sources (name, type, contentType, version)
                VALUES(?, ?, ?, ?) 
                ON CONFLICT(name)
                DO UPDATE SET version=excluded.version;""",
            (mod.get_name(), SOURCETYPE_SWORD, mod.get_type() ,mod.get_version()))

        if sourceId is None:
            raise sqlite3.Error("Fails to index the module {}".format(mod.get_name()))

        # Add the module description in the index
        self.index.execute_returning_id("""INSERT INTO sourceDescriptions (id_source, description)
                VALUES(?, ?);
                """,
            (sourceId, mod.get_description()))

        self.index.commit()

        # Next indexing steps depend of the module type
        if mod.get_type() == theke.sword.MODTYPE_BIBLES:
            self.index_biblical_module(swordEditionId, sourceId, mod)

        elif mod.get_type() == theke.sword.MODTYPE_GENBOOKS:
            logger.debug("ThekeIndexBuilder - [Index %s as a book]", mod.get_name())

        else:
            logger.debug("ThekeIndexBuilder - Unknown type (%s) of %s", mod.get_type(), mod.get_name())

    def index_biblical_module(self, swordEditionId, sourceId, mod) -> None:
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
                    # Is this document already registered?
                    documentId = self.index.get_document_id(vk.getBookName())

                    if documentId < 0:
                        # No, so create a new document entry
                        documentId = self.index.execute_returning_id("""INSERT INTO documents (type, nbOfSections)
                            VALUES(?, ?);""",
                        (theke.TYPE_BIBLE, vk.getChapterMax()))

                        # and save its name
                        self.index.execute("""INSERT INTO documentNames (id_document, id_edition, name)
                            VALUES(?, ?, ?);""",
                            (documentId, swordEditionId, vk.getBookName()))

                    self.index.execute_returning_id("""INSERT OR IGNORE INTO link_document_source (id_document, id_source)
                            VALUES(?, ?);""",
                        (documentId, sourceId))

        self.index.commit()
