import logging

import os
import sqlite3
from typing import Any

from collections import namedtuple

import theke

logger = logging.getLogger(__name__)

dicoEntry = namedtuple('dicoEntry',['id','strongsNb','lemma', 'definition'])

DICO_PATH = os.path.join(theke.PATH_DATA, 'myDico.tdic')

class myDico:
    def __init__(self) -> None:
        logger.debug("myDico - Create a new instance")

        logger.debug("myDico - Connect to the database")
        self.con = sqlite3.connect(DICO_PATH)

        logger.debug("myDico - Initiate the database (if necessary)")
        self.con.execute("""CREATE TABLE IF NOT EXISTS dictionary (
            id integer PRIMARY KEY,
            strongs_nb text UNIQUE NOT NULL,
            lemma text,
            definition text NOT NULL
            );""")

    def set_entry(self, strongsNb, lemma, definition):
        if definition != '':
            logger.debug("myDico - Set an entry: {} ({})".format(lemma, strongsNb))

            self.con.execute("""INSERT INTO dictionary (strongs_nb, lemma, definition)
                VALUES(?, ?, ?) 
                ON CONFLICT(strongs_nb) 
                DO UPDATE SET definition=excluded.definition;""",
            (strongsNb, lemma, definition))
            self.con.commit()

        else:
            logger.debug("myDico - Remove an entry: {} ({})".format(lemma, strongsNb))

            self.con.execute("""DELETE FROM dictionary
                WHERE strongs_nb=?;""",
            (strongsNb,))
            self.con.commit()

    def get_entry(self, strongsNb) -> Any:
        rawEntry = self.con.execute("""SELECT *
            FROM dictionary
            WHERE strongs_nb=?""",
            (strongsNb,)).fetchone()

        return None if rawEntry is None else dicoEntry._make(rawEntry)