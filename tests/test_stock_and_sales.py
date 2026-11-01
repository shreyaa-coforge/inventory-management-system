import sqlite3
from datetime import UTC, datetime

import pytest

import inventory_db as db

FIXED_TIME = datetime(2026, 11, 1, 9, 0, 0, tzinfo=UTC)


def stock(connection, product_id):
    return db.get_product(connection, product_id)["quantity"]


def count(connection, table):
    # table always comes from the fixed names written in these tests
    return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def snapshot(connection):
    """Everything a stock change or sale could touch, to compare before and after."""
    quantities = connection.execute(
        "SELECT product_id, quantity FROM products ORDER BY product_id"
    ).fetchall()
    return (count(connection, "sales"), count(connection, "sale_items"),
            count(connection, "stock_movements"), [tuple(q) for q in quantities])


# ---------- restock ----------

def test_restock_increases_stock_and_logs_one_movement(connection):
    db.restock(connection, 1, 10, now=FIXED_TIME)
    assert stock(connection, 1) == 15
    movements = connection.execute("SELECT * FROM stock_movements").fetchall()
    assert len(movements) == 1
    assert movements[0]["quantity_change"] == 10
    assert movements[0]["reason"] == "restock"
    assert movements[0]["movement_timestamp"] == "2026-11-01 09:00:00"


@pytest.mark.parametrize("amount", [0, -5])
def test_restock_of_zero_or_less_is_refused(connection, amount):
    before = snapshot(connection)
    with pytest.raises(ValueError):
        db.restock(connection, 1, amount)
    assert snapshot(connection) == before


# ---------- adjust ----------

def test_adjustment_changes_stock_and_logs_it(connection):
    db.adjust_stock(connection, 3, -4, now=FIXED_TIME)
    assert stock(connection, 3) == 16
    movement = connection.execute("SELECT * FROM stock_movements").fetchone()
    assert movement["quantity_change"] == -4
    assert movement["reason"] == "adjustment"


def test_adjustment_below_zero_is_refused_and_changes_nothing(connection):
    before = snapshot(connection)
    with pytest.raises(sqlite3.IntegrityError):
        db.adjust_stock(connection, 2, -3)  # only 2 in stock
    assert snapshot(connection) == before


# ---------- record a sale ----------

def test_sale_records_lines_at_current_price_reduces_stock_and_logs(connection):
    db.update_price(connection, 3, 950)  # new price must be used, not the old 899
    sale_no = db.record_sale(connection, [(3, 2), (4, 1)], now=FIXED_TIME)

    assert sale_no == 6
    lines = connection.execute(
        "SELECT product_id, units, unit_price_cents FROM sale_items "
        "WHERE sale_no = ? ORDER BY product_id", (sale_no,)
    ).fetchall()
    assert [tuple(line) for line in lines] == [(3, 2, 950), (4, 1, 599)]
    assert stock(connection, 3) == 18
    assert stock(connection, 4) == 14
    movements = connection.execute(
        "SELECT product_id, quantity_change, reason FROM stock_movements "
        "ORDER BY product_id"
    ).fetchall()
    assert [tuple(m) for m in movements] == [(3, -2, "sale"), (4, -1, "sale")]


def test_sale_that_fails_halfway_changes_nothing(connection):
    before = snapshot(connection)
    with pytest.raises(sqlite3.IntegrityError):
        # line 1 is fine, line 2 asks for 99 when only 20 are in stock
        db.record_sale(connection, [(4, 1), (3, 99)])
    assert snapshot(connection) == before


def test_sale_for_unknown_product_changes_nothing(connection):
    before = snapshot(connection)
    with pytest.raises(ValueError):
        db.record_sale(connection, [(4, 1), (999, 1)])
    assert snapshot(connection) == before


def test_sale_with_same_product_twice_changes_nothing(connection):
    before = snapshot(connection)
    with pytest.raises(ValueError):
        db.record_sale(connection, [(4, 1), (4, 2)])
    assert snapshot(connection) == before