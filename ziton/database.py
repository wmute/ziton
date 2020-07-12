"""
Sqlite Database API for the application.
Provides functionality to rebuild and interact with the database.
"""

import logging
import os
import pathlib
import sqlite3
import time
from dataclasses import dataclass

from ziton.config import (
    database_path,
    included_directories,
    hidden_files_enabled,
    excluded_files,
)

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


@dataclass
class DatabaseEntry:
    """dataclass container that represents a single db entry"""

    filename: str
    filepath: str
    size: int
    modified: int


def build_database():
    """Build database in pure python code."""
    db_path = database_path()
    check_hidden = hidden_files_enabled()
    # establish connection and create table if it doesn'T exist yet
    LOGGER.info("Complete database rebuild...(python backend)")
    start_time = time.time()
    ex = excluded_files()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS files")
    cursor.execute(
        """CREATE TABLE files(filename TEXT, filepath TEXT,
            size INT, modified INT);"""
    )
    # iterate over disk and build file entries
    directories = included_directories()
    file_list = []
    for directory in directories:
        for root, dirs, files in os.walk(directory, topdown=True):
            if not check_hidden:
                files = [f for f in files if not f[0] == "." and f not in ex]
                dirs[:] = [d for d in dirs if not d[0] == "." and d not in ex]
            # iterate over files
            for fil in files:
                path = os.path.join(root, fil)
                if os.path.exists(path):
                    f_info = os.stat(path)
                    size = int(f_info.st_size)
                    modified = int(f_info.st_mtime)
                    file_list.append((fil, path, size, modified))
            # iterate over directories
            for drt in dirs:
                path = os.path.join(root, drt)
                if os.path.exists(path):
                    f_info = os.stat(path)
                    modified = int(f_info.st_mtime)
                    file_list.append((drt, path, 0, modified))

    # write file entries to database
    cursor.executemany("INSERT INTO files VALUES (?, ?, ?, ?)", file_list)
    conn.commit()
    conn.close()

    t_end = time.time() - start_time
    LOGGER.info(f"Full rebuild finished. Time elapsed: {t_end:.2f}s")


def number_of_rows():
    "Number of entries in the table."

    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM files")
    data = cursor.fetchall()
    conn.close()
    return data[0][0]


def validate_database():
    "Check if database exists, if not build it."
    LOGGER.info(f"Validating Database -> '{database_path()}' ")
    path = pathlib.Path(database_path())
    if not path.parent.exists():
        pathlib.Path(database_path()).parent.mkdir()
    if not path.exists():
        build_database()


def dbrecord_from_path(filepath):
    "Builds up a dataclass that represents a db record for the `files` table."
    fileinfo = os.stat(filepath)
    filename = str(pathlib.Path(filepath).name)
    filesize = fileinfo.st_size
    modified = fileinfo.st_mtime
    db_record = DatabaseEntry(filename, filepath, filesize, modified)
    return db_record


def find_row_id(filepath):
    "Find the row id of given filepath."
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()
    cursor.execute("SELECT ROWID FROM files WHERE filepath=?", [filepath])
    data = cursor.fetchall()
    conn.close()
    return data


def delete_record(filepath):
    "Deletes a row from the table."
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM files WHERE filepath=?", [filepath])
    conn.close()


def add_bookmark(filepath):
    """add bookmark to the database"""
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()
    fname = pathlib.Path(filepath).name
    # create table if it doesn't exist yet
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS bookmarks(
        filename TEXT,
        filepath TEXT,
        UNIQUE(filename, filepath))"""
    )
    cursor.execute("INSERT OR IGNORE INTO bookmarks VALUES (?, ?)", (fname, filepath))
    conn.commit()
    conn.close()


def get_bookmarks():
    """Select all bookmarks from the database."""
    try:
        conn = sqlite3.connect(database_path())
        cursor = conn.cursor()
        sql = cursor.execute("SELECT * FROM bookmarks")
        rows = sql.fetchall()
        conn.commit()
        conn.close()
        return rows
    except Exception as err:
        LOGGER.error(err)
        return ()


def delete_bookmarks():
    """Remove all entries from the bookmark table."""
    LOGGER.info("Removing all bookmarks...")
    conn = sqlite3.connect(database_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookmarks;")
    conn.commit()
    conn.close()
