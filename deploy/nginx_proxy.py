#!/usr/bin/env python3
"""AI数字名片 统一入口代理 (:8200) — 纯stdlib"""
import os, sys, json, urllib.request, urllib.error, mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

BACKEND = "http://127.0.0.1:8203"
STATIC = os.path.abspath(r"D:\AI数智名片\frontend\nginx_html")
HOST, PORT = "0.0.0.0", 8200

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _p(self, m):
        url = BACKEND + self.path
        b = self.rfile.read(int(self.headers.get("Content-Length", 0))) if "Content-Length" in self.headers else None
        h = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "transfer-encoding", "connection")}
        try:
            r = urllib.request.Request(url, data=b, headers=h, method=m)
            r = urllib.request.urlopen(r, timeout=120)
            d = r.read()
            self.send_response(r.status)
            for k, v in r.headers.items():
                if k.lower() not in ("transfer-encoding", "content-encoding", "connection"):
                    self.send_header(k, v)
            self.send_header("Content-Length", str(len(d)))
            self.end_headers(); self.wfile.write(d)
        except urllib.error.HTTPError as e:
            d = e.read(); self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() not in ("transfer-encoding", "content-encoding", "connection"):
                    self.send_header(k, v)
            self.send_header("Content-Length", str(len(d)))
            self.end_headers(); self.wfile.write(d)
        except urllib.error.URLError as e:
            self._e(502, f"Backend: {e.reason}")
    def _e(self, c, m):
        b = json.dumps({"error": m}).encode()
        self.send_response(c); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def _s(self):
        p = self.path.split("?", 1)[0].split("#", 1)[0]; p = "/index.html" if p == "/" else p
        fp = os.path.realpath(os.path.join(STATIC, os.path.normpath(p.lstrip("/"))))
        if not fp.startswith(os.path.realpath(STATIC) + os.sep):
            return self._e(403, "Forbidden")
        if os.path.isfile(fp):
            ct = (mimetypes.guess_type(fp)[0] or "application/octet-stream")
            if "text" in ct or "javascript" in ct: ct += "; charset=utf-8"
            with open(fp, "rb") as f: d = f.read()
            self.send_response(200); self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(d))); self.send_header("Cache-Control", "no-cache")
            self.end_headers(); self.wfile.write(d)
        else:
            ip = os.path.join(STATIC, "index.html")
            if os.path.isfile(ip):
                with open(ip, "rb") as f: d = f.read()
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(d))); self.end_headers(); self.wfile.write(d)
            else: self._e(404, "Not Found")
    def _is_api(self): return self.path in ("/health", "/docs", "/openapi.json") or self.path.startswith("/api/")
    def do_GET(self): self._p("GET") if self._is_api() else self._s()
    def do_HEAD(self): self._p("HEAD") if self._is_api() else self._s()
    def do_POST(self): self._p("POST") if self._is_api() else self._e(405, "Not Allowed")
    def do_PUT(self): self.do_POST()
    def do_DELETE(self): self.do_POST()
    def do_PATCH(self): self.do_POST()
    def do_OPTIONS(self):
        if self._is_api():
            self._p("OPTIONS")
        else:
            self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Access-Control-Max-Age", "86400"); self.send_header("Content-Length", "0")
            self.end_headers()

class T(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True; daemon_threads = True

def main():
    if not os.path.isdir(STATIC):
        print(f"Error: {STATIC} not found", file=sys.stderr); sys.exit(1)
    s = T((HOST, PORT), H)
    print(f"[proxy] 统一入口 http://{HOST}:{PORT}")
    print(f"[proxy] 静态: {STATIC}  后端: {BACKEND}")
    try: s.serve_forever()
    except KeyboardInterrupt: print("\n[proxy] 停止"); s.server_close()

if __name__ == "__main__": main()
