# Inventory Management System

A terminal inventory system for a small hardware store. It keeps suppliers,
products, sales, and a log of every stock movement in a SQLite database. Staff
can search products with filters, look up and add products, run reports,
restock, and record sales that either save completely or not at all. It runs
locally or in a Docker container, with the database kept in a volume.

## Project layout

| File | Purpose |
|---|---|
| `schema.sql` | The five tables and their rules. Safe to run more than once. |
| `inventory_db.py` | Every database function. No `input()` or `print()`. |
| `seed_db.py` | Builds a fresh database with sample data and prints the row counts. |
| `main.py` | The terminal menu. All input and output lives here. |
| `tests/` | pytest tests, each using a fresh in-memory database. |
| `Dockerfile`, `.dockerignore` | The container image. |
| `CHANGELOG.md` | What changed in each version. |
| `PLAN.md` | The design written before the code. |

## Running locally

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed_db.py
python main.py
```

`seed_db.py` builds a fresh `inventory.db` with sample data. Running it again resets the data.

## Configuration

| Variable | Meaning | Default |
|---|---|---|
| `INVENTORY_DB` | Path of the SQLite database file | `inventory.db` next to the code |

The Docker image sets `INVENTORY_DB=/data/inventory.db`.

## Running the tests

```
pytest -q
ruff check .
```

```
......................................                                   [100%]
38 passed in 0.04s
All checks passed!
```

Each test gets a fresh in-memory database loaded with the sample data, so the
real `inventory.db` is never touched. CI runs the tests, ruff, and a Docker
build that runs the tests inside the image on every push and pull request.

## Sample data

`python seed_db.py` prints:

```
Row counts:
  suppliers: 4
  products: 12
  sales: 5
  sale_items: 12
  stock_movements: 0
```

The data has 12 products in 3 categories (Hand Tools, Fasteners, Safety
Equipment), 2 products that were never sold (Earplugs Box, Dust Masks 10pk),
and 2 products at or below their reorder level (Adjustable Wrench, Claw Hammer).

## Expected report results

Money is stored as whole cents and shown here with two decimals.

**Stock value by supplier** (highest first)

| Supplier | Stock value |
|---|---|
| Global Building Supplies | $738.64 |
| FastFix Fasteners | $720.75 |
| ToolCorp Industries | $269.65 |
| Acme Hardware Wholesale | $128.95 |

**Low stock**

| SKU | Product | In stock | Reorder level | Units short |
|---|---|---|---|---|
| SKU-H002 | Adjustable Wrench | 2 | 5 | 3 |
| SKU-H001 | Claw Hammer | 5 | 5 | 0 |

**Sales by product** (highest revenue first)

| Product | Units sold | Revenue |
|---|---|---|
| Adjustable Wrench | 4 | $58.00 |
| Claw Hammer | 2 | $39.98 |
| Work Gloves | 2 | $25.98 |
| Tape Measure | 2 | $17.98 |
| Hex Bolts 50pk | 2 | $17.00 |
| Wood Screws 100pk | 2 | $12.98 |
| Wall Anchors | 3 | $11.97 |
| Safety Glasses | 1 | $7.99 |
| Utility Knife | 1 | $5.99 |
| Nails 2in 1lb | 1 | $4.99 |

**Never sold**

| SKU | Product |
|---|---|
| SKU-S204 | Dust Masks 10pk |
| SKU-S203 | Earplugs Box |

## What happens when a sale fails halfway

`record_sale` runs every step inside one `with connection:` block. Below, line 1
(1 Utility Knife) is valid, but line 2 asks for 99 Tape Measures when only 20 are
in stock. Line 1 was already inserted and its stock reduced when line 2 failed,
but the rollback undid it too.

```
Before:
  sales: 5
  sale_items: 12
  stock_movements: 0
  Tape Measure stock: 20
  Utility Knife stock: 15

Call: db.record_sale(connection, [(4, 1), (3, 99)])
Error: CHECK constraint failed: quantity >= 0

After:
  sales: 5
  sale_items: 12
  stock_movements: 0
  Tape Measure stock: 20
  Utility Knife stock: 15
```

Nothing changed: no sale row, no sale lines, no stock movements, and no stock change.

## Deploying with Docker

Build the image with a version tag:

```
docker build -t inventory:1.1.0 .
```

```
[+] Building 0.6s (11/11) FINISHED                            docker:desktop-linux
 => [internal] load metadata for docker.io/library/python:3.12-slim           0.4s
 => [1/6] FROM docker.io/library/python:3.12-slim@sha256:b18b261e1b4974b4f32  0.0s
 => CACHED [2/6] WORKDIR /app                                                 0.0s
 => CACHED [3/6] COPY requirements.txt .                                      0.0s
 => CACHED [4/6] RUN pip install --no-cache-dir -r requirements.txt           0.0s
 => [5/6] COPY . .                                                            0.0s
 => [6/6] RUN mkdir -p /data                                                  0.1s
 => => naming to docker.io/library/inventory:1.1.0                            0.0s
```

Steps 2 to 4 are `CACHED` because only the code changed since the last build.
The Dockerfile copies `requirements.txt` and installs packages before copying
the code, so Docker reuses the package layer and only redoes the last steps.

Run the tests inside the image:

```
docker run --rm inventory:1.1.0 python -m pytest -q
```

Seed the database into a volume, then start the menu. `-it` is needed so the
menu can read what you type.

```
docker run --rm -v inventory-data:/data inventory:1.1.0 python seed_db.py
docker run -it --rm -v inventory-data:/data inventory:1.1.0
```

### Persistence check

The database lives in the `inventory-data` volume, not inside the container,
so it survives when a container is removed and a new one starts.

1. Seed the volume:

```
docker run --rm -v inventory-data:/data inventory python seed_db.py
Row counts:
  suppliers: 4
  products: 12
  sales: 5
  sale_items: 12
  stock_movements: 0
```

2. First container: restock product 1 (Claw Hammer, 5 in stock) by 10, then quit.
   `--rm` deletes this container when it exits.

```
docker run -it --rm -v inventory-data:/data inventory
Choose an option: 4
Product id: 1
Units to add: 10
Restocked.
Choose an option: 0
```

3. A brand-new container with the same volume: the change is still there.

```
docker run -it --rm -v inventory-data:/data inventory
Choose an option: 2
Product id: 1
1. SKU-H001  Claw Hammer (Hand Tools) from Acme Hardware Wholesale, $19.99, 15 in stock, reorder at 5
Choose an option: 0
```

## Releases

| Version | Git tag | Docker image | Change |
|---|---|---|---|
| 1.0.0 | `v1.0.0` | `inventory:1.0.0` | First release |
| 1.1.0 | `v1.1.0` | `inventory:1.1.0` | Low stock banner when the menu starts |

See [CHANGELOG.md](CHANGELOG.md) for details.

## Backup and restore

Backups use SQLite's own backup function, which copies a consistent snapshot
even while the database is in use. From the menu, choose `10. Back up the database`.
The copy is saved as `backups/inventory-YYYY-MM-DD.db` next to the database.
Take a backup before every release.

### Backup check

This makes a backup inside the volume, then checks both files:

```
docker run --rm -i -v inventory-data:/data inventory:1.1.0 python - <<'EOF'
from contextlib import closing

import inventory_db as db
import seed_db

backup = db.backup_database(db.DB_PATH, "/data/backups")
for label, path in [("Original", db.DB_PATH), ("Backup", backup)]:
    with closing(db.connect(path)) as connection:
        check = connection.execute("PRAGMA integrity_check").fetchone()[0]
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in seed_db.TABLES
        }
    print(f"{label}: {path}")
    print(f"  integrity_check: {check}")
    print(f"  row counts: {counts}")
EOF
```

```
Original: /data/inventory.db
  integrity_check: ok
  row counts: {'suppliers': 4, 'products': 12, 'sales': 5, 'sale_items': 12, 'stock_movements': 1}
Backup: /data/backups/inventory-2026-11-02.db
  integrity_check: ok
  row counts: {'suppliers': 4, 'products': 12, 'sales': 5, 'sale_items': 12, 'stock_movements': 1}
```

The backup passes `PRAGMA integrity_check` and has the same row counts as the original.

### Restore

Stop the program first, then copy the backup over the database file.

Locally:

```
cp backups/inventory-2026-11-02.db inventory.db
```

In Docker:

```
docker run --rm -v inventory-data:/data inventory:1.0.0 cp /data/backups/inventory-2026-11-02.db /data/inventory.db
```

## Rolling back

Roll back by starting the previous image with the same volume. The data lives in
the volume, not the image, and 1.1.0 did not change the database layout, so
1.0.0 reads it as it is. If a release also damaged data, restore the backup
taken before the release.

```
docker run -it --rm -v inventory-data:/data inventory:1.0.0
```

### Rollback check

1. Running 1.1.0: the banner shows, and Tape Measure is restocked from 20 to 25.

```
docker run -it --rm -v inventory-data:/data inventory:1.1.0
*** Low stock: 1 product(s) at or below reorder level ***

Choose an option: 4
Product id: 3
Units to add: 5
Restocked.
Choose an option: 0
```

2. Rolled back to 1.0.0: no banner, and the data written by 1.1.0 is still there.

```
docker run -it --rm -v inventory-data:/data inventory:1.0.0

Choose an option: 2
Product id: 3
3. SKU-H003  Tape Measure (Hand Tools) from ToolCorp Industries, $8.99, 25 in stock, reorder at 10
Choose an option: 2
Product id: 1
1. SKU-H001  Claw Hammer (Hand Tools) from Acme Hardware Wholesale, $19.99, 15 in stock, reorder at 5
Choose an option: 0
```

No banner appears, which confirms version 1.0.0 is running, and the change made
under 1.1.0 (Tape Measure at 25) is still there.

## Self-review

**What I would do differently.** I would design the schema with every rule from
the start. I first wrote it with `DROP TABLE`, which erased data on a second run,
and had to change it to `CREATE TABLE IF NOT EXISTS`. I would also add
`UNIQUE (sale_no, product_id)` to `sale_items`, so the database refuses the same
product twice in a sale instead of relying on a check in Python. In the menu, I
would ask for prices in dollars instead of cents, since typing 1999 for $19.99
is easy to get wrong. Finally, `friendly_message` picks a message by matching
text in the SQLite error, which works but would break if the wording changed;
checking the inputs before saving would give more precise messages.

**Something I want a reviewer to check.** Deleting a product is refused when it
has sales, which is what the assignment asks for. But `stock_movements` also
points at products, so a product that was only ever restocked, and never sold,
can't be deleted either, and the database reports it with the same foreign key
error. I'm not sure whether that product should be deletable, which would mean
also deleting or keeping its movement history, or whether keeping the history
and refusing the delete is the right call for an audit log.