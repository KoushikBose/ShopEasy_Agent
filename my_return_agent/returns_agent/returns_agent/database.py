"""ShopEasy's database. Run  python database.py  to create fresh sample data.

Who uses what:
    get_orders tool      ->  get_customer_orders
    guardrails (checks)  ->  get_order_for_customer, is_return_booked, is_in_stock
    actions (changes)    ->  add_return, reduce_stock
    staff in the app     ->  get_pending_returns, update_return_status
"""

import sqlite3
from datetime import date, timedelta

FILE = "shopeasy.db"


# Runs any SQL query and gives back the rows
def run_sql(sql, values=()):
    with sqlite3.connect(FILE) as con:
        con.row_factory = sqlite3.Row
        return [dict(row) for row in con.execute(sql, values)]


# ---------- used by the get_orders tool

# Gets all orders of a customer, and shows if a return is booked
def get_customer_orders(customer_id):
    return run_sql("""
        SELECT orders.*, returns.type AS return_type, returns.status AS return_status
        FROM orders
        LEFT JOIN returns ON orders.order_id = returns.order_id
        WHERE orders.customer_id = ?
    """, (customer_id,))


# ---------- guardrails: checks before a return or exchange is booked

# Gets one order, but only if it belongs to this customer
def get_order_for_customer(order_id, customer_id):
    rows = run_sql("SELECT * FROM orders WHERE order_id = ? AND customer_id = ?", (order_id, customer_id))
    if len(rows) == 0:
        return None      # not this customer's order (or no such order)
    return rows[0]       # the order


# Tells if this order already has a return or exchange
def is_return_booked(order_id):
    return len(run_sql("SELECT * FROM returns WHERE order_id = ?", (order_id,))) > 0


# Tells if this item is available in this size
def is_in_stock(item, size):
    return len(run_sql("SELECT * FROM stock WHERE item = ? AND size = ? AND quantity > 0", (item, size))) > 0


# ---------- actions: change the data after the checks pass

# Saves a new return or exchange
def add_return(order_id, type, status, details):
    run_sql("INSERT INTO returns (order_id, type, status, details) VALUES (?, ?, ?, ?)",
            (order_id, type, status, details))


# Takes one piece out of stock (for an exchange)
def reduce_stock(item, size):
    run_sql("UPDATE stock SET quantity = quantity - 1 WHERE item = ? AND size = ?", (item, size))


# ---------- staff approval in the app (refunds above Rs 10,000)

# Gets the returns that are waiting for staff approval
def get_pending_returns():
    return run_sql("""
        SELECT returns.return_id, returns.order_id, orders.item, returns.details
        FROM returns
        JOIN orders ON returns.order_id = orders.order_id
        WHERE returns.status = 'waiting_for_staff'
    """)


# Staff approves or rejects a return
def update_return_status(return_id, status):
    run_sql("UPDATE returns SET status = ? WHERE return_id = ?", (status, return_id))


# ---------- sample data

# Gives the date n days before today
def days_ago(n):
    return str(date.today() - timedelta(days=n))


# Creates the tables and fills them with sample data
def reset():
    for table in ["customers", "orders", "returns", "stock"]:
        run_sql(f"DROP TABLE IF EXISTS {table}")

    run_sql("CREATE TABLE customers (customer_id TEXT, name TEXT)")
    run_sql("CREATE TABLE orders (order_id TEXT, customer_id TEXT, item TEXT, category TEXT, size TEXT, price INTEGER, delivered_on TEXT)")
    run_sql("CREATE TABLE returns (return_id INTEGER PRIMARY KEY, order_id TEXT, type TEXT, status TEXT, details TEXT)")
    run_sql("CREATE TABLE stock (item TEXT, size TEXT, quantity INTEGER)")

    customers = [
        ("C-101", "Priya Menon"),
        ("C-102", "Rahul Verma"),
        ("C-103", "Anita Desai"),
        ("C-104", "Vikram Shah"),
        ("C-105", "Neha Kapoor"),
        ("C-106", "Arjun Nair"),
    ]
    orders = [
        ("ORD-5001", "C-101", "Cotton Kurta",                         "clothing",    "M",  1299,  days_ago(6)),
        ("ORD-5002", "C-101", "Sequin Party Dress",                   "party_wear",  "S",  3499,  days_ago(9)),
        ("ORD-5003", "C-102", "Stride Running Shoes",                 "footwear",    "8",  2799,  days_ago(4)),
        ("ORD-5004", "C-102", "Zentro Vision 55 4K LED TV (ZT-55U5)", "electronics", None, 36990, days_ago(3)),
        ("ORD-5005", "C-103", "Sheesham Wood Coffee Table",           "home",        None, 18500, days_ago(5)),
        ("ORD-5006", "C-104", "Cotton Kurta",                         "clothing",    "L",  1299,  days_ago(3)),
        ("ORD-5007", "C-104", "Linen Kurta",                          "clothing",    "L",  1899,  days_ago(8)),
        ("ORD-5008", "C-104", "Slim Fit Jeans",                       "clothing",    "34", 2199,  days_ago(12)),
        ("ORD-5009", "C-104", "Steel Pressure Cooker 5L",             "home",        None, 2450,  days_ago(2)),
        ("ORD-5010", "C-105", "Stride Running Shoes",                 "footwear",    "6",  2799,  days_ago(5)),
        ("ORD-5011", "C-105", "Urban Walk Sneakers",                  "footwear",    "6",  3299,  days_ago(2)),
        ("ORD-5012", "C-105", "Nexa Buds 3 (NX-B3)",                  "electronics", None, 2499,  days_ago(6)),
        ("ORD-5013", "C-105", "Nexa Buds 3 Pro (NX-B3P)",             "electronics", None, 4999,  days_ago(1)),
        ("ORD-5014", "C-105", "Silk Saree",                           "clothing",    None, 5499,  days_ago(10)),
        ("ORD-5015", "C-106", "Sequin Party Dress",                   "party_wear",  "M",  3499,  days_ago(10)),
        ("ORD-5016", "C-106", "Sequin Party Dress",                   "party_wear",  "L",  3499,  days_ago(2)),
        ("ORD-5017", "C-106", "Leather Formal Shoes",                 "footwear",    "9",  4299,  days_ago(4)),
    ]
    stock = [
        ("Cotton Kurta", "S", 4), 
        ("Cotton Kurta", "L", 2),
        ("Stride Running Shoes", "7", 3), 
        ("Stride Running Shoes", "9", 0),
        ("Linen Kurta", "M", 5), 
        ("Linen Kurta", "XL", 1),
        ("Urban Walk Sneakers", "7", 2),
        ("Leather Formal Shoes", "10", 2),
    ]

    for row in customers:
        run_sql("INSERT INTO customers VALUES (?, ?)", row)
    for row in orders:
        run_sql("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", row)
    for row in stock:
        run_sql("INSERT INTO stock VALUES (?, ?, ?)", row)


if __name__ == "__main__":
    reset()
    print("Created shopeasy.db: 6 customers, 17 orders")