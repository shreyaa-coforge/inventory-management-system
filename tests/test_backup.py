from contextlib import closing

import inventory_db as db
import seed_db


def row_counts(path):
    with closing(db.connect(path)) as connection:
        return [
            # table names come from the fixed list in seed_db
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in seed_db.TABLES
        ]


def test_backup_passes_integrity_check_and_has_same_row_counts(tmp_path):
    original = tmp_path / "inventory.db"
    with closing(db.connect(original)) as connection:
        seed_db.create_tables(connection)
        seed_db.load_sample_data(connection)

    backup = db.backup_database(original, tmp_path / "backups")

    with closing(db.connect(backup)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert row_counts(backup) == row_counts(original)