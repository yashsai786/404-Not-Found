from abc import ABC, abstractmethod
import sqlite3

# ==========================================
# 1. STRATEGY PATTERN (Hardware & Payment)
# ==========================================
class IPaymentStrategy(ABC):
    @abstractmethod
    def process(self, amount): pass

class CardPayment(IPaymentStrategy):
    def process(self, amount): return f"💳 CARD: Chip read successful. Charged ${amount}."

class UPIPayment(IPaymentStrategy):
    def process(self, amount): return f"📱 UPI: QR Scanned. Received ${amount}."

class IDispenseStrategy(ABC):
    @abstractmethod
    def dispense(self, item): pass

class SpiralDispense(IDispenseStrategy):
    def dispense(self, item): return f"🌀 SPIRAL: Rotating coil... {item} dropped."

class RoboticDispense(IDispenseStrategy):
    def dispense(self, item): return f"🤖 ROBOTIC: Arm picking {item}... Delivered."

# ==========================================
# 2. PROXY PATTERN (Access Control)
# ==========================================
class IAdminService(ABC):
    @abstractmethod
    def update_hardware(self, kiosk, method): pass
    @abstractmethod
    def add_item(self, kiosk, name, price, stock): pass
    @abstractmethod
    def delete_item(self, kiosk, item_id): pass
    @abstractmethod
    def update_stock(self, kiosk, item_id, qty): pass

class RealAdminService(IAdminService):
    def update_hardware(self, kiosk, method):
        if method == "robotic": kiosk.dispense_strat = RoboticDispense()
        else: kiosk.dispense_strat = SpiralDispense()
        return f"System: Hardware changed to {method.upper()}."

    def add_item(self, kiosk, name, price, stock):
        with sqlite3.connect(kiosk.db_path) as conn:
            conn.execute("INSERT INTO items (kiosk_type, name, price, stock) VALUES (?,?,?,?)", 
                         (kiosk.k_type, name, price, stock))
        return f"System: Added {name} to {kiosk.k_type} inventory."

    def delete_item(self, kiosk, item_id):
        with sqlite3.connect(kiosk.db_path) as conn:
            conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        return "System: Item deleted."

    def update_stock(self, kiosk, item_id, qty):
        with sqlite3.connect(kiosk.db_path) as conn:
            conn.execute("UPDATE items SET stock=? WHERE id=?", (qty, item_id))
        return "System: Stock updated."

class AdminProxy(IAdminService):
    def __init__(self):
        self._real = None
        self.is_auth = False

    def login(self, pwd):
        if pwd == "admin123":
            self.is_auth = True
            return True
        return False

    def update_hardware(self, kiosk, method):
        if self.is_auth:
            if not self._real: self._real = RealAdminService()
            return self._real.update_hardware(kiosk, method)
        return "ERROR: Unauthorized!"

    def add_item(self, kiosk, name, price, stock):
        if self.is_auth:
            if not self._real: self._real = RealAdminService()
            return self._real.add_item(kiosk, name, price, stock)
        return "ERROR: Unauthorized!"

    def delete_item(self, kiosk, item_id):
        if self.is_auth:
            if not self._real: self._real = RealAdminService()
            return self._real.delete_item(kiosk, item_id)
        return "ERROR: Unauthorized!"

    def update_stock(self, kiosk, item_id, qty):
        if self.is_auth:
            if not self._real: self._real = RealAdminService()
            return self._real.update_stock(kiosk, item_id, qty)
        return "ERROR: Unauthorized!"

# ==========================================
# 3. FACTORY PATTERN (Kiosk Construction)
# ==========================================
class UnifiedKiosk:
    def __init__(self, k_type):
        self.k_type = k_type
        # Factory sets default hardware based on type
        if k_type == "food":
            self.dispense_strat = SpiralDispense()
        else:
            self.dispense_strat = RoboticDispense()
            
        self.payment_strat = CardPayment() 
        self.db_path = "kiosk_master.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS items 
                           (id INTEGER PRIMARY KEY, kiosk_type TEXT, 
                            name TEXT, price REAL, stock INTEGER)""")
            # Pre-fill some data if empty
            if not conn.execute("SELECT count(*) FROM items").fetchone()[0]:
                data = [
                    ("pharmacy", "Advil", 10.0, 5),
                    ("pharmacy", "Mask", 5.0, 20),
                    ("food", "Coke", 2.5, 10),
                    ("food", "Chips", 1.5, 30)
                ]
                conn.executemany("INSERT INTO items (kiosk_type, name, price, stock) VALUES (?,?,?,?)", data)

    def set_payment_logic(self, method):
        if method == "upi": self.payment_strat = UPIPayment()
        else: self.payment_strat = CardPayment()

    def process_purchase(self, item_id, item_name, amount):
        with sqlite3.connect(self.db_path) as conn:
            # Check stock
            curr = conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()
            if curr and curr[0] > 0:
                # Deduct stock
                conn.execute("UPDATE items SET stock=? WHERE id=?", (curr[0]-1, item_id))
                p_log = self.payment_strat.process(amount)
                d_log = self.dispense_strat.dispense(item_name)
                return {"payment": p_log, "dispense": d_log, "success": True}
        return {"success": False, "msg": "Out of Stock!"}

class KioskFactory:
    @staticmethod
    def construct_kiosk(choice):
        # The Factory logic: creates the object with specified character
        return UnifiedKiosk(choice)
