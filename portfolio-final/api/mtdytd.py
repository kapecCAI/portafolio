import json, ssl, urllib.request, time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def get_cookie_crumb():
    cookie_jar = {}
    try:
        req = urllib.request.Request("https://fc.yahoo.com", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as r:
            for h in r.headers.get_all('Set-Cookie') or []:
                k,_,v = h.partition('=')
                cookie_jar[k.strip()] = v.split(';')[0].strip()
    except: pass
    crumb = ""
    try:
        cookie_str = "; ".join(f"{k}={v}" for k,v in cookie_jar.items())
        req2 = urllib.request.Request("https://query1.finance.yahoo.com/v1/test/getcrumb", headers={
            "User-Agent": "Mozilla/5.0",
            "Cookie": cookie_str,
        })
        with urllib.request.urlopen(req2, timeout=5, context=SSL_CTX) as r:
            crumb = r.read().decode()
    except: pass
    return cookie_jar, crumb

def get_hist_price(ticker, date_str, cookie_jar, crumb):
    try:
        symbol = ticker if ticker.endswith(".BA") else ticker+".BA"
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        p1 = int((dt - timedelta(days=5)).timestamp())
        p2 = int((dt + timedelta(days=2)).timestamp())
        cookie_str = "; ".join(f"{k}={v}" for k,v in cookie_jar.items())
        url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
               f"?period1={p1}&period2={p2}&interval=1d"
               + (f"&crumb={crumb}" if crumb else ""))
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": cookie_str,
        })
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
            qs = parse_qs(urlparse(self.path).query)
            tickers = [t.strip() for t in qs.get("tickers",[""])[0].split(",") if t.strip()]
            if not tickers: raise ValueError("No tickers")
            now = datetime.now()
            inicio_mes  = now.replace(day=1).strftime("%Y-%m-%d")
            inicio_anio = now.replace(month=1,day=1).strftime("%Y-%m-%d")
            cookie_jar, crumb = get_cookie_crumb()
            out = {}
            for ticker in tickers:
                out[ticker] = {
                    "baseMes":  get_hist_price(ticker, inicio_mes, cookie_jar, crumb),
                    "baseAnio": get_hist_price(ticker, inicio_anio, cookie_jar, crumb),
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
