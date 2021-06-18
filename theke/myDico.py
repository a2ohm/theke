import sqlite3
from typing import Any

from collections import namedtuple

dicoEntry = namedtuple('dicoEntry',['id','strongsNb','lemma', 'definition'])

class myDico:
    def __init__(self) -> None:
        self.con = sqlite3.connect('data/myDico.tdic')

        self.con.execute("""CREATE TABLE IF NOT EXISTS dictionary (
            id integer PRIMARY KEY,
            strongs_nb text UNIQUE NOT NULL,
            lemma text,
            definition text NOT NULL
            );""")

    def set_entry(self, strongsNb, lemma, definition):
        if definition != '':
            self.con.execute("""INSERT INTO dictionary (strongs_nb, lemma, definition)
                VALUES(?, ?, ?) 
                ON CONFLICT(strongs_nb) 
                DO UPDATE SET definition=excluded.definition;""",
            (strongsNb, lemma, definition))
            self.con.commit()

    def get_entry(self, strongsNb) -> Any:
        rawEntry = self.con.execute("""SELECT *
            FROM dictionary
            WHERE strongs_nb=?""",
            (strongsNb,)).fetchone()

        return None if rawEntry is None else dicoEntry._make(rawEntry)