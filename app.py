"""
Aura Retail OS — Flask entry point.
Wires HTTP routes to the Facade. No business logic lives here.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify, session

from db.database import init_db
from patterns.singleton import CentralRegistry
from patterns.facade import KioskInterface
from patterns.command import list_recent_transactions
from patterns.proxy import UnauthorizedAccess

app = Flask(__name__)
app.secret_key = "aura-retail-os-demo-secret"

init_db()
registry = CentralRegistry()

# In-memory map of active facades per kiosk type
_facades = {}

def get_facade(kiosk_type, modules=None):
    if kiosk_type not in _facades:
        # default modules per kiosk type
        defaults = {
            "PHARMACY": ["network"],
            "FOOD": ["refrigeration", "network"],
            "EMERGENCY": ["solar", "network"],
        }
        _facades[kiosk_type] = KioskInterface(kiosk_type, modules or defaults.get(kiosk_type, []))
    elif modules is not None:
        _facades[kiosk_type].attach_modules(modules)
    return _facades[kiosk_type]


# ----------------------------- HTML PAGES -----------------------------
@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/kiosk/<kiosk_type>")
def kiosk(kiosk_type):
    kiosk_type = kiosk_type.upper()
    if kiosk_type not in ("PHARMACY", "FOOD", "EMERGENCY"):
        return "Unknown kiosk", 404
    get_facade(kiosk_type)
    return render_template("kiosk.html", kiosk_type=kiosk_type)


# ----------------------------- JSON API -----------------------------
@app.route("/api/state/<kiosk_type>")
def api_state(kiosk_type):
    kt = kiosk_type.upper()
    fac = get_facade(kt)
    products = [p.describe() for p in fac.inventory.list_products(kt)]
    bundles = [b.describe() for b in fac.inventory.list_bundles(kt)]
    return jsonify({
        "kiosk_type": kt,
        "diagnostics": fac.run_diagnostics(),
        "products": products,
        "bundles": bundles,
        "transactions": list_recent_transactions(15),
        "events": registry.event_log[-30:],
        "admin": registry.admin_authenticated,
        "emergency": registry.get_config("emergency_mode") == "1",
        "dispenser": registry.get_config("dispenser"),
    })


@app.route("/api/purchase", methods=["POST"])
def api_purchase():
    d = request.get_json(force=True)
    fac = get_facade(d["kiosk_type"].upper())
    
    if "items" in d:
        # Multi-item cart (MacroCommand)
        res = fac.process_cart(d["items"], d.get("payment", "card"))
    else:
        # Single item legacy support
        res = fac.purchase_item(
            int(d["product_id"]), int(d.get("qty", 1)), d.get("payment", "card"),
            item_type=d.get("item_type", "product")
        )
    return jsonify(res)


@app.route("/api/refund", methods=["POST"])
def api_refund():
    d = request.get_json(force=True)
    fac = get_facade(d["kiosk_type"].upper())
    res = fac.refund_transaction(int(d["txn_id"]))
    return jsonify(res)


@app.route("/api/restock", methods=["POST"])
def api_restock():
    d = request.get_json(force=True)
    fac = get_facade(d["kiosk_type"].upper())
    try:
        res = fac.restock_inventory(int(d["product_id"]), int(d["qty"]))
    except UnauthorizedAccess as e:
        return jsonify({"ok": False, "message": str(e)}), 403
    return jsonify(res)


@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    d = request.get_json(force=True)
    if d.get("pin") == registry.get_config("admin_pin"):
        registry.admin_authenticated = True
        registry.log_event("AUTH", "Admin authenticated via Proxy")
        return jsonify({"ok": True})
    registry.log_event("AUTH", "Admin authentication FAILED")
    return jsonify({"ok": False, "message": "Invalid PIN"}), 401


@app.route("/api/admin/logout", methods=["POST"])
def api_admin_logout():
    registry.admin_authenticated = False
    registry.log_event("AUTH", "Admin logged out")
    return jsonify({"ok": True})


@app.route("/api/admin/product", methods=["POST"])
def api_admin_add_product():
    d = request.get_json(force=True)
    fac = get_facade(d["kiosk_type"].upper())
    try:
        pid = fac.inventory.add_product(
            d["kiosk_type"].upper(), d["name"], float(d["price"]),
            int(d["stock"]), bool(d.get("requires_refrigeration", False)),
            emergency_price=float(d.get("emergency_price", 0.0))
        )
        registry.log_event("INVENTORY", f"Added product #{pid} {d['name']}")
        return jsonify({"ok": True, "id": pid})
    except UnauthorizedAccess as e:
        return jsonify({"ok": False, "message": str(e)}), 403


@app.route("/api/admin/price", methods=["POST"])
def api_admin_update_price():
    d = request.get_json(force=True)
    fac = get_facade(d["kiosk_type"].upper())
    try:
        fac.inventory.update_item_price(
            int(d["id"]), float(d["price"]), float(d["emergency_price"]),
            d.get("item_type", "product")
        )
        registry.log_event("INVENTORY", f"Updated {d.get('item_type')} #{d['id']} price to Standard:₹{d['price']} / Emergency:₹{d['emergency_price']}")
        return jsonify({"ok": True})
    except UnauthorizedAccess as e:
        return jsonify({"ok": False, "message": str(e)}), 403


@app.route("/api/admin/product/<int:pid>", methods=["DELETE"])
def api_admin_delete_product(pid):
    kt = request.args.get("kiosk_type", "PHARMACY").upper()
    fac = get_facade(kt)
    try:
        fac.inventory.delete_product(pid)
        registry.log_event("INVENTORY", f"Deleted product #{pid}")
        return jsonify({"ok": True})
    except UnauthorizedAccess as e:
        return jsonify({"ok": False, "message": str(e)}), 403
@app.route("/api/admin/bundle", methods=["POST"])
def api_admin_add_bundle():
    d = request.get_json(force=True)
    fac = get_facade(d["kiosk_type"].upper())
    try:
        fac.inventory.add_bundle(
            d["kiosk_type"].upper(), d["name"], d["items"],
            price=float(d.get("price", 0.0)),
            emergency_price=float(d.get("emergency_price", 0.0))
        )
        registry.log_event("INVENTORY", f"Created bundle: {d['name']}")
        return jsonify({"ok": True})
    except UnauthorizedAccess as e:
        return jsonify({"ok": False, "message": str(e)}), 403


@app.route("/api/admin/bundle/<int:bid>", methods=["DELETE"])
def api_admin_delete_bundle(bid):
    kt = request.args.get("kiosk_type", "PHARMACY").upper()
    fac = get_facade(kt)
    try:
        fac.inventory.delete_bundle(bid)
        registry.log_event("INVENTORY", f"Deleted bundle #{bid}")
        return jsonify({"ok": True})
    except UnauthorizedAccess as e:
        return jsonify({"ok": False, "message": str(e)}), 403


@app.route("/api/admin/rename", methods=["POST"])
def api_admin_rename():
    d = request.get_json(force=True)
    fac = get_facade(d["kiosk_type"].upper())
    try:
        fac.inventory.update_item_name(int(d["id"]), d["name"], d.get("item_type", "product"))
        registry.log_event("INVENTORY", f"Renamed {d.get('item_type')} #{d['id']} to {d['name']}")
        return jsonify({"ok": True})
    except UnauthorizedAccess as e:
        return jsonify({"ok": False, "message": str(e)}), 403


@app.route("/api/admin/dispenser", methods=["POST"])
def api_admin_dispenser():
    d = request.get_json(force=True)
    fac = get_facade(d["kiosk_type"].upper())
    if not registry.admin_authenticated:
        return jsonify({"ok": False, "message": "Admin only"}), 403
    fac.set_dispenser(d["name"])
    return jsonify({"ok": True, "dispenser": fac.dispenser.name})


@app.route("/api/admin/modules", methods=["POST"])
def api_admin_modules():
    d = request.get_json(force=True)
    if not registry.admin_authenticated:
        return jsonify({"ok": False, "message": "Admin only"}), 403
    fac = get_facade(d["kiosk_type"].upper(), modules=d.get("modules", []))
    return jsonify({"ok": True, "modules": fac.unit.status(), "capabilities": fac.unit.capabilities()})


@app.route("/api/admin/emergency", methods=["POST"])
def api_admin_emergency():
    if not registry.admin_authenticated:
        return jsonify({"ok": False, "message": "Admin only"}), 403
    d = request.get_json(force=True)
    on = "1" if d.get("on") else "0"
    registry.set_config("emergency_mode", on)
    registry.log_event("MODE", f"Emergency mode {'ACTIVATED' if on=='1' else 'cleared'}")
    return jsonify({"ok": True, "emergency": on == "1"})


if __name__ == "__main__":
    # Use the PORT environment variable if available (Render/Heroku), otherwise default to 8000
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
