from abc import ABC, abstractmethod
import sqlite3
import os

# --- 0. CLOUD DATABASE (SQLite Persistence) ---
class KioskDatabase:
    def __init__(self):
        self.db_path = "kiosk_os.db"
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS inventory 
                           (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            kiosk_type TEXT, name TEXT, price REAL, stock INTEGER)''')
            # Pre-populate if empty
            if not self.get_items("pharmacy_factory") and not self.get_items("food_factory"):
                self.add_item("pharmacy_factory", "Advil", 15.0, 10)
                self.add_item("pharmacy_factory", "Mask", 5.0, 50)
                self.add_item("food_factory", "Coke", 2.0, 20)
                self.add_item("food_factory", "Chips", 1.5, 30)

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

# --- 1. PRODUCT CLASSES ---
class Product:
    def __init__(self, name, price, stock, db_id=None):
        self.name, self.price, self.stock, self.db_id = name, price, stock, db_id
    def is_available(self): return self.stock > 0
    def reduce_stock(self, db_handler): 
        if self.stock > 0:
            self.stock -= 1
            db_handler.update_stock(self.db_id, self.stock)

# --- 2. COMPONENT INTERFACES ---
class IPayment(ABC):
    @abstractmethod
    def pay(self, amount): pass

class IDispenser(ABC):
    @abstractmethod
    def dispense(self, item): pass

# --- 3. CONCRETE COMPONENTS ---
class UPIPayment(IPayment):
    def pay(self, amount): return f"UPI: Paid ${amount}"

class CardPayment(IPayment):
    def pay(self, amount): return f"Card: Paid ${amount}"

class SpiralDispenser(IDispenser):
    def dispense(self, item): return f"Spiral spinning... {item} dropped."

class RoboticDispenser(IDispenser):
    def dispense(self, item): return f"Robot arm picking... {item} ready."

# --- 4. THE FACTORY PATTERN ---
class KioskFactory(ABC):
    @abstractmethod
    def get_payment_method(self) -> IPayment: pass
    @abstractmethod
    def get_dispenser_type(self) -> IDispenser: pass
    @abstractmethod
    def get_kiosk_type(self): pass

class PharmacyFactory(KioskFactory):
    def get_payment_method(self): return CardPayment()
    def get_dispenser_type(self): return RoboticDispenser()
    def get_kiosk_type(self): return "pharmacy_factory"

class FoodFactory(KioskFactory):
    def get_payment_method(self): return UPIPayment()
    def get_dispenser_type(self): return SpiralDispenser()
    def get_kiosk_type(self): return "food_factory"

# --- 5. THE KIOSK (Client) ---
class Kiosk:
    def __init__(self, factory: KioskFactory, db_handler: KioskDatabase):
        self.db = db_handler
        self.k_type = factory.get_kiosk_type()
        self.payment = factory.get_payment_method()
        self.dispenser = factory.get_dispenser_type()
        self.inventory = self.db.get_items(self.k_type)

    def process_purchase(self, item_key):
        item = self.inventory.get(item_key)
        if item and item.is_available():
            # Reduce stock in Memory AND Database
            item.reduce_stock(self.db)
            pay_msg = self.payment.pay(item.price)
            disp_msg = self.dispenser.dispense(item.name)
            return f"{pay_msg} | {disp_msg}"
        return "Failed: Out of stock"

    def add_item(self, name, price, stock):
        self.db.add_item(self.k_type, name, price, stock)
        self.inventory = self.db.get_items(self.k_type) # Sync memory
        return f"Admin: Added {name}"

    def update_item_stock(self, item_id, new_stock):
        self.db.update_stock(item_id, new_stock)
        self.inventory = self.db.get_items(self.k_type) # Sync memory
        return "Admin: Stock Updated"

    def delete_item(self, item_id):
        self.db.delete_item(item_id)
        self.inventory = self.db.get_items(self.k_type) # Sync memory
        return "Admin: Item Removed"
