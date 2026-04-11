import http.server
import socketserver
import json
import os
from urllib.parse import urlparse
from kiosk_logic import StrategyKiosk, SpiralDispense, RoboticDispense, UPIPayment, CardPayment

class StrategyOSHandler(http.server.SimpleHTTPRequestHandler):
    kiosk = StrategyKiosk()

    def do_GET(self):
        # FORCE SERVE index.html with NO CACHE
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()
            with open("index.html", "rb") as f:
                self.wfile.write(f.read())
            return
            
        if self.path == "/inventory":
            items = self.kiosk.db.get_items()
            data = [{"name": r[0], "price": r[1], "stock": r[2], "id": r[3]} for r in items]
            self.send_json({"status": "ok", "data": data})
            return
        
        return super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(content_length).decode('utf-8')) if content_length else {}
        response = {"status": "ok"}
        
        if self.path == "/admin_auth":
            if data.get("password") == "admin": response["status"] = "ok"
            else: response["status"] = "error"

        elif self.path == "/set_strategy":
            stype = data.get("type")
            val = data.get("value")
            if stype == "dispense":
                self.kiosk.set_dispense_strategy(RoboticDispense() if val == "robotic" else SpiralDispense())
            elif stype == "payment":
                self.kiosk.set_payment_strategy(CardPayment() if val == "card" else UPIPayment())
            response["msg"] = f"Strategy Hotswapped: {val.upper()}"

        elif self.path == "/purchase":
            res = self.kiosk.execute_sale(data.get("id"), data.get("name"), data.get("price"))
            if res["success"]:
                response["details"] = res
                response["msg"] = f"Success"
            else:
                response["status"] = "error"
                response["msg"] = "FAIL: Out of Stock"

        elif self.path == "/admin_add":
            self.kiosk.db.add_item(data.get("n"), data.get("p"), data.get("s"))
            response["msg"] = f"Admin: Added {data.get('n')}"

        elif self.path == "/admin_update":
            self.kiosk.db.update_stock(data.get("id"), data.get("s"))
            response["msg"] = "Admin: Updated"

        elif self.path == "/admin_delete":
            self.kiosk.db.delete_item(data.get("id"))
            response["msg"] = "Admin: Deleted"

        self.send_json(response)

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

if __name__ == "__main__":
    # Ensure we are in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", 8080), StrategyOSHandler) as httpd:
        print("🎯 SECURE STRATEGY OS - CACHE DISABLED - http://localhost:8080")
        httpd.serve_forever()
