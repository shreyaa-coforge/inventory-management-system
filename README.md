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