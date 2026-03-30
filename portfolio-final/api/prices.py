import json, ssl, urllib.request, urllib.parse, os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

IOL_BASE = "https://api.invertironline.com"

def get_token():
    user = os.environ.get("IOL_USER", "")
    pwd  = os.environ.get("IOL_PASS", "")
    if not user or not pwd:
        raise Exception("IOL_USER / IOL_PASS no configuradas")
    body = urllib.parse.urlencode({
        "username": user, "password": pwd, "grant_type": "password"
    }).encode()
    req = urllib.request.Request(
        IOL_BASE + "/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
        data = json.loads(r.read().decode())
    token = data.get("access_token")
    if not token:
        raise Exception("IOL login fallido")
    return token

def iol_get(path, token):
    req = urllib.request.Request(
        IOL_BASE + path,
        headers={"Authorization": "Bearer " + token}
    )
    with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
        return json.loads(r.read().decode())

def fetch_cotizacion(ticker, token):
    data = iol_get(f"/api/v2/bCBA/Titulos/{ticker}/Cotizacion", token)
    price = data.get("ultimoPrecio")
    if not price:
        return None
    return {
        "price":     price,
        "changePct": data.get("variacion"),
        "apertura":  data.get("apertura"),
        "maximo":    data.get("maximo"),
        "minimo":    data.get("minimo"),
        "volumen":   data.get("volumen"),
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            tickers = [t.strip() for t in qs.get("tickers", [""])[0].split(",") if t.strip()]
            if not tickers:
                raise ValueError("No tickers")
            token = get_token()
            out = {}
            for t in tickers:
                try:
                    d = fetch_cotizacion(t, token)
                    if d: out[t] = d
                except Exception as e:
                    print(f"Error {t}: {e}")
            body = json.dumps(out).encode()
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
