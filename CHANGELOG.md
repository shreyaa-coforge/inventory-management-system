# Changelog

All notable changes to this project are listed here. Versions follow
semantic versioning (MAJOR.MINOR.PATCH).

## [1.1.0] - 2026-11-02

### Added
- The menu shows a banner with the number of low stock products when it starts.

## [1.0.0] - 2026-11-02

### Added
- SQLite database with suppliers, products, sales, sale items, and stock movements, with rules enforced by the database.
- Add, look up, reprice, and delete products.
- Search by name, SKU, or supplier with category, max price, in stock, and low stock filters.
- Reports: stock value by supplier, low stock, sales by product, and never sold.
- Restock, adjust, and record a sale, each as a single transaction with a stock movement log.
- Terminal menu with friendly error messages.
- Database backup using SQLite's backup function.
- Docker image, with the database location set by `INVENTORY_DB` and kept in a volume.