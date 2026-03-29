import json, ssl, urllib.request, csv, io
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def fetch_stooq(ticker):
    symbol = ticker.lower() + ".ba"
    url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
            text = r.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            try:
                close = float(row.get("Close") or 0)
                open_ = float(row.get("Open")  or 0)
                high  = float(row.get("High")  or 0)
                low   = float(row.get("Low")   or 0)
                chg   = round((close - open_) / open_ * 100, 2) if open_ else 0
                if close > 0:
                    return {"price": close, "changePct": chg, "apertura": open_, "maximo": high, "minimo": low}
            except: continue
    except Exception as e:
        print(f"Stooq {ticker}: {e}")
    return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            tickers = [t.strip() for t in qs.get("tickers",[""])[0].split(",") if t.strip()]
            if not tickers: raise ValueError("No tickers")
            out = {}
            for t in tickers:
                d = fetch_stooq(t)
                if d: out[t] = d
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
