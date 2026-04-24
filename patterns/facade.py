"""
=========================================
DESIGN PATTERN #9 — FACADE (Structural)
=========================================
Owner: Megha Lalwani
Purpose:
  KioskInterface is the single, simplified entry point external systems use:
    purchase_item(), refund_transaction(), run_diagnostics(), restock_inventory()
  It hides Inventory, Payment, Hardware, Strategy, Decorator, Command subsystems.
"""
import json
from db.database import get_conn
from patterns.singleton import CentralRegistry
from patterns.factory import get_factory
from patterns.proxy import InventorySecurityProxy, UnauthorizedAccess
from patterns.strategy import select_pricing
from patterns.decorator import build_kiosk_unit
from patterns.command import PurchaseCommand, RefundCommand, RestockCommand, MacroCommand
from hardware.dispensers import get_dispenser
from payments.gateways import get_gateway


class KioskInterface:
    """Facade — orchestrates every subsystem behind one clean API."""

    def __init__(self, kiosk_type, modules=None):
        self.registry = CentralRegistry()
        self.registry.active_kiosk_type = kiosk_type
        self.factory = get_factory(kiosk_type)
        self.kiosk_type = kiosk_type
        self.inventory = InventorySecurityProxy()      # Proxy
        self.unit = build_kiosk_unit(kiosk_type, modules or [])  # Decorator chain
        self.dispenser = self.factory.create_dispenser()         # Strategy via Factory
        self.registry.log_event("SYSTEM", f"Kiosk initialized as {kiosk_type}")

    # ------------------------------------------------------------------
    # PUBLIC FACADE API
    # ------------------------------------------------------------------
    def purchase_item(self, product_id, qty, payment_method, item_type="product"):
        gw = get_gateway(payment_method)
        cmd = PurchaseCommand(self, product_id, qty, gw, item_type=item_type)
        return cmd.execute()

    def process_cart(self, items, payment_method):
        """Processes a list of items using the MacroCommand pattern."""
        gw = get_gateway(payment_method)
        commands = []
        for it in items:
            cmd = PurchaseCommand(self, it["product_id"], it["qty"], gw, item_type=it.get("item_type", "product"))
            commands.append(cmd)
        
        macro = MacroCommand(self, commands)
        return macro.execute()

    def refund_transaction(self, txn_id):
        return RefundCommand(self, txn_id).execute()

    def restock_inventory(self, product_id, qty):
        return RestockCommand(self, product_id, qty).execute()

    def run_diagnostics(self):
        return {
            "kiosk_type": self.kiosk_type,
            "dispenser": self.dispenser.name,
            "modules": self.unit.status(),
            "capabilities": self.unit.capabilities(),
            "policy": self.factory.inventory_policy(),
            "emergency_mode": self.registry.get_config("emergency_mode") == "1",
        }

    def set_dispenser(self, name):
        """Strategy switch at runtime."""
        self.dispenser = get_dispenser(name)
        self.registry.set_config("dispenser", name)
        self.registry.log_event("HARDWARE", f"Dispenser switched to {self.dispenser.name}")

    def attach_modules(self, modules):
        self.unit = build_kiosk_unit(self.kiosk_type, modules)
        self.registry.log_event("HARDWARE", f"Modules now: {modules or 'none'}")

    # ------------------------------------------------------------------
    # INTERNAL — invoked by Command objects
    # ------------------------------------------------------------------
    def _do_purchase(self, product_id, qty, gateway, cmd, item_type="product"):
        if item_type == "bundle":
            product = self.inventory.get_bundle(product_id)
        else:
            product = self.inventory.get_product(product_id)
        if not product:
            cmd._record(self.kiosk_type, {"product_id": product_id}, "FAIL", "Product not found")
            return {"ok": False, "message": "Product not found"}

        # Composite-friendly availability check
        if not product.is_available(qty):
            cmd._record(self.kiosk_type, product.describe(), "FAIL", "Out of stock")
            return {"ok": False, "message": "Out of stock"}

        # Hardware-dependency constraint (refrigeration)
        caps = self.unit.capabilities()
        if product.requires_refrigeration and "refrigeration" not in caps:
            cmd._record(self.kiosk_type, product.describe(), "FAIL",
                        "Refrigeration module required")
            return {"ok": False, "message": "Refrigeration module required for this product"}

        # Strategy: dynamic pricing
        emergency = self.registry.get_config("emergency_mode") == "1"
        pricing = select_pricing(emergency=emergency)
        unit_price = pricing.compute(product)
        total = round(unit_price * qty, 2)

        # Snapshot (for atomic rollback)
        snapshot = product.stock

        # Adapter: payment
        receipt = gateway.pay(total)
        if not receipt["ok"]:
            cmd._record(self.kiosk_type, {"product": product.describe(), "receipt": receipt},
                        "FAIL", "Payment declined")
            return {"ok": False, "message": "Payment declined"}

        try:
            # System write through proxy (system=True bypasses admin gate)
            logs = []
            if item_type == "bundle":
                for child, q in product.children:
                    self.inventory.update_stock(child.id, -(q * qty), system=True)
                    for _ in range(q * qty):
                        logs.append(self.dispenser.dispense(child.name))
            else:
                self.inventory.update_stock(product_id, -qty, system=True)
                for _ in range(qty):
                    logs.append(self.dispenser.dispense(product.name))

            dispense_log = " | ".join(logs)
        except Exception as e:
            # Rollback (simplified: restore items if hardware fails)
            if item_type == "bundle":
                for child, q in product.children:
                    self.inventory.update_stock(child.id, (q * qty), system=True)
            else:
                self.inventory.update_stock(product_id, qty, system=True)

            cmd._record(self.kiosk_type, {"error": str(e)}, "FAIL", "Hardware fault — rolled back")
            return {"ok": False, "message": f"Hardware fault: {str(e)} — transaction rolled back"}

        payload = {
            "product": product.describe(),
            "qty": qty,
            "unit_price": unit_price,
            "total": total,
            "pricing_strategy": pricing.name,
            "receipt": receipt,
            "dispense": dispense_log,
        }
        txn_id = cmd._record(self.kiosk_type, payload, "OK",
                             f"Sold {qty} x {product.name} via {receipt['provider']}")
        self.registry.log_event(
            "PURCHASE",
            f"{qty} x {product.name} for ₹{total} ({pricing.name} pricing, {receipt['provider']})"
        )
        payload["txn_id"] = txn_id
        return {"ok": True, "message": "Purchase complete", "data": payload}

    def _do_refund(self, txn_id, cmd):
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM transactions WHERE id=? AND status='OK'",
                               (txn_id,)).fetchone()
            if not row or row["command"] != "PURCHASE":
                cmd._record(self.kiosk_type, {"txn_id": txn_id}, "FAIL", "Txn not refundable")
                return {"ok": False, "message": "Transaction not found or not refundable"}
            data = json.loads(row["payload"])
        # restore stock
        if data["product"].get("type") == "bundle":
            for child in data["product"].get("children", []):
                # child["qty"] is quantity per bundle, data["qty"] is number of bundles
                self.inventory.update_stock(child["id"], child["qty"] * data["qty"], system=True)
        else:
            self.inventory.update_stock(data["product"]["id"], data["qty"], system=True)

        cmd._record(self.kiosk_type, {"refunded_txn": txn_id, "amount": data["total"]},
                    "OK", f"Refunded ₹{data['total']}")
        self.registry.log_event("REFUND", f"Txn #{txn_id} refunded (₹{data['total']})")
        return {"ok": True, "message": "Refund processed", "amount": data["total"]}

    def _do_restock(self, product_id, qty, cmd):
        try:
            self.inventory.update_stock(product_id, qty)  # admin-gated by proxy
        except UnauthorizedAccess as e:
            cmd._record(self.kiosk_type, {"product_id": product_id, "qty": qty},
                        "FAIL", str(e))
            return {"ok": False, "message": str(e)}
        cmd._record(self.kiosk_type, {"product_id": product_id, "qty": qty},
                    "OK", f"Restocked +{qty}")
        self.registry.log_event("RESTOCK", f"Product #{product_id} +{qty} units")
        return {"ok": True, "message": "Restocked"}
