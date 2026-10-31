import sqlite3
import pytest
from pathlib import Path

def test_schema_tables_exist(connection):
    """Verify all five required tables exist in the database."""
    tables = ["suppliers", "products", "sales", "sale_items", "stock_movements"]
    for table in tables:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?;", (table,)
        )
        assert cursor.fetchone() is not None

def test_foreign_key_constraint_enforced(connection):
    """Verify that inserting a product with a non-existent supplier_id is refused."""
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """INSERT INTO products (SKU, product_name, category, supplier_id, price_cents, quantity, reorder_level)
               VALUES ('SKU-TEST', 'Test Item', 'Tools', 999, 1000, 10, 5);"""
        )

def test_check_constraints_negative_values(connection):
    """Verify that negative prices or quantities violate CHECK constraints."""
    # First insert a valid supplier
    connection.execute("INSERT INTO suppliers (supplier_name) VALUES ('Test Supplier');")
    sup_id = connection.execute("SELECT last_insert_rowid();").fetchone()[0]
    
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """INSERT INTO products (SKU, product_name, category, supplier_id, price_cents, quantity, reorder_level)
               VALUES ('SKU-NEG', 'Bad Price', 'Tools', ?, -50, 10, 5);""", (sup_id,)
        )

def test_stock_movement_reason_constraint(connection):
    """Verify that stock movements only accept valid reasons ('restock', 'adjustment', 'sale')."""
    # Insert supplier and product first
    connection.execute("INSERT INTO suppliers (supplier_name) VALUES ('Sup');")
    sup_id = connection.execute("SELECT last_insert_rowid();").fetchone()[0]
    connection.execute(
        """INSERT INTO products (SKU, product_name, category, supplier_id, price_cents, quantity, reorder_level)
           VALUES ('SKU-M1', 'Item', 'Tools', ?, 100, 10, 5);""", (sup_id,)
    )
    prod_id = connection.execute("SELECT last_insert_rowid();").fetchone()[0]
    
    # Invalid reason should fail
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """INSERT INTO stock_movements (product_id, quantity_change, reason, movement_timestamp)
               VALUES (?, 5, 'invalid_reason', '2026-10-30 12:00:00');""", (prod_id,)
        )