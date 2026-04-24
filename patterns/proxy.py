"""
=======================================
DESIGN PATTERN #6 — PROXY (Structural)
=======================================
Owner: Yash Gangwani
Purpose:
  All inventory mutations must pass through a security proxy that:
   - checks admin authentication (via CentralRegistry singleton)
   - logs every access to the audit_log table
Read-only operations are allowed to non-admin clients (so customers can browse).
"""
from db.database import get_conn
from inventory.inventory_system import InventorySystem
from patterns.singleton import CentralRegistry


class UnauthorizedAccess(Exception):
    pass


class InventorySecurityProxy:
    def __init__(self):
        self._real = InventorySystem()
        self._registry = CentralRegistry()

    # ---- audit helper ----
    def _audit(self, actor, action, detail=""):
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO audit_log (actor,action,detail) VALUES (?,?,?)",
                (actor, action, detail),
            )

    def _require_admin(self, action):
        if not self._registry.admin_authenticated:
            self._audit("anon", "DENIED:" + action, "Admin auth required")
            raise UnauthorizedAccess(f"Admin authentication required for {action}")

    # ---- read-through (allowed for everyone) ----
    def list_products(self, kiosk_type=None):
        self._audit("user", "READ:products", f"kiosk={kiosk_type}")
        return self._real.list_products(kiosk_type)

    def list_bundles(self, kiosk_type=None):
        self._audit("user", "READ:bundles", f"kiosk={kiosk_type}")
        return self._real.list_bundles(kiosk_type)

    def get_product(self, pid):
        return self._real.get_product(pid)

    def get_bundle(self, bid):
        return self._real.get_bundle(bid)

    # ---- write-through (admin only OR system on successful purchase) ----
    def update_stock(self, pid, delta, system=False):
        if not system:
            self._require_admin("update_stock")
        self._audit("admin" if not system else "system", "WRITE:stock",
                    f"pid={pid} delta={delta}")
        return self._real.update_stock(pid, delta)

    def add_product(self, kiosk_type, name, price, stock, requires_refrigeration=False, emergency_price=0.0):
        self._require_admin("add_product")
        self._audit("admin", "WRITE:add_product", f"{name} ({kiosk_type})")
        return self._real.add_product(kiosk_type, name, price, stock, requires_refrigeration, emergency_price)

    def delete_product(self, pid):
        self._require_admin("delete_product")
        self._audit("admin", "WRITE:delete_product", f"pid={pid}")
        return self._real.delete_product(pid)

    def add_bundle(self, kiosk_type, name, items, price=0.0, emergency_price=0.0):
        self._require_admin("add_bundle")
        self._audit("admin", "WRITE:add_bundle", f"{name} ({kiosk_type})")
        return self._real.add_bundle(kiosk_type, name, items, price, emergency_price)

    def delete_bundle(self, bid):
        self._require_admin("delete_bundle")
        self._audit("admin", "WRITE:delete_bundle", f"bid={bid}")
        return self._real.delete_bundle(bid)

    def update_item_name(self, item_id, new_name, item_type="product"):
        self._require_admin("update_item_name")
        self._audit("admin", "WRITE:update_name", f"{item_type} #{item_id} -> {new_name}")
        return self._real.update_item_name(item_id, new_name, item_type)

    def update_item_price(self, item_id, price, emergency_price, item_type="product"):
        self._require_admin("update_item_price")
        self._audit("admin", "WRITE:update_price", f"{item_type} #{item_id} -> {price}/{emergency_price}")
        return self._real.update_item_price(item_id, price, emergency_price, item_type)
