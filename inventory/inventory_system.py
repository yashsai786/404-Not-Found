"""
Real Inventory Subject (used by the Proxy).
Talks to SQLite directly. NEVER call this directly from controllers — go
through InventorySecurityProxy.
"""
from db.database import get_conn
from patterns.composite import Product, Bundle


class InventorySystem:
    def list_products(self, kiosk_type=None):
        with get_conn() as conn:
            if kiosk_type:
                rows = conn.execute(
                    "SELECT * FROM products WHERE kiosk_type=? ORDER BY name", (kiosk_type,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM products ORDER BY kiosk_type,name").fetchall()
            return [Product(r["id"], r["name"], r["price"], r["stock"], r["requires_refrigeration"], r["emergency_price"]) for r in rows]

    def list_bundles(self, kiosk_type=None):
        with get_conn() as conn:
            if kiosk_type:
                bs = conn.execute("SELECT * FROM bundles WHERE kiosk_type=?", (kiosk_type,)).fetchall()
            else:
                bs = conn.execute("SELECT * FROM bundles").fetchall()
            bundles = []
            for b in bs:
                bundle = Bundle(b["id"], b["name"], b["price"], b["emergency_price"])
                items = conn.execute(
                    "SELECT * FROM bundle_items WHERE bundle_id=?", (b["id"],)
                ).fetchall()
                for it in items:
                    if it["child_product_id"]:
                        p = conn.execute(
                            "SELECT * FROM products WHERE id=?", (it["child_product_id"],)
                        ).fetchone()
                        if p:
                            bundle.add(Product(p["id"], p["name"], p["price"], p["stock"], p["requires_refrigeration"], p["emergency_price"]),
                                       it["quantity"])
                bundles.append(bundle)
            return bundles

    def get_product(self, pid):
        with get_conn() as conn:
            r = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
            return Product(r["id"], r["name"], r["price"], r["stock"], r["requires_refrigeration"], r["emergency_price"]) if r else None

    def get_bundle(self, bid):
        with get_conn() as conn:
            b = conn.execute("SELECT * FROM bundles WHERE id=?", (bid,)).fetchone()
            if not b: return None
            bundle = Bundle(b["id"], b["name"], b["price"], b["emergency_price"])
            items = conn.execute(
                "SELECT * FROM bundle_items WHERE bundle_id=?", (b["id"],)
            ).fetchall()
            for it in items:
                if it["child_product_id"]:
                    p = conn.execute(
                        "SELECT * FROM products WHERE id=?", (it["child_product_id"],)
                    ).fetchone()
                    if p:
                        bundle.add(Product(p["id"], p["name"], p["price"], p["stock"], p["requires_refrigeration"], p["emergency_price"]),
                                   it["quantity"])
            return bundle

    def update_stock(self, pid, delta):
        with get_conn() as conn:
            conn.execute("UPDATE products SET stock = stock + ? WHERE id=?", (delta, pid))

    def add_product(self, kiosk_type, name, price, stock, requires_refrigeration=False, emergency_price=0.0):
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO products (kiosk_type,name,price,emergency_price,stock,requires_refrigeration) VALUES (?,?,?,?,?,?)",
                (kiosk_type, name, price, emergency_price, stock, int(requires_refrigeration)),
            )
            return cur.lastrowid

    def add_bundle(self, kiosk_type, name, items, price=0.0, emergency_price=0.0):
        """
        items: list of {'product_id': int, 'qty': int}
        """
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO bundles (kiosk_type, name, price, emergency_price) VALUES (?,?,?,?)",
                (kiosk_type, name, price, emergency_price)
            )
            bid = cur.lastrowid
            for it in items:
                conn.execute(
                    "INSERT INTO bundle_items (bundle_id, child_product_id, quantity) VALUES (?,?,?)",
                    (bid, it["product_id"], it["qty"])
                )
            return bid

    def delete_product(self, pid):
        with get_conn() as conn:
            conn.execute("DELETE FROM products WHERE id=?", (pid,))

    def delete_bundle(self, bid):
        with get_conn() as conn:
            conn.execute("DELETE FROM bundles WHERE id=?", (bid,))
            conn.execute("DELETE FROM bundle_items WHERE bundle_id=?", (bid,))

    def update_item_name(self, item_id, new_name, item_type="product"):
        with get_conn() as conn:
            table = "products" if item_type == "product" else "bundles"
            conn.execute(f"UPDATE {table} SET name=? WHERE id=?", (new_name, item_id))

    def update_item_price(self, item_id, price, emergency_price, item_type="product"):
        with get_conn() as conn:
            table = "products" if item_type == "product" else "bundles"
            conn.execute(f"UPDATE {table} SET price=?, emergency_price=? WHERE id=?", (price, emergency_price, item_id))
