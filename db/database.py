"""
SQLite Database Layer
---------------------
Single point of access to the persistence backend (SQLite only).
Used by the InventorySystem, CentralRegistry, and Command logger.
"""
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "aura.db")


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


@contextmanager
def get_conn():
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables if they do not exist and seed default data."""
    _ensure_dir()
    with get_conn() as conn:
        c = conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kiosk_type TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            emergency_price REAL NOT NULL DEFAULT 0.0,
            stock INTEGER NOT NULL DEFAULT 0,
            requires_refrigeration INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS bundles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kiosk_type TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL DEFAULT 0.0,
            emergency_price REAL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS bundle_items (
            bundle_id INTEGER NOT NULL,
            child_product_id INTEGER,
            child_bundle_id INTEGER,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (bundle_id) REFERENCES bundles(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT DEFAULT CURRENT_TIMESTAMP,
            kiosk_type TEXT,
            command TEXT,
            payload TEXT,
            status TEXT,
            message TEXT
        );

        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT DEFAULT CURRENT_TIMESTAMP,
            actor TEXT,
            action TEXT,
            detail TEXT
        );
        """)

        # Seed default products only the first time
        cnt = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if cnt == 0:
            seed = [
                # PHARMACY
                ("PHARMACY", "Surgical Mask", 5.0, 4.0, 50, 0),
                ("PHARMACY", "Band Aid Pack", 10.0, 8.0, 80, 0),
                ("PHARMACY", "Paracetamol", 8.0, 6.0, 120, 0),
                ("PHARMACY", "Insulin Vial", 45.0, 35.0, 12, 1),
                # FOOD
                ("FOOD", "Sandwich", 6.0, 5.0, 30, 1),
                ("FOOD", "Cola Can", 2.5, 2.0, 100, 1),
                ("FOOD", "Energy Bar", 3.0, 2.5, 60, 0),
                ("FOOD", "Bottled Water", 1.5, 1.0, 200, 0),
                # EMERGENCY
                ("EMERGENCY", "Water Bottle (1L)", 0.5, 0.2, 500, 0),
                ("EMERGENCY", "First-Aid Kit", 12.0, 5.0, 40, 0),
                ("EMERGENCY", "Emergency Blanket", 4.0, 1.0, 150, 0),
                ("EMERGENCY", "Ration Pack", 8.0, 2.0, 300, 0),
            ]
            c.executemany(
                "INSERT INTO products (kiosk_type,name,price,emergency_price,stock,requires_refrigeration) VALUES (?,?,?,?,?,?)",
                seed,
            )

            # Seed bundles (Composite pattern)
            c.execute("INSERT INTO bundles (kiosk_type, name) VALUES (?,?)",
                      ("EMERGENCY", "Disaster Relief Kit"))
            bundle_id = c.lastrowid
            # link bundle to products
            water = c.execute("SELECT id FROM products WHERE name=?",
                              ("Water Bottle (1L)",)).fetchone()[0]
            kit = c.execute("SELECT id FROM products WHERE name=?",
                            ("First-Aid Kit",)).fetchone()[0]
            blanket = c.execute("SELECT id FROM products WHERE name=?",
                                ("Emergency Blanket",)).fetchone()[0]
            c.executemany(
                "INSERT INTO bundle_items (bundle_id, child_product_id, quantity) VALUES (?,?,?)",
                [(bundle_id, water, 4), (bundle_id, kit, 1), (bundle_id, blanket, 2)],
            )

        # default config
        defaults = [("admin_pin", "admin123"), ("emergency_mode", "0"), ("dispenser", "spiral")]
        for k, v in defaults:
            c.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (k, v))
