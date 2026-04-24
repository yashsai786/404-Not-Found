"""
========================================
DESIGN PATTERN #8 — COMMAND (Behavioral)
========================================
Owner: Megha Lalwani
Purpose:
  Every operation (Purchase, Refund, Restock) is encapsulated as a Command
  object with execute() and undo() methods. Commands are persisted in the
  `transactions` SQLite table for replay / audit.
"""
from abc import ABC, abstractmethod
import json
from db.database import get_conn


class Command(ABC):
    name = "base"

    @abstractmethod
    def execute(self): ...

    def undo(self):
        return {"ok": False, "message": "undo not supported"}

    # ---- persistence helper used by every concrete command ----
    def _record(self, kiosk_type, payload, status, message):
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO transactions (kiosk_type,command,payload,status,message) "
                "VALUES (?,?,?,?,?)",
                (kiosk_type, self.name, json.dumps(payload), status, message),
            )
            return cur.lastrowid


class PurchaseCommand(Command):
    name = "PURCHASE"

    def __init__(self, kiosk_facade, product_id, qty, gateway, item_type="product"):
        self.kiosk = kiosk_facade
        self.product_id = product_id
        self.qty = qty
        self.gateway = gateway
        self.item_type = item_type

    def execute(self):
        return self.kiosk._do_purchase(self.product_id, self.qty, self.gateway, self, item_type=self.item_type)


class RefundCommand(Command):
    name = "REFUND"

    def __init__(self, kiosk_facade, txn_id):
        self.kiosk = kiosk_facade
        self.txn_id = txn_id

    def execute(self):
        return self.kiosk._do_refund(self.txn_id, self)


class RestockCommand(Command):
    name = "RESTOCK"

    def __init__(self, kiosk_facade, product_id, qty):
        self.kiosk = kiosk_facade
        self.product_id = product_id
        self.qty = qty

    def execute(self):
        return self.kiosk._do_restock(self.product_id, self.qty, self)


class MacroCommand(Command):
    """DESIGN PATTERN EXTENSION: MacroCommand handles a sequence of commands."""
    name = "CHECKOUT_CART"

    def __init__(self, kiosk_facade, commands):
        self.kiosk = kiosk_facade
        self.commands = commands

    def execute(self):
        results = []
        for cmd in self.commands:
            results.append(cmd.execute())
        
        # Aggregate results for the UI
        successes = [r for r in results if r.get("ok")]
        if not successes:
            return {"ok": False, "message": "All items failed to dispense"}
        
        items_msg = ", ".join([r.get("data", {}).get("dispense", "Item") for r in successes])
        return {
            "ok": True, 
            "dispense": f"Cart Dispensed: {items_msg}",
            "count": len(successes),
            "total_items": len(results)
        }


def list_recent_transactions(limit=20):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id,ts,kiosk_type,command,payload,status,message "
            "FROM transactions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
