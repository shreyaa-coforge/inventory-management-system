import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "inventory.db"


def connect(path=DB_PATH):
    """Open a connection with foreign keys on and rows readable by column name."""
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection