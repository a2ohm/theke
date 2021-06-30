import sqlite3
from sqlite3.dbapi2 import Cursor
from typing import Any, Dict

import logging
logger = logging.getLogger(__name__)

import Sword
import theke.sword

from collections import namedtuple

moduleData = namedtuple('moduleData',['name', 'type', 'description'])
documentData = namedtuple('documentData',['name', 'moduleName'])

index_path = 'data/thekeIndex.db'

class ThekeIndex:
    def __init__(self) -> None:
        logger.debug("ThekeIndex - Create a new instance")
        logger.debug("ThekeIndex - Connect to the database")
        self.con = sqlite3.connect(index_path)

    def execute(self, sql, parameters = ()) -> Cursor:
        return self.con.execute(sql, parameters)

    def execute_returning_id(self, sql, parameters = ()) -> Any:
        """Insert an entry and return the row id
        """
        cur = self.con.cursor()
        cur.execute(sql, parameters)
        #self.con.commit()

        return cur.lastrowid

    def commit(self) -> None:
        self.con.commit()

    def get_document_id(self, documentName) -> int:
        rawId = self.con.execute("""SELECT id
            FROM documents
            WHERE swordName=?;""",
            (documentName,)).fetchone()

        return -1 if rawId is None else rawId[0]

    def get_document_nbOfSections(self, documentName) -> int:
        rawNbOfSections = self.con.execute("""SELECT nbOfSections
            FROM documentDetails
            INNER JOIN documents ON documentDetails.id_document = documents.id
            WHERE documents.swordName=?;""",
            (documentName,)).fetchone()

        return -1 if rawNbOfSections is None else rawNbOfSections[0]

    def get_module_version(self, moduleName) -> str:
        """Return the version a of sword module
        """
        rawVersion = self.con.execute("""SELECT version
            FROM modules
            WHERE name=?;""",
            (moduleName,)).fetchone()

        return '0' if rawVersion is None else rawVersion[0]

    def list_modules(self, moduleType = None):
        if moduleType is None:
            rawModulesData = self.con.execute("""SELECT modules.name, modules.type, moduleDescriptions.description
                FROM modules
                INNER JOIN moduleDescriptions ON modules.id = moduleDescriptions.id_module;""")

        else:
            rawModulesData = self.con.execute("""SELECT modules.name, modules.type, moduleDescriptions.description
                FROM modules
                INNER JOIN moduleDescriptions ON modules.id = moduleDescriptions.id_module
                WHERE modules.type=?;""",
                (moduleType,))

        for rawModuleData in rawModulesData:
            yield moduleData._make(rawModuleData)

    def list_documents(self):
        rawDocumentsData = self.con.execute("""SELECT documents.swordName, modules.name
                FROM documents
                INNER JOIN link_document_module ON documents.id = link_document_module.id_document
                INNER JOIN modules ON link_document_module.id_module = modules.id;""")

        for rawDocumentData in rawDocumentsData:
            yield documentData._make(rawDocumentData)

class ThekeIndexBuilder:
    def __init__(self) -> None:
        logger.debug("ThekeIndexBuilder - Create a new instance")
        self.index = ThekeIndex()

        logger.debug("ThekeIndexBuilder - Initiate the database (if necessary)")
        # ... documents
        self.index.execute("""CREATE TABLE IF NOT EXISTS documents (
            id integer PRIMARY KEY,
            swordName text UNIQUE NOT NULL,
            type text NOT NULL
            );""")

        # ... documentDescriptions
        self.index.execute("""CREATE TABLE IF NOT EXISTS documentDescriptions (
            id_document integer NOT NULL,
            description text NOT NULL,
            lang text NOT NULL,
            FOREIGN KEY(id_document) REFERENCES documents(id) ON DELETE CASCADE
            );""")

        # ... documentDetails
        self.index.execute("""CREATE TABLE IF NOT EXISTS documentDetails (
            id_document integer NOT NULL,
            nbOfSections int NOT NULL,
            FOREIGN KEY(id_document) REFERENCES documents(id) ON DELETE CASCADE
            );""")

        # ... modules
        self.index.execute("""CREATE TABLE IF NOT EXISTS modules (
            id integer PRIMARY KEY,
            name text UNIQUE NOT NULL,
            type text NOT NULL,
            version text NOT NULL
            );""")

        # ... moduleDescriptions
        self.index.execute("""CREATE TABLE IF NOT EXISTS moduleDescriptions (
            id_module integer NOT NULL,
            description text NOT NULL,
            lang text DEFAULT "en",
            FOREIGN KEY(id_module) REFERENCES modules(id) ON DELETE CASCADE
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
            shortname text NOT NULL,
            FOREIGN KEY(id_document) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY(id_edition) REFERENCES editions(id) ON DELETE CASCADE
            );""")

        # ... link_document_module
        self.index.execute("""CREATE TABLE IF NOT EXISTS link_document_module (
            id_document integer NOT NULL,
            id_module integer NOT NULL,
            FOREIGN KEY(id_document) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY(id_module) REFERENCES modules(id) ON DELETE CASCADE
            );""")

    def build(self, force = False) -> None:
        """Build the index.
        """
        swordLibrary = theke.sword.SwordLibrary()

        for moduleName, mod in swordLibrary.get_modules():
            if force or (mod.get_version() > self.index.get_module_version(moduleName)):
                self.index_module(mod)
    
    def index_module(self, mod) -> None:
        logger.debug("ThekeIndexBuilder - Index {}".format(mod.get_name()))

        # Add the module in the index
        moduleId = self.index.execute_returning_id("""INSERT INTO modules (name, type, version)
                VALUES(?, ?, ?) 
                ON CONFLICT(name)
                DO UPDATE SET version=excluded.version;""",
            (mod.get_name(), mod.get_type(), mod.get_version()))

        if moduleId is None:
            raise sqlite3.Error("Fails to index the module {}".format(mod.get_name()))

        # Add the module description in the index
        self.index.execute_returning_id("""INSERT INTO moduleDescriptions (id_module, description)
                VALUES(?, ?);
                """,
            (moduleId, mod.get_description()))

        self.index.commit()
        
        # Next indexing steps depend of the module type
        if mod.get_type() == theke.sword.MODTYPE_BIBLES:
            self.index_biblical_module(mod, moduleId)

        elif mod.get_type() == theke.sword.MODTYPE_GENBOOKS:
            logger.debug("ThekeIndexBuilder - [Index {} as a book]".format(mod.get_name()))

        else:
            logger.debug("ThekeIndexBuilder - Unknown type ({}) of {}".format(mod.get_type(), mod.get_name()))

    def index_biblical_module(self, mod, moduleId) -> None:
        logger.debug("ThekeIndexBuilder - Index {} as a Bible (id: {})".format(mod.get_name(), moduleId))

        # Index each of the biblical books of this module
        # TODO: Y a-t-il une façon plus propre de faire la même chose ?
        vk = Sword.VerseKey()
        
        for itestament in [1, 2]:
            vk.setTestament(itestament)

            for ibook in range(1, vk.getBookMax() +1):
                vk.setBook(ibook)
                if mod.has_entry(vk):
                    self.index.execute("""INSERT OR IGNORE INTO documents (swordName, type)
                            VALUES(?, ?);""",
                        (vk.getBookName(), theke.sword.MODTYPE_BIBLES))

                    documentId = self.index.get_document_id(vk.getBookName())

                    if documentId < 0:
                        raise sqlite3.Error("Entry not found, even if it should be there...")

                    self.index.execute_returning_id("""INSERT OR IGNORE INTO link_document_module (id_document, id_module)
                            VALUES(?, ?);""",
                        (documentId, moduleId))

                    self.index.execute("""INSERT OR IGNORE INTO documentDetails (id_document, nbOfSections)
                            VALUES(?, ?);""",
                            (documentId, vk.getChapterMax()))
        
        self.index.commit()