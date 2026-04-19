from abc import ABC, abstractmethod
import sqlite3

# --- 0. CLOUD DATABASE (Persistence) ---
class KioskDatabase:
    def __init__(self):
        self.db_path = "proxy_os.db"
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS inventory 
                           (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            kiosk_type TEXT, name TEXT, price REAL, stock INTEGER)''')
            if not self.get_items("pharmacy_proxy"):
                conn.execute("INSERT INTO inventory (kiosk_type, name, price, stock) VALUES (?,?,?,?)", 
                             ("pharmacy_proxy", "Advil", 12.0, 10))

    def add_item(self, k_type, name, price, stock):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO inventory (kiosk_type, name, price, stock) VALUES (?,?,?,?)", 
                         (k_type, name, price, stock))

    def get_items(self, k_type):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT name, price, stock, id FROM inventory WHERE kiosk_type=?", (k_type,)).fetchall()
            return {r[0]: Product(r[0], r[1], r[2], r[3]) for r in rows}

    def update_stock(self, item_id, new_stock):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE inventory SET stock=? WHERE id=?", (new_stock, item_id))

    def delete_item(self, item_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM inventory WHERE id=?", (item_id,))

# --- 1. PRODUCT CLASS ---
class Product:
    def __init__(self, name, price, stock, db_id=None):
        self.name, self.price, self.stock, self.db_id = name, price, stock, db_id

# --- 2. THE PROXY PATTERN (Subject Interface) ---
class IKiosk(ABC):
    @abstractmethod
    def get_inventory(self): pass
    @abstractmethod
    def process_purchase(self, item_key): pass
    @abstractmethod
    def admin_mod(self, action, data): pass

# --- 3. REAL SUBJECT (The core system) ---
class RealKiosk(IKiosk):
    def __init__(self, kiosk_id, db):
        self.kiosk_id = kiosk_id
        self.db = db
        self.inventory = self.db.get_items(kiosk_id)

    def get_inventory(self):
        self.inventory = self.db.get_items(self.kiosk_id)
        return self.inventory

    def process_purchase(self, item_key):
        item = self.inventory.get(item_key)
        if item and item.stock > 0:
            item.stock -= 1
            self.db.update_stock(item.db_id, item.stock)
            return f"Dispensed: {item.name}"
        return "Denied: Out of Stock"

    def admin_mod(self, action, data):
        if action == "add":
            self.db.add_item(self.kiosk_id, data['n'], data['p'], data['s'])
        elif action == "delete":
            self.db.delete_item(data['id'])
        elif action == "update":
            self.db.update_stock(data['id'], data['s'])
        self.inventory = self.db.get_items(self.kiosk_id)
        return f"System: {action.title()} logic executed."

# --- 4. THE PROTECTION PROXY ---
class KioskProxy(IKiosk):
    def __init__(self, kiosk_id, db):
        self._real_kiosk = None # Lazy initialization
        self.kiosk_id = kiosk_id
        self.db = db
        self.is_admin = False

    def _get_real(self):
        if self._real_kiosk is None: 
            self._real_kiosk = RealKiosk(self.kiosk_id, self.db)
        return self._real_kiosk

    def authenticate(self, pwd):
        if pwd == "admin":
            self.is_admin = True
            return True
        return False

    def get_inventory(self):
        # Always allow public to view inventory
        return self._get_real().get_inventory()

    def process_purchase(self, item_key):
        # Custom logging logic at the proxy level
        print(f"LOG: Proxy intercepting purchase for {item_key} via node {self.kiosk_id}")
        return self._get_real().process_purchase(item_key)

    def admin_mod(self, action, data):
        # SECURITY PROTECTION: Intercept sensitive calls
        if self.is_admin:
            print(f"SECURITY: Authorized modification request: {action}")
            return self._get_real().admin_mod(action, data)
        return "SECURITY ALERT: Access Denied. Administrator proxy key required."
