import http.server
import socketserver
import json
import webbrowser
import os
from allthree.kiosk_logic import KioskFactory, AdminProxy

# Global System State
kiosk = None # Will be initialized via Factory on landing page
admin_proxy = AdminProxy()

class PatternHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        global kiosk
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        path = self.path
        response = {"status": "error"}

        # --- FACTORY PATTERN ---
        if path == "/init_kiosk":
            kiosk = KioskFactory.construct_kiosk(data['type'])
            response = {"status": "ok", "type": kiosk.k_type}

        # --- STRATEGY PATTERN ---
        elif path == "/set_payment":
            kiosk.set_payment_logic(data['method'])
            response = {"status": "ok", "msg": f"Strategy: Payment switched to {data['method'].upper()}"}

        elif path == "/buy":
            res = kiosk.process_purchase(data['id'], data['name'], data['price'])
            if res.get("success"):
                response = {"status": "ok", "logs": res}
            else:
                response = {"status": "error", "msg": res["msg"]}

        # --- PROXY PATTERN ---
        elif path == "/login":
            success = admin_proxy.login(data['password'])
            response = {"status": "ok" if success else "fail"}

        # --- CRUD ---
        elif path == "/add_item":
            msg = admin_proxy.add_item(kiosk, data['name'], float(data['price']), int(data['stock']))
            response = {"status": "ok", "msg": msg}

        elif path == "/delete_item":
            msg = admin_proxy.delete_item(kiosk, data['id'])
            response = {"status": "ok", "msg": msg}

        elif path == "/update_stock":
            msg = admin_proxy.update_stock(kiosk, data['id'], int(data['stock']))
            response = {"status": "ok", "msg": msg}

        elif path == "/update_hardware":
            msg = admin_proxy.update_hardware(kiosk, data['method'])
            response = {"status": "ok", "msg": msg}

        elif path == "/logout":
            admin_proxy.is_auth = False
            response = {"status": "ok"}

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        # Update path to look inside allthree/templates
        if self.path == "/":
            self.path = "/allthree/templates/index.html"
        elif self.path == "/get_items":
            if kiosk:
                import sqlite3
                with sqlite3.connect(kiosk.db_path) as conn:
                    items = conn.execute("SELECT id, name, price, stock FROM items WHERE kiosk_type=?", (kiosk.k_type,)).fetchall()
                    data = [{"id": i[0], "name": i[1], "price": i[2], "stock": i[3]} for i in items]
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(data).encode())
                    return
            else:
                self.send_response(400)
                self.end_headers()
                return
        
        # Adjust base directory for simple server
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

if __name__ == "__main__":
    PORT = 8000
    print(f"\n🚀 System Starting at http://localhost:{PORT}")
    webbrowser.open(f"http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), PatternHandler) as httpd:
        httpd.serve_forever()
