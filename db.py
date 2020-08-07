import os
import sqlite3
import numpy as np


def ensure_connection(func):
    def inner(*args, **kwargs):
        with sqlite3.connect('chords.db') as conn:
            res = func(*args, conn=conn, **kwargs)
        return res

    return inner


__connection = None


def get_connect():
    global __connection
    if __connection is None:
        __connection = sqlite3.connect('chords.db')
    return __connection


@ensure_connection
def init_db(conn, force: bool = False):
    c = conn.cursor()

    if force:
        c.execute('DROP TABLE IF EXISTS default_instrument')

    c.execute('''
        CREATE TABLE IF NOT EXISTS default_instrument (
            user_id INTEGER PRIMARY KEY,
            instrument    TEXT NOT NULL
        )
        ''')

    conn.commit()


def add_chord(note: str, name: str, path: str):
    conn = get_connect()
    c = conn.cursor()
    name = name.replace("slash", "/")
    c.execute("INSERT INTO guitar_chords (note, name, image) VALUES (?, ?, ?)", (note, name, path))
    conn.commit()


def fill_db(_type: str = "guitar"):
    path = os.path.join("database", _type)
    notes = os.listdir(path)
    for note in notes:
        p = os.path.join(path, note)
        chords = os.listdir(p)
        for chord in chords:
            p1 = os.path.join(p, chord)
            images = os.listdir(p1)
            for image in images:
                add_chord(note, chord, p1 + "\\" + image)
                print(f"Chord {chord} is added to {p1}\\{image}")


@ensure_connection
def select_chords(conn):
    c = conn.cursor()
    c.execute("SELECT * FROM guitar_chords")
    res = c.fetchall()
    conn.commit()
    return res


@ensure_connection
def get_chord_versions(_type: str, name: str, conn):
    c = conn.cursor()
    c.execute(f"SELECT image, name FROM {_type}_chords WHERE LOWER(name) = '{name.lower()}'")
    res = c.fetchall()
    conn.commit()

    return [path[0] for path in res], res[0][1] if res else None


@ensure_connection
def get_chords_names(_type: str, note: str, conn):
    c = conn.cursor()
    c.execute(f"SELECT DISTINCT name FROM {_type}_chords WHERE note = '{note}'")
    res = c.fetchall()
    conn.commit()

    chords = [path[0] for path in res]
    chords.remove(f"{note}major")
    chords.remove(f"{note}minor")
    chords.insert(0, f"{note}major")
    chords.insert(1, f"{note}minor")
    return chords


@ensure_connection
def set_default_instrument(user_id: int, instrument: str, conn):
    c = conn.cursor()

    if not get_user_instrument(user_id):
        c.execute("INSERT INTO default_instrument (user_id, instrument) VALUES (?, ?)", (user_id, instrument))
    else:
        c.execute(f"UPDATE 'default_instrument'"
                  f"SET instrument='{instrument}'"
                  f"WHERE user_id={user_id}")
    conn.commit()


@ensure_connection
def get_user_instrument(user_id: int, conn):
    c = conn.cursor()
    c.execute(f"SELECT instrument FROM default_instrument WHERE user_id = '{user_id}'")
    res = c.fetchall()
    conn.commit()

    if res:
        return res[0][0]
    else:
        return None


if __name__ == '__main__':
    init_db(force=True)

