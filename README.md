# inventory-management-system

## Sample data

`python seed_db.py` builds a fresh `inventory.db` and prints:

    Row counts:
      suppliers: 4
      products: 12
      sales: 5
      sale_items: 12
      stock_movements: 0

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

## Configuration

| Variable | Meaning | Default |
|---|---|---|
| `INVENTORY_DB` | Path of the SQLite database file | `inventory.db` next to the code |

## Running with Docker

Build the image:

```
docker build -t inventory .
```

```
[+] Building 18.6s (11/11) FINISHED
 => [1/6] FROM docker.io/library/python:3.12-slim
 => [2/6] WORKDIR /app
 => [3/6] COPY requirements.txt .
 => [4/6] RUN pip install --no-cache-dir -r requirements.txt
 => [5/6] COPY . .
 => [6/6] RUN mkdir -p /data
 => => naming to docker.io/library/inventory:latest
```

Run the tests inside the image:

```
docker run --rm inventory python -m pytest -q
.....................................                                    [100%]
37 passed in 0.04s
```

Seed the database into a volume, then start the menu:

```
docker run --rm -v inventory-data:/data inventory python seed_db.py
docker run -it --rm -v inventory-data:/data inventory
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