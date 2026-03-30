import json, ssl, urllib.request, urllib.parse, os, time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

IOL_BASE = "https://api.invertironline.com"

def get_token():
    user = os.environ.get("IOL_USER", "")
    pwd  = os.environ.get("IOL_PASS", "")
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
    return data["access_token"]

def get_hist_price(ticker, fecha_desde, token):
    hasta = datetime.now().strftime("%Y-%m-%d")
    path  = f"/api/v2/bCBA/Titulos/{ticker}/Cotizacion/seriehistorica/{fecha_desde}/{hasta}/sinAjustar"
    req   = urllib.request.Request(
        IOL_BASE + path,
        headers={"Authorization": "Bearer " + token}
    )
    try:
        with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
            data = json.loads(r.read().decode())
        if isinstance(data, list) and data:
            return data[0].get("precio") or data[0].get("precioAjustado")
    except Exception as e:
        print(f"Hist {ticker}: {e}")
    return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            tickers = [t.strip() for t in qs.get("tickers", [""])[0].split(",") if t.strip()]
            if not tickers: raise ValueError("No tickers")
            token = get_token()
            now   = datetime.now()
            inicio_mes  = now.replace(day=1).strftime("%Y-%m-%d")
            inicio_anio = now.replace(month=1, day=1).strftime("%Y-%m-%d")
            out = {}
            for t in tickers:
                out[t] = {
                    "baseMes":  get_hist_price(t, inicio_mes, token),
                    "baseAnio": get_hist_price(t, inicio_anio, token),
                }
                time.sleep(0.1)
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
