import http.server
import socketserver
import json
from urllib.parse import urlparse
from kiosk_logic import KioskProxy, KioskDatabase

class ProxyOSHandler(http.server.SimpleHTTPRequestHandler):
    proxy = None # KioskProxy
    db = KioskDatabase()

    def do_GET(self):
        if self.path == "/inventory":
            inv = []
            if self.proxy:
                items = self.proxy.get_inventory()
                for k, v in items.items():
                    inv.append({"key": k, "name": v.name, "price": v.price, "stock": v.stock, "id": v.db_id})
            self.send_json({"status": "ok", "data": inv})
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}

        if parsed.path == "/initialize":
            t = data.get("type", "pharmacy") + "_proxy"
            self.__class__.proxy = KioskProxy(t, self.db)
            self.send_json({"status": "ok", "msg": f"Proxy initialized for {t.upper()} node."})

        elif parsed.path == "/purchase":
            msg = self.proxy.process_purchase(data.get("key"))
            self.send_json({"status": "ok", "msg": msg})

        elif parsed.path == "/admin_auth":
            if self.proxy.authenticate(data.get("password")): 
                self.send_json({"status": "ok", "msg": "Proxy: Admin Access Granted"})
            else: 
                self.send_json({"status": "error", "msg": "Proxy: Access Denied"})

        elif parsed.path == "/add":
            n, p, s = data.get("n"), float(data.get("p")), int(data.get("s"))
            msg = self.proxy.admin_mod("add", {"n": n, "p": p, "s": s})
            self.send_json({"status": "ok", "msg": msg})

        elif parsed.path == "/update_stock":
            msg = self.proxy.admin_mod("update", {"id": data.get("id"), "s": data.get("s")})
            self.send_json({"status": "ok", "msg": msg})

        elif parsed.path == "/delete":
            msg = self.proxy.admin_mod("delete", {"id": data.get("id")})
            self.send_json({"status": "ok", "msg": msg})

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

if __name__ == "__main__":
    with socketserver.TCPServer(("", 8080), ProxyOSHandler) as httpd:
        print("🔥 PROXY DESIGN OS LIVE AT http://localhost:8080")
        httpd.serve_forever()
