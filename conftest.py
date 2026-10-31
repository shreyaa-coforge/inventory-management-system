import pytest

import inventory_db as db
import seed_db


@pytest.fixture
def connection():
    """A fresh in-memory database with the schema and sample data for each test."""
    con = db.connect(":memory:")
    seed_db.create_tables(con)
    seed_db.load_sample_data(con)
    yield con
    con.close()