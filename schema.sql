CREATE TABLE IF NOT EXISTS suppliers(
    supplier_id INTEGER PRIMARY KEY,
    supplier_name TEXT NOT NULL UNIQUE
) STRICT;

CREATE TABLE IF NOT EXISTS products(
    product_id INTEGER PRIMARY KEY,
    SKU TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(supplier_id),
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    reorder_level INTEGER NOT NULL CHECK (reorder_level >= 0)
) STRICT;

CREATE TABLE IF NOT EXISTS sales(
    sale_no INTEGER PRIMARY KEY,
    sale_timestamp TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS sale_items(
    sale_item_id INTEGER PRIMARY KEY,
    sale_no INTEGER NOT NULL REFERENCES sales(sale_no),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    units INTEGER NOT NULL CHECK (units > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0)
) STRICT;

CREATE TABLE IF NOT EXISTS stock_movements(
    movement_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity_change INTEGER NOT NULL,
    reason TEXT NOT NULL CHECK (reason IN('restock', 'adjustment', 'sale')),
    movement_timestamp TEXT NOT NULL
) STRICT;

CREATE INDEX IF NOT EXISTS idx_products_supplier ON products(supplier_id);