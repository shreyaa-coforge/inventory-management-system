import sqlite3

import pytest

import inventory_db as db


def add_test_product(connection, sku="SKU-T001", supplier_id=1,
                     price_cents=2500, quantity=4):
    """Add a valid test product. Tests change one value to break one rule."""
    return db.add_product(connection, sku, "Hand Saw", "Hand Tools",
                          supplier_id, price_cents, quantity, 2)


def test_add_product_returns_new_id(connection):
    new_id = add_test_product(connection)
    assert new_id == 13
    product = db.get_product(connection, new_id)
    assert product["product_name"] == "Hand Saw"
    assert product["supplier_name"] == "Acme Hardware Wholesale"


def test_duplicate_sku_is_refused(connection):
    with pytest.raises(sqlite3.IntegrityError):
        add_test_product(connection, sku="SKU-H001")


def test_unknown_supplier_is_refused(connection):
    with pytest.raises(sqlite3.IntegrityError):
        add_test_product(connection, supplier_id=99)


@pytest.mark.parametrize("price_cents, quantity", [
    (-1, 4),    # negative price
    (2500, -1), # negative quantity
])
def test_negative_price_or_quantity_is_refused(connection, price_cents, quantity):
    with pytest.raises(sqlite3.IntegrityError):
        add_test_product(connection, price_cents=price_cents, quantity=quantity)


def test_update_price_changes_the_price(connection):
    assert db.update_price(connection, 1, 2199) is True
    assert db.get_product(connection, 1)["price_cents"] == 2199


def test_update_price_of_missing_product_returns_false(connection):
    assert db.update_price(connection, 999, 100) is False


def test_sold_product_cannot_be_deleted(connection):
    with pytest.raises(sqlite3.IntegrityError):
        db.delete_product(connection, 1)
    assert db.get_product(connection, 1) is not None


def test_never_sold_product_can_be_deleted(connection):
    assert db.delete_product(connection, 11) is True
    assert db.get_product(connection, 11) is None