import inventory_db as db


def as_tuples(rows):
    """Turn sqlite3.Row objects into plain tuples so they compare easily."""
    return [tuple(row) for row in rows]


def test_stock_value_by_supplier(connection):
    assert as_tuples(db.stock_value_by_supplier(connection)) == [
        ("Global Building Supplies", 73864),
        ("FastFix Fasteners", 72075),
        ("ToolCorp Industries", 26965),
        ("Acme Hardware Wholesale", 12895),
    ]


def test_low_stock(connection):
    assert as_tuples(db.low_stock(connection)) == [
        ("SKU-H002", "Adjustable Wrench", 2, 5, 3),
        ("SKU-H001", "Claw Hammer", 5, 5, 0),
    ]


def test_sales_by_product(connection):
    assert as_tuples(db.sales_by_product(connection)) == [
        ("Adjustable Wrench", 4, 5800),
        ("Claw Hammer", 2, 3998),
        ("Work Gloves", 2, 2598),
        ("Tape Measure", 2, 1798),
        ("Hex Bolts 50pk", 2, 1700),
        ("Wood Screws 100pk", 2, 1298),
        ("Wall Anchors", 3, 1197),
        ("Safety Glasses", 1, 799),
        ("Utility Knife", 1, 599),
        ("Nails 2in 1lb", 1, 499),
    ]


def test_never_sold(connection):
    assert as_tuples(db.never_sold(connection)) == [
        ("SKU-S204", "Dust Masks 10pk"),
        ("SKU-S203", "Earplugs Box"),
    ]