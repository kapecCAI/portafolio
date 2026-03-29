import json, ssl, urllib.request, time
from http.server import BaseHTTPRequestHandler
from datetime import datetime, timedelta

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

def get_historical_price(ticker, date_str):
    try:
        symbol = ticker if ticker.endswith(".BA") else ticker + ".BA"
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        p1 = int((dt - timedelta(days=5)).timestamp())
        p2 = int((dt + timedelta(days=2)).timestamp())
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
               f"?period1={p1}&period2={p2}&interval=1d")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as r:
            data = json.loads(r.read().decode())
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]
        return closes[0] if closes else None
    except:
        return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            tickers_raw = qs.get("tickers", [""])[0].split(",")
            tickers = [t.strip() for t in tickers_raw if t.strip()]
            if not tickers:
                raise ValueError("No tickers")

            now = datetime.now()
            inicio_mes  = now.replace(day=1).strftime("%Y-%m-%d")
            inicio_anio = now.replace(month=1, day=1).strftime("%Y-%m-%d")

            out = {}
            for ticker in tickers:
                base_mes  = get_historical_price(ticker, inicio_mes)
                base_anio = get_historical_price(ticker, inicio_anio)
                out[ticker] = {"baseMes": base_mes, "baseAnio": base_anio}
                time.sleep(0.05)

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
