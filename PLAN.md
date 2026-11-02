# Inventory Management System - Project Plan

## 1. Project Overview
Hardware store keeps its stock in a spreadsheet which leads to price drifts, wrong stock count and nobody can say what changed when a sale goes through. I am building an inventory management system for the store where data is kept in SQLite3 database with 5 tables and a Python terminal interface. The user will be able to add and look up products, search with filters, run reports and record sales.

## 2. Database Design
### 2.1 Suppliers
Contains information about suppliers that supply the products to the hardware company. 
Columns: supplier_id, supplier_name where supplier_id is the primary key.
### 2.2 Products
The current state of each item the store sells.
Fields and types: product_id INTEGER, sku TEXT, product_name TEXT, category TEXT, supplier_id INTEGER, price_cents INTEGER, quantity INTEGER, reorder_level INTEGER
Primary key: product_id
Foreign key: supplier_id references suppliers(supplier_id). An unknown supplier is refused.
### 2.3 Sales
Purpose: One row is one completed sale. It is the parent of the sale's lines.
Fields and types: sale_no INTEGER, sale_timestamp TEXT
Primary key: sale_no
### 2.4 Sale Items
Sale lines are separate from sales because one sale holds many products and one product appears in many sales (many-to-many). The line also holds facts that belong to the pairing: the quantity and the price charged.
Fields and types: sale_item_id INTEGER, sale_no INTEGER, product_id INTEGER, units INTEGER, unit_price_cents INTEGER
Primary key: sale_item_id
Foreign keys: sale_no references sales(sale_no); product_id references products(product_id).
### 2.5 Stock Movements
An audit log that answers "what changed and why" for every stock count.
Fields and types: movement_id INTEGER, product_id INTEGER, quantity_change INTEGER, reason TEXT, movement_timestamp TEXT
Primary key: movement_id
Foreign key: product_id references products(product_id)
### 2.6 Relationships and Constraints
Supplier → products: one-to-many. One supplier supplies many products; each product has exactly one supplier.
Sale → sale items: one-to-many. A sale has one or more lines.
Product → sale items: one-to-many. A product can appear on many lines (one per sale). With sale_items, this makes sales and products many-to-many.
Product → stock movements: one-to-many. A product has many logged movements.

| Constraint | Why it exists |
|---|---|
| `STRICT` on every table | Refuses a value of the wrong type, such as text in a price column. |
| `NOT NULL` on every required column | A product without a name, category, supplier, or price is useless. |
| `UNIQUE` on `supplier_name` | The same supplier should not be entered twice. |
| `UNIQUE` on `SKU` | Staff identify items by SKU, so two products can't share one. |
| `CHECK (price_cents >= 0)` and `CHECK (unit_price_cents >= 0)` | A negative price is impossible. |
| `CHECK (quantity >= 0)` | Stock can't go below zero. This is also what stops a sale or adjustment that needs more than we have. |
| `CHECK (reorder_level >= 0)` | A negative reorder level makes no sense. |
| `CHECK (units > 0)` on sale items | A sale line for zero or fewer units makes no sense. |
| `CHECK (reason IN ('restock', 'adjustment', 'sale'))` | Every movement must have one of the three known reasons. |
| Foreign keys on `supplier_id`, `sale_no`, and `product_id` | Refuse a product with an unknown supplier, and refuse deleting a product that has been sold. Turned on for every connection in `connect()`. |
| Index `idx_products_supplier` on `products(supplier_id)` | Used by the stock value by supplier report to find each supplier's products. |
| `CREATE TABLE IF NOT EXISTS` | Running the schema a second time does not fail or erase data. |

Money is stored as whole cents (INTEGER) so totals are exact. It is shown with two decimals only when printed.

## 3. Function Design
Database functions live in `inventory_db.py`, take the connection as the first parameter, and never print or ask for input. That way tests can pass in an in-memory database.

### 3.1 Database Functions
| Function | Inputs | Returns |
|---|---|---|
| `connect(path=DB_PATH)` | database file path, or `":memory:"` | a connection with foreign keys on and rows readable by column name |
| `create_tables(connection)` (in `seed_db.py`) | connection | nothing; runs `schema.sql` |
| `load_sample_data(connection)` (in `seed_db.py`) | connection | nothing; inserts the sample rows in one transaction |

`DB_PATH` comes from the `INVENTORY_DB` environment variable, or `inventory.db` next to the code.

### 3.2 Product Functions
| Function | Inputs | Returns |
|---|---|---|
| `add_product(connection, sku, name, category, supplier_id, price_cents, quantity, reorder_level)` | product fields | the new product id; raises `sqlite3.IntegrityError` for a duplicate SKU, unknown supplier, or negative price or quantity |
| `get_product(connection, product_id)` | product id | one row with the supplier's name (using a join), or `None` |
| `update_price(connection, product_id, new_price_cents)` | id and new price | `True` if the product exists, `False` if not |
| `delete_product(connection, product_id)` | product id | `True` if deleted, `False` if missing; raises `sqlite3.IntegrityError` if the product has been sold |

### 3.3 Search Function
`search_products(connection, text="", category=None, max_price_cents=None, in_stock_only=False, low_stock_only=False)` returns a list of products whose name, SKU, or supplier name contains the text, ignoring case, sorted by name. The filters are optional and can be combined. Every value goes into the query through a `?` placeholder.

### 3.4 Report Functions
| Function | Returns |
|---|---|
| `stock_value_by_supplier(connection)` | supplier name and total stock value in cents, highest first |
| `low_stock(connection)` | SKU, name, quantity, reorder level, and units short for products at or below their reorder level |
| `sales_by_product(connection)` | product name, units sold, and revenue in cents, highest revenue first |
| `never_sold(connection)` | SKU and name of products that appear in no sale |

### 3.5 Stock and Sales Functions
| Function | Inputs | Returns |
|---|---|---|
| `restock(connection, product_id, amount, now=None)` | id, positive amount, optional time | nothing; raises `ValueError` for an amount of 0 or less or an unknown product |
| `adjust_stock(connection, product_id, quantity_change, now=None)` | id, signed change, optional time | nothing; raises `sqlite3.IntegrityError` if stock would go negative |
| `record_sale(connection, items, now=None)` | list of `(product_id, units)` pairs, optional time | the new sale number; raises an error and saves nothing if any line fails |

Helpers used inside these transactions, which never commit by themselves:
- `timestamp_text(now=None)` returns the given time, or the current UTC time, as text.
- `change_stock(connection, product_id, quantity_change)` adds a signed amount to stock.
- `log_movement(connection, product_id, quantity_change, reason, timestamp)` inserts one stock movement.

### 3.6 Backup Function
`backup_database(source_path, backup_folder)` copies the live database with SQLite's `backup()` function and returns the backup file's path, named `inventory-YYYY-MM-DD.db`.

## 4. Transaction Design
Each change below runs inside one `with connection:` block. If every step succeeds, the block commits them together. If any step raises an error, the block rolls back every step since it began and the error goes up to the caller.

### 4.1 Restock
1. Refuse an amount of 0 or less with a `ValueError`, before touching the database.
2. Add the amount to the product's quantity. If no row changed, the product is unknown, so raise a `ValueError`.
3. Insert a `restock` movement with the amount and the time.

If step 2 or 3 fails, nothing is saved.

### 4.2 Adjust Stock
1. Add the signed change to the product's quantity. The `quantity >= 0` check refuses a result below zero.
2. Insert an `adjustment` movement with the change and the time.

If step 1 fails, step 2 never runs and the stock is unchanged.

### 4.3 Record Sale
1. Refuse the same product appearing twice in the list, before touching the database.
2. Insert the sale row and keep its new sale number.
3. For each line:
   - look up the product's current price (an unknown product raises a `ValueError`),
   - insert the sale line at that price,
   - reduce the stock (the `quantity >= 0` check refuses selling more than we have),
   - insert a `sale` movement with a negative change.
4. Return the sale number.

### 4.4 Failure and Rollback Behavior
If any line of a sale fails, everything already done in that call is undone: the sale row, every line already added, every stock reduction, and every movement. The database looks exactly as it did before the call. The README shows this with a real before and after.

## 5. Testing Strategy
- Tests are written first with pytest.
- A fixture in `conftest.py` gives each test a fresh `connect(":memory:")` database with the schema and the sample data, so tests never touch the real file or affect each other.
- Tests check that bad input is refused, not only the happy path. `parametrize` covers negative prices and quantities, search matching name, SKU, and supplier, and restock amounts of zero or less.
- The most important tests compare a snapshot of the database before and after a failed sale, a refused adjustment, and a refused restock, and require them to be identical.
- Stock and sale tests pass a fixed time so timestamps can be checked.
- The backup test uses `tmp_path` and checks `PRAGMA integrity_check` and the row counts.
- At least 23 tests. CI runs pytest, ruff, and the tests inside the Docker image.

## 6. Git and Development Plan
Only setup files and PLAN.md go straight to `main`. Everything else comes through these pull requests, in order, each with a passing CI run before merging:
1. `feature/database-and-seed`: schema, seed script, connect(), CI
2. `feature/products-and-search`: product functions and search
3. `feature/reports`: the four reports and their expected results in the README
4. `feature/stock-and-sales`: restock, adjust, record a sale, and the failed sale example
5. `feature/menu-and-container`: menu, backup, `INVENTORY_DB`, Dockerfile, `.dockerignore`, docker CI job
6. `feature/low-stock-banner`: the 1.1.0 change, CHANGELOG, and release documentation

Commit messages start with a verb, tests are committed before the code they test, and each branch is deleted after merging.

## 7. Release, Docker, and Backup Plan
- The image starts from a pinned `python:3.12-slim`. It copies `requirements.txt` and installs packages before copying the code, so code changes reuse the cached package layer.
- The database lives at `/data/inventory.db` in a Docker volume, so it survives new containers.
- 1.0.0: after PR 5 is merged, run the tests, tag `v1.0.0` on `main`, and build `inventory:1.0.0`.
- 1.1.0: build the banner on `feature/low-stock-banner`, build `inventory:1.1.0`, and after the PR is merged, tag `v1.1.0` on `main`.
- Backup: before releasing, back up with SQLite's backup function, then check the copy with `PRAGMA integrity_check` and compare row counts with the original.
- Restore: stop the program and copy the backup file over the database file.
- Rollback: start `inventory:1.0.0` with the same volume. 1.1.0 does not change the database layout, so the data stays intact.