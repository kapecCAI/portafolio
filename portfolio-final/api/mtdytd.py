import json, ssl, urllib.request, csv, io, time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get_hist_price(ticker, date_str):
    """Precio de cierre en o después de date_str usando Stooq histórico."""
    try:
        symbol = ticker.lower() + ".ba"
        d1 = date_str.replace("-","")
        d2 = datetime.now().strftime("%Y%m%d")
        url = f"https://stooq.com/q/d/l/?s={symbol}&d1={d1}&d2={d2}&i=d"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
            text = r.read().decode("utf-8")
        reader = list(csv.DictReader(io.StringIO(text)))
        if reader:
            row = reader[0]  # más antiguo = más cercano a date_str
            close = float(row.get("Close") or 0)
            if close > 0: return close
    except Exception as e:
        print(f"Stooq hist {ticker}: {e}")
    return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            tickers = [t.strip() for t in qs.get("tickers",[""])[0].split(",") if t.strip()]
            if not tickers: raise ValueError("No tickers")
            now = datetime.now()
            inicio_mes  = now.replace(day=1).strftime("%Y-%m-%d")
            inicio_anio = now.replace(month=1,day=1).strftime("%Y-%m-%d")
            out = {}
            for t in tickers:
                out[t] = {
                    "baseMes":  get_hist_price(t, inicio_mes),
                    "baseAnio": get_hist_price(t, inicio_anio),
                }
                time.sleep(0.1)
            body = json.dumps(out).encode()
            self.send_response(200)
        except Exception as e:
            body = json.dumps({"error": str(e)}).encode()
            self.send_response(500)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
