import sqlite3
from pathlib import Path

def seed_database():
    db_path = Path("inventory.db")

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON;")

    schema_script = Path("schema.sql").read_text(encoding = "utf-8")
    connection.executescript(schema_script)

    #seeding supplier table
    suppliers_data = [
        ("Acme Hardware Wholesale",),
        ("ToolCorp Industries",),
        ("FastFix Fasteners",),
        ("Global Building Supplies",)
    ]
    connection.executemany(
        "INSERT INTO suppliers (supplier_name) VALUES (?);",
        suppliers_data
    )

    # seeding products table
    products_data = [
        ("SKU-H001", "Claw Hammer", "Hand Tools", 1, 1999, 5, 5),          # At reorder level
        ("SKU-H002", "Adjustable Wrench", "Hand Tools", 1, 1450, 2, 5),     # Below reorder level
        ("SKU-H003", "Tape Measure", "Hand Tools", 2, 899, 20, 10),
        ("SKU-H004", "Utility Knife", "Hand Tools", 2, 599, 15, 5),
        ("SKU-F101", "Wood Screws 100pk", "Fasteners", 3, 649, 30, 10),
        ("SKU-F102", "Nails 2in 1lb", "Fasteners", 3, 499, 45, 15),
        ("SKU-F103", "Hex Bolts 50pk", "Fasteners", 3, 850, 12, 5),
        ("SKU-F104", "Wall Anchors", "Fasteners", 3, 399, 50, 20),
        ("SKU-S201", "Safety Glasses", "Safety Equipment", 4, 799, 10, 5),
        ("SKU-S202", "Work Gloves", "Safety Equipment", 4, 1299, 8, 5),
        ("SKU-S203", "Earplugs Box", "Safety Equipment", 4, 1500, 25, 10),  # Never sold
        ("SKU-S204", "Dust Masks 10pk", "Safety Equipment", 4, 999, 18, 8) # Never sold
    ]
    connection.executemany(
        """INSERT INTO products (SKU, product_name, category, supplier_id, price_cents, quantity, reorder_level)
           VALUES (?, ?, ?, ?, ?, ?, ?);""",
        products_data
    )

    #seeding sales table
    sales_data = [
        (1, "2026-10-01 10:00:00"),
        (2, "2026-10-02 11:30:00"),
        (3, "2026-10-03 14:15:00"),
        (4, "2026-10-04 09:45:00"),
        (5, "2026-10-05 16:20:00")
    ]
    connection.executemany(
        "INSERT INTO sales (sale_no, sale_timestamp) VALUES (?, ?);",
        sales_data
    )

    #seeding sales item 
    sale_items_data = [
        (1, 1, 1, 1999),
        (1, 3, 2, 899),
        (2, 2, 3, 1450),
        (2, 4, 1, 599),
        (3, 5, 2, 649),
        (3, 6, 1, 499),
        (4, 7, 2, 850),
        (4, 8, 3, 399),
        (5, 9, 1, 799),
        (5, 10, 2, 1299),
        (5, 1, 1, 1999),
        (5, 2, 1, 1450)
    ]
    connection.executemany(
        """INSERT INTO sale_items (sale_no, product_id, units, unit_price_cents)
           VALUES (?, ?, ?, ?);""",
        sale_items_data
    )
    
    connection.commit()

    tables = ["suppliers", "products", "sales", "sale_items", "stock_movements"]
    print("Database seeded successfully. Row counts:")
    for table in tables:
        count = connection.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
        print(f" - {table}: {count}")
        
    connection.close()

if __name__ == "__main__":
    seed_database()