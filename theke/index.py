from collections import namedtuple
from typing import Any

import logging
import os
import yaml
import sqlite3
from sqlite3.dbapi2 import Cursor

import Sword
import theke
import theke.sword

logger = logging.getLogger(__name__)

SourceData = namedtuple('SourceData',['name', 'type', 'contentType', 'description'])
DocumentData = namedtuple('documentData',['name', 'type'])

SOURCETYPE_SWORD = 'sword'
SOURCETYPE_EXTERN = 'extern'

INDEX_PATH = os.path.join(theke.PATH_DATA, 'thekeIndex.db')

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

    def get_document_names(self, documentName) -> Any:
        """From a name of a document, return all other names
        """

        documentId = self.get_document_id(documentName)
        rawNames = self.con.execute("""SELECT name
            FROM documentNames
            WHERE id_document=?  AND isShortName=?;""",
            (documentId, False)).fetchall()

        rawShortnames = self.con.execute("""SELECT name
            FROM documentNames
            WHERE id_document=? AND isShortName=?;""",
            (documentId, True)).fetchall()

        return {'names': [n[0] for n in rawNames],
                'shortnames': [n[0] for n in rawShortnames]}
    
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
            version text DEFAULT "0",
            uri text DEFAULT ""
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

        self.index.execute("""INSERT OR IGNORE INTO editions (name, shortname, lang)
                VALUES(?, ?, ?);""",
            ("sword", "sword", ""))

        swordEditionId = self.index.get_edition_id("sword")

        for moduleName, mod in swordLibrary.get_modules():
            if force or (mod.get_version() > self.index.get_source_version(moduleName)):
                self.index_sword_module(swordEditionId, mod)

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

    def index_sword_module(self, swordEditionId, mod) -> None:
        """Index a sword module
        """

        logger.debug("ThekeIndexBuilder - Index %s", mod.get_name())

        # Add the module to the index
        sourceId = self.index.execute_returning_id("""INSERT INTO sources (name, type, contentType, version)
                VALUES(?, ?, ?, ?) 
                ON CONFLICT(name)
                DO UPDATE SET version=excluded.version;""",
            (mod.get_name(), SOURCETYPE_SWORD, mod.get_type() ,mod.get_version()))

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
            self.index_biblical_sword_module(swordEditionId, sourceId, mod)

        elif mod.get_type() == theke.sword.MODTYPE_GENBOOKS:
            self.index_book_sword_module(swordEditionId, sourceId, mod)

        else:
            logger.debug("ThekeIndexBuilder - Unknown type (%s) of %s", mod.get_type(), mod.get_name())

    def index_biblical_sword_module(self, swordEditionId, sourceId, mod) -> None:
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
                    self.index_document(vk.getBookName(), None, vk.getChapterMax(), swordEditionId, sourceId, doCommit=False)

        self.index.commit()

    def index_book_sword_module(self, swordEditionId, sourceId, mod) -> None:
        """Index a sword book module
        """
        logger.debug("ThekeIndexBuilder - Index %s as a book (id: %s)", mod.get_name(), sourceId)
        
        #TOFIX: boucler sur les titres des livres contenus dans ce module.
        self.index_document(mod.get_name(), mod.get_short_repr(), 0, swordEditionId, sourceId)

    ### Index exernal source

    def index_external_source(self, sourceName, data) -> None:
        """Index an external source
        """
        logger.debug("ThekeIndexBuilder - Index %s as an external source", sourceName)

        # Add the external source to the index
        sourceId = self.index.execute_returning_id("""INSERT INTO sources (name, type, contentType, version, uri)
                VALUES(?, ?, ?, ?, ?) 
                ON CONFLICT(name)
                DO UPDATE SET version=excluded.version;""",
            (sourceName, SOURCETYPE_EXTERN, data['type'], data['version'], data['uri']))

        if sourceId is None:
            raise sqlite3.Error("Fails to index the external source {}".format(sourceName))

        # # Add the module description to the index
        # self.index.execute_returning_id("""INSERT INTO sourceDescriptions (id_source, description)
        #         VALUES(?, ?);
        #         """,
        #     (sourceId, data.get('description', '')))

        # Add its edition
        self.index.execute("""INSERT OR IGNORE INTO editions (name, shortname, lang)
                VALUES(?, ?, ?);""",
            (data['edition']['name'], data['edition']['shortname'], data['edition']['lang']))

        editionId = self.index.get_edition_id(data['edition']['name'])

        # Is this document already registered?
        documentId = self.index.get_document_id(data['name'])

        if documentId < 0:
            # No, so create a new document entry
            documentId = self.index.execute_returning_id("""INSERT INTO documents (type, nbOfSections)
                VALUES(?, ?);""",
            (theke.TYPE_EXTERN, 0))

        # Add the document name and shortname
        self.index.execute("""INSERT OR IGNORE INTO documentNames (id_document, id_edition, name)
            VALUES(?, ?, ?);""",
            (documentId, editionId, data['name']))

        self.index.execute("""INSERT OR IGNORE INTO documentNames (id_document, id_edition, name, isShortName)
            VALUES(?, ?, ?, ?);""",
            (documentId, editionId, data['shortname'], True))

        # Add its description
        self.index.execute_returning_id("""INSERT OR IGNORE INTO documentDescriptions (id_document, description, lang)
                VALUES(?, ?, ?);
                """,
            (documentId, data.get('description', ''), ''))

        self.index.execute_returning_id("""INSERT OR IGNORE INTO link_document_source (id_document, id_source)
                VALUES(?, ?);""",
            (documentId, sourceId))

        self.index.commit()
    
    def index_document(self, documentName, documentShortName, nbOfSections, editionId, sourceId, doCommit = True) -> None:
        """Index a document

        @param documentName: (str) name of the document
        @param documentShortName: (str) shortnae of the document (eg. abbreviation of its title)
        @param nbOfSections: (int) for a bible book: number of chapters
        @param editionId: (int) id of the edition
        @param sourceId: (int) id of the source
        """
        # Is this document already registered?
        documentId = self.index.get_document_id(documentName)

        if documentId < 0:
            # No, so create a new document entry
            documentId = self.index.execute_returning_id("""INSERT INTO documents (type, nbOfSections)
                VALUES(?, ?);""",
            (theke.TYPE_BIBLE, nbOfSections))

            # and save its name
            self.index.execute("""INSERT INTO documentNames (id_document, id_edition, name)
                VALUES(?, ?, ?);""",
                (documentId, editionId, documentName))

        # Save its shortname
        if documentShortName is not None:
            self.index.execute("""INSERT INTO documentNames (id_document, id_edition, name, isShortName)
                VALUES(?, ?, ?, ?);""",
                (documentId, editionId, documentShortName, True))

        self.index.execute_returning_id("""INSERT OR IGNORE INTO link_document_source (id_document, id_source)
                VALUES(?, ?);""",
            (documentId, sourceId))

        if doCommit:
            self.index.commit()
