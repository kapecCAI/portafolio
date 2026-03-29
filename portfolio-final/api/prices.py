import json, ssl, urllib.request
from http.server import BaseHTTPRequestHandler

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as r:
        return json.loads(r.read().decode())

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            tickers_raw = qs.get("tickers", [""])[0].split(",")
            tickers = [t.strip() for t in tickers_raw if t.strip()]
            if not tickers:
                raise ValueError("No tickers provided")

            symbols = [t if t.endswith(".BA") else t + ".BA" for t in tickers]
            url = ("https://query1.finance.yahoo.com/v7/finance/quote?symbols="
                   + ",".join(symbols)
                   + "&fields=regularMarketPrice,regularMarketChangePercent,"
                     "regularMarketOpen,regularMarketDayHigh,regularMarketDayLow,"
                     "regularMarketPreviousClose")
            data = fetch(url)
            result = data.get("quoteResponse", {}).get("result", [])
            out = {}
            for q in result:
                raw = q.get("symbol", "").replace(".BA", "")
                out[raw] = {
                    "price":     q.get("regularMarketPrice"),
                    "changePct": q.get("regularMarketChangePercent"),
                    "apertura":  q.get("regularMarketOpen"),
                    "maximo":    q.get("regularMarketDayHigh"),
                    "minimo":    q.get("regularMarketDayLow"),
                    "prevClose": q.get("regularMarketPreviousClose"),
                }
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
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()
