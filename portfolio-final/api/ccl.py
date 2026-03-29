import json, ssl, urllib.request
from http.server import BaseHTTPRequestHandler

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def get_dolar(tipo):
    url = f"https://dolarapi.com/v1/dolares/{tipo}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
        return json.loads(r.read().decode())

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            ccl_data = get_dolar("contadoconliqui")
            mep_data = get_dolar("bolsa")
            body = json.dumps({
                "ccl": ccl_data.get("venta"),
                "mep": mep_data.get("venta"),
            }).encode()
            self.send_response(200)
        except Exception as e:
            body = json.dumps({"error": str(e)}).encode()
            self.send_response(500)

        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
