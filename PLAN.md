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
## 3. Function Design
### 3.1 Database Functions
### 3.2 Product Functions
### 3.3 Search Function
### 3.4 Report Functions
### 3.5 Stock and Sales Functions
### 3.6 Backup Function

## 4. Transaction Design
### 4.1 Restock
### 4.2 Adjust Stock
### 4.3 Record Sale
### 4.4 Failure and Rollback Behavior

## 5. Testing Strategy

## 6. Git and Development Plan

## 7. Release, Docker, and Backup Plan