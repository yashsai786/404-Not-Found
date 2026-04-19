from abc import ABC, abstractmethod
import sqlite3

class KioskDatabase:
    def __init__(self):
        self.db_path = "strategy_os.db"
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS inventory 
                           (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            name TEXT, price REAL, stock INTEGER)''')
            if not conn.execute("SELECT count(*) FROM inventory").fetchone()[0]:
                data = [("Energy Drink", 2.5, 20), ("Protein Bar", 3.0, 15), ("Headphones", 25.0, 5)]
                conn.executemany("INSERT INTO inventory (name, price, stock) VALUES (?,?,?)", data)

    def get_items(self):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT name, price, stock, id FROM inventory").fetchall()

    def add_item(self, name, price, stock):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO inventory (name, price, stock) VALUES (?,?,?)", (name, price, stock))

    def update_stock(self, item_id, new_stock):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE inventory SET stock=? WHERE id=?", (new_stock, item_id))

    def delete_item(self, item_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM inventory WHERE id=?", (item_id,))

class IDispenseStrategy(ABC):
    @abstractmethod
    def dispense(self, item_name): pass

class IPaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount): pass

class SpiralDispense(IDispenseStrategy):
    def dispense(self, item_name):
        return f"ALGO_SPIRAL: Rotating specific motor channel to drop {item_name} via gravity."

class RoboticDispense(IDispenseStrategy):
    def dispense(self, item_name):
        return f"ALGO_ROBOTIC: Coordinates (X,Y,Z) calculated. Arm picking {item_name} from shelf."

class UPIPayment(IPaymentStrategy):
    def pay(self, amount):
        return f"GATEWAY_UPI: Generating QR for ${amount}."

class CardPayment(IPaymentStrategy):
    def pay(self, amount):
        return f"GATEWAY_EMV: Processing chip transaction for ${amount}."

class StrategyKiosk:
    def __init__(self):
        self.dispense_strategy = SpiralDispense()
        self.payment_strategy = UPIPayment()
        self.db = KioskDatabase()

    def set_dispense_strategy(self, strategy: IDispenseStrategy):
        self.dispense_strategy = strategy

    def set_payment_strategy(self, strategy: IPaymentStrategy):
        self.payment_strategy = strategy

    def execute_sale(self, item_id, name, price):
        with sqlite3.connect(self.db.db_path) as conn:
            stock = conn.execute("SELECT stock FROM inventory WHERE id=?", (item_id,)).fetchone()[0]
            if stock > 0:
                conn.execute("UPDATE inventory SET stock=? WHERE id=?", (stock - 1, item_id))
                pay_log = self.payment_strategy.pay(price)
                disp_log = self.dispense_strategy.dispense(name)
                return {"payment": pay_log, "dispense": disp_log, "success": True}
        return {"success": False, "msg": "Out of Stock"}
