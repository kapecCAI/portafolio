import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request, ssl, time

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def fetch_yahoo(symbols):
    """Fetch usando cookies de Yahoo Finance para evitar 401"""
    # Primero obtenemos cookies/crumb
    try:
        cookie_url = "https://fc.yahoo.com"
        req = urllib.request.Request(cookie_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        })
        cookie_jar = {}
        try:
            with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as r:
                for h in r.headers.get_all('Set-Cookie') or []:
                    k,_,v = h.partition('=')
                    cookie_jar[k.strip()] = v.split(';')[0].strip()
        except: pass

        # Obtener crumb
        crumb = ""
        crumb_url = "https://query1.finance.yahoo.com/v1/test/getcrumb"
        cookie_str = "; ".join(f"{k}={v}" for k,v in cookie_jar.items())
        req2 = urllib.request.Request(crumb_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": cookie_str,
        })
        try:
            with urllib.request.urlopen(req2, timeout=5, context=SSL_CTX) as r:
                crumb = r.read().decode()
        except: pass

        # Fetch cotizaciones
        sym_str = ",".join(symbols)
        url = (f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={sym_str}"
               f"&fields=regularMarketPrice,regularMarketChangePercent,"
               f"regularMarketOpen,regularMarketDayHigh,regularMarketDayLow"
               + (f"&crumb={crumb}" if crumb else ""))
        req3 = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": cookie_str,
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req3, timeout=15, context=SSL_CTX) as r:
            data = json.loads(r.read().decode())
        return data.get("quoteResponse", {}).get("result", [])
    except Exception as e:
        raise Exception(f"Yahoo fetch error: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            tickers = [t.strip() for t in qs.get("tickers",[""])[0].split(",") if t.strip()]
            if not tickers:
                raise ValueError("No tickers")
            symbols = [t if t.endswith(".BA") else t+".BA" for t in tickers]
            result = fetch_yahoo(symbols)
            out = {}
            for q in result:
                raw = q.get("symbol","").replace(".BA","")
                out[raw] = {
                    "price":     q.get("regularMarketPrice"),
                    "changePct": q.get("regularMarketChangePercent"),
                    "apertura":  q.get("regularMarketOpen"),
                    "maximo":    q.get("regularMarketDayHigh"),
                    "minimo":    q.get("regularMarketDayLow"),
                }
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
