import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "inventory.db"
# Each product with its supplier's name. Shared by get_product and search_products.
PRODUCT_SELECT = (
    "SELECT p.product_id, p.SKU, p.product_name, p.category, s.supplier_name, "
    "p.price_cents, p.quantity, p.reorder_level "
    "FROM products p JOIN suppliers s ON s.supplier_id = p.supplier_id"
)

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
        PRODUCT_SELECT + " WHERE p.product_id = ?", (product_id,)
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

def search_products(connection, text="", category=None, max_price_cents=None,
                    in_stock_only=False, low_stock_only=False):
    """Return products whose name, SKU, or supplier name contains the text, sorted by name.

    The optional filters can be combined. Only fixed pieces of SQL are added
    to the query; every value goes in through a placeholder.
    """
    pattern = f"%{text}%"
    sql = PRODUCT_SELECT + (
        " WHERE (p.product_name LIKE ? OR p.SKU LIKE ? OR s.supplier_name LIKE ?)"
    )
    params = [pattern, pattern, pattern]

    if category is not None:
        sql += " AND p.category = ?"
        params.append(category)
    if max_price_cents is not None:
        sql += " AND p.price_cents <= ?"
        params.append(max_price_cents)
    if in_stock_only:
        sql += " AND p.quantity > 0"
    if low_stock_only:
        sql += " AND p.quantity <= p.reorder_level"

    sql += " ORDER BY p.product_name"
    return connection.execute(sql, params).fetchall()

# ---------- Reports ----------
# Money stays in whole cents here. The menu formats it with two decimals.

def stock_value_by_supplier(connection):
    """Return each supplier's name and total stock value (price x quantity), highest first."""
    return connection.execute(
        "SELECT s.supplier_name, SUM(p.price_cents * p.quantity) AS stock_value_cents "
        "FROM suppliers s JOIN products p ON p.supplier_id = s.supplier_id "
        "GROUP BY s.supplier_id, s.supplier_name "
        "ORDER BY stock_value_cents DESC"
    ).fetchall()


def low_stock(connection):
    """Return products at or below their reorder level, with how many units short they are."""
    return connection.execute(
        "SELECT SKU, product_name, quantity, reorder_level, "
        "reorder_level - quantity AS units_short "
        "FROM products "
        "WHERE quantity <= reorder_level "
        "ORDER BY units_short DESC, product_name"
    ).fetchall()


def sales_by_product(connection):
    """Return each sold product with units sold and revenue, highest revenue first."""
    return connection.execute(
        "SELECT p.product_name, SUM(si.units) AS units_sold, "
        "SUM(si.units * si.unit_price_cents) AS revenue_cents "
        "FROM products p JOIN sale_items si ON si.product_id = p.product_id "
        "GROUP BY p.product_id, p.product_name "
        "ORDER BY revenue_cents DESC, p.product_name"
    ).fetchall()


def never_sold(connection):
    """Return products that appear in no sale."""
    return connection.execute(
        "SELECT p.SKU, p.product_name "
        "FROM products p LEFT JOIN sale_items si ON si.product_id = p.product_id "
        "WHERE si.product_id IS NULL "
        "ORDER BY p.product_name"
    ).fetchall()