"""Terminal menu for the inventory system. All input() and print() live here."""

import sqlite3
from contextlib import closing

import inventory_db as db

# Turns a database error into a message a store worker understands.
# Each pair is (text found in the sqlite3 error, friendly message).
FRIENDLY_ERRORS = [
    ("products.SKU", "That SKU is already used by another product."),
    ("FOREIGN KEY", "There is no supplier with that id."),
    ("price_cents >= 0", "The price can't be negative."),
    ("quantity >= 0", "Stock can't go below zero. There isn't enough stock for that."),
    ("reorder_level >= 0", "The reorder level can't be negative."),
    ("units > 0", "The quantity must be at least 1."),
]


def friendly_message(error):
    """Return a friendly message for a sqlite3.IntegrityError."""
    for error_text, message in FRIENDLY_ERRORS:
        if error_text in str(error):
            return message
    return "The database refused that change."


def format_money(cents):
    """Show whole cents as dollars with two decimals, like $19.99."""
    return f"${cents / 100:.2f}"


def ask_int(prompt):
    """Ask until the person types a whole number."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please type a whole number.")


def ask_optional_int(prompt):
    """Like ask_int, but pressing Enter returns None (no value)."""
    while True:
        text = input(prompt).strip()
        if text == "":
            return None
        try:
            return int(text)
        except ValueError:
            print("Please type a whole number, or press Enter to skip.")


def print_products(products):
    if not products:
        print("No products found.")
    for p in products:
        print(f"{p['product_id']}. {p['SKU']}  {p['product_name']} ({p['category']}) "
              f"from {p['supplier_name']}, {format_money(p['price_cents'])}, "
              f"{p['quantity']} in stock, reorder at {p['reorder_level']}")


# ---------- Menu actions ----------

def search(connection):
    text = input("Search name, SKU, or supplier (Enter for all): ").strip()
    category = input("Category (Enter for any): ").strip() or None
    max_price = ask_optional_int("Max price in cents (Enter for any): ")
    in_stock = input("In stock only? (y/n): ").strip().lower() == "y"
    low_stock = input("Low stock only? (y/n): ").strip().lower() == "y"
    print_products(db.search_products(connection, text, category, max_price,
                                      in_stock, low_stock))


def look_up(connection):
    product = db.get_product(connection, ask_int("Product id: "))
    if product is None:
        print("No product has that id.")
    else:
        print_products([product])


def add(connection):
    sku = input("SKU: ").strip()
    name = input("Name: ").strip()
    category = input("Category: ").strip()
    supplier_id = ask_int("Supplier id: ")
    price = ask_int("Price in cents (1999 means $19.99): ")
    quantity = ask_int("Quantity in stock: ")
    reorder_level = ask_int("Reorder level: ")
    try:
        new_id = db.add_product(connection, sku, name, category, supplier_id,
                                price, quantity, reorder_level)
    except sqlite3.IntegrityError as error:
        print(friendly_message(error))
        return
    print(f"Added product {new_id}.")


def restock(connection):
    product_id = ask_int("Product id: ")
    amount = ask_int("Units to add: ")
    try:
        db.restock(connection, product_id, amount)
    except ValueError as error:
        print(error)
        return
    print("Restocked.")


def sale(connection):
    items = []
    while True:
        product_id = ask_optional_int("Product id (Enter to finish): ")
        if product_id is None:
            break
        items.append((product_id, ask_int("Units: ")))
    if not items:
        print("No items entered. Sale cancelled.")
        return
    try:
        sale_no = db.record_sale(connection, items)
    except ValueError as error:
        print(f"{error}. Nothing was saved.")
        return
    except sqlite3.IntegrityError as error:
        print(f"{friendly_message(error)} Nothing was saved.")
        return
    print(f"Recorded sale {sale_no}.")


def report_stock_value(connection):
    for row in db.stock_value_by_supplier(connection):
        print(f"{row['supplier_name']}: {format_money(row['stock_value_cents'])}")


def report_low_stock(connection):
    rows = db.low_stock(connection)
    if not rows:
        print("No products are low on stock.")
    for row in rows:
        print(f"{row['SKU']}  {row['product_name']}: {row['quantity']} in stock, "
              f"reorder at {row['reorder_level']}, {row['units_short']} short")


def report_sales(connection):
    for row in db.sales_by_product(connection):
        print(f"{row['product_name']}: {row['units_sold']} sold, "
              f"{format_money(row['revenue_cents'])}")


def report_never_sold(connection):
    rows = db.never_sold(connection)
    if not rows:
        print("Every product has been sold at least once.")
    for row in rows:
        print(f"{row['SKU']}  {row['product_name']}")


def backup(connection):
    path = db.backup_database(db.DB_PATH, db.DB_PATH.parent / "backups")
    print(f"Backup saved to {path}")


MENU = {
    "1": ("Search products", search),
    "2": ("Look up a product", look_up),
    "3": ("Add a product", add),
    "4": ("Restock a product", restock),
    "5": ("Record a sale", sale),
    "6": ("Report: stock value by supplier", report_stock_value),
    "7": ("Report: low stock", report_low_stock),
    "8": ("Report: sales by product", report_sales),
    "9": ("Report: never sold", report_never_sold),
    "10": ("Back up the database", backup),
}


def main():
    with closing(db.connect()) as connection:
        while True:
            print()
            for key, (label, _action) in MENU.items():
                print(f"{key}. {label}")
            print("0. Quit")
            choice = input("Choose an option: ").strip()
            if choice == "0":
                break
            if choice not in MENU:
                print("Please choose a number from the menu.")
                continue
            MENU[choice][1](connection)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye.")