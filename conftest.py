import sqlite3
from pathlib import Path
import pytest

PROJECT_FOLDER = Path(__file__).parent

@pytest.fixture
def connection():
    """Provides a fresh in-memory database with schema and foreign keys enabled for each test."""
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON;")
    con.row_factory = sqlite3.Row
    
    # Execute schema
    schema_script = (PROJECT_FOLDER / "schema.sql").read_text(encoding="utf-8")
    con.executescript(schema_script)
    
    yield con
    con.close()