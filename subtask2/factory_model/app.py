import http.server
import socketserver
import json
import logging
from urllib.parse import urlparse
from kiosk_logic import PharmacyFactory, FoodFactory, Kiosk, KioskDatabase

class FactoryOSHandler(http.server.SimpleHTTPRequestHandler):
    kiosk = None
    factory_map = {"pharmacy": PharmacyFactory, "food": FoodFactory}
    db = KioskDatabase()

    def do_GET(self):
        if self.path == "/inventory":
            inv = []
            if self.kiosk:
                # Always get fresh items from DB
                self.kiosk.inventory = self.db.get_items(self.kiosk.k_type)
                for k, v in self.kiosk.inventory.items():
                    inv.append({"key": k, "name": v.name, "price": v.price, "stock": v.stock, "id": v.db_id})
            self.send_json({"status": "ok", "data": inv})
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}

        if parsed.path == "/initialize":
            f_cls = self.factory_map.get(data.get("type"))
            if f_cls: 
                self.__class__.kiosk = Kiosk(f_cls(), self.db)
                self.send_json({"status": "ok", "msg": f"{data.get('type').title()} Started!"})

        elif parsed.path == "/purchase":
            msg = self.kiosk.process_purchase(data.get("key"))
            self.send_json({"status": "ok", "msg": msg})

        elif parsed.path == "/admin_auth":
            if data.get("password") == "admin": 
                self.send_json({"status": "ok"})
            else: 
                self.send_json({"status": "error"})

        elif parsed.path == "/add":
            n, p, s = data.get("n"), float(data.get("p")), int(data.get("s"))
            self.kiosk.add_item(n, p, s)
            self.send_json({"status": "ok", "msg": f"Admin: Added {n}"})

        elif parsed.path == "/update_stock":
            item_id, stock = data.get("id"), int(data.get("s"))
            self.kiosk.update_item_stock(item_id, stock)
            self.send_json({"status": "ok", "msg": "Admin: Stock Updated"})

        elif parsed.path == "/delete":
            item_id = data.get("id")
            self.kiosk.delete_item(item_id)
            self.send_json({"status": "ok", "msg": "Admin: Item Erased"})

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

if __name__ == "__main__":
    with socketserver.TCPServer(("", 8080), FactoryOSHandler) as httpd:
        print("🔥 PERSISTENT FACTORY OS LIVE AT http://localhost:8080")
        httpd.serve_forever()
