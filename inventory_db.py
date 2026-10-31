import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "inventory.db"


def connect(path=DB_PATH):
    """Open a connection with foreign keys on and rows readable by column name."""
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection

def add_product(connection, sku, name, category, supplier_id,
                price_cents, quantity, reorder_level):
    """Add a product and return its new id.

    Raises sqlite3.IntegrityError for a duplicate SKU, an unknown supplier,
    or a negative price or quantity.
    """
    cursor = connection.execute(
        "INSERT INTO products (SKU, product_name, category, supplier_id, "
        "price_cents, quantity, reorder_level) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sku, name, category, supplier_id, price_cents, quantity, reorder_level),
    )
    connection.commit()
    return cursor.lastrowid


def get_product(connection, product_id):
    """Return one product with its supplier's name, or None if there is no such product."""
    return connection.execute(
        "SELECT p.product_id, p.SKU, p.product_name, p.category, s.supplier_name, "
        "p.price_cents, p.quantity, p.reorder_level "
        "FROM products p JOIN suppliers s ON s.supplier_id = p.supplier_id "
        "WHERE p.product_id = ?",
        (product_id,),
    ).fetchone()


def update_price(connection, product_id, new_price_cents):
    """Set a product's price. Return True if the product exists.

    Raises sqlite3.IntegrityError for a negative price.
    """
    cursor = connection.execute(
        "UPDATE products SET price_cents = ? WHERE product_id = ?",
        (new_price_cents, product_id),
    )
    connection.commit()
    return cursor.rowcount == 1


def delete_product(connection, product_id):
    """Delete a product. Return True if it existed.

    Raises sqlite3.IntegrityError if the product has been sold, because
    sale_items still refers to it.
    """
    cursor = connection.execute(
        "DELETE FROM products WHERE product_id = ?", (product_id,)
    )
    connection.commit()
    return cursor.rowcount == 1