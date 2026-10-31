import pytest

import inventory_db as db


def names(rows):
    """Return just the product names, to keep the asserts short."""
    return [row["product_name"] for row in rows]


@pytest.mark.parametrize("text, expected", [
    ("hammer", ["Claw Hammer"]),                       # name
    ("sku-f10", ["Hex Bolts 50pk", "Nails 2in 1lb",
                 "Wall Anchors", "Wood Screws 100pk"]),  # SKU
    ("TOOLCORP", ["Tape Measure", "Utility Knife"]),     # supplier name
])
def test_search_matches_name_sku_and_supplier_ignoring_case(connection, text, expected):
    assert names(db.search_products(connection, text)) == expected


def test_category_filter(connection):
    rows = db.search_products(connection, category="Fasteners")
    assert names(rows) == ["Hex Bolts 50pk", "Nails 2in 1lb",
                           "Wall Anchors", "Wood Screws 100pk"]


def test_max_price_filter(connection):
    rows = db.search_products(connection, max_price_cents=499)
    assert names(rows) == ["Nails 2in 1lb", "Wall Anchors"]


def test_in_stock_only_filter(connection):
    db.add_product(connection, "SKU-T001", "Empty Toolbox", "Hand Tools", 1, 3000, 0, 2)
    assert "Empty Toolbox" in names(db.search_products(connection))
    assert "Empty Toolbox" not in names(db.search_products(connection, in_stock_only=True))


def test_low_stock_only_filter(connection):
    rows = db.search_products(connection, low_stock_only=True)
    assert names(rows) == ["Adjustable Wrench", "Claw Hammer"]


def test_filters_combine(connection):
    rows = db.search_products(connection, category="Hand Tools",
                              max_price_cents=1500, low_stock_only=True)
    assert names(rows) == ["Adjustable Wrench"]


def test_dangerous_text_is_never_run_as_sql(connection):
    assert db.search_products(connection, "'; DROP TABLE products; --") == []
    count = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    assert count == 12