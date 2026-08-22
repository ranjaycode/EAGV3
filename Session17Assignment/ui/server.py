"""Development Web Server for Arcturus Studio.

Hosts frontend UI assets on http://localhost:8115 and proxies API endpoints to S17Code engine (port 8113).
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import sys
import os

PORT = 8115
S17_BACKEND = "http://localhost:8113"

UI_DIR = os.path.dirname(os.path.abspath(__file__))


class ArcturusServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=UI_DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith("/v1/") or self.path.startswith("/s/"):
            self.proxy_to_s17()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/v1/"):
            self.proxy_to_s17()
        else:
            self.send_error(405, "Method Not Allowed")

    def proxy_to_s17(self):
        url = f"{S17_BACKEND}{self.path}"
        try:
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len) if content_len > 0 else None
            req = urllib.request.Request(url, data=body, headers={k: v for k, v in self.headers.items() if k.lower() != 'host'}, method=self.command)
            with urllib.request.urlopen(req) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(f'{{"error": "S17 backend unavailable: {e}"}}'.encode("utf-8"))


def main():
    with socketserver.TCPServer(("", PORT), ArcturusServerHandler) as httpd:
        print(f"[ARCTURUS] Arcturus Studio running on http://localhost:{PORT}")
        print(f"[ARCTURUS] Proxying API endpoints (/v1/*) to S17Code engine at {S17_BACKEND}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down Arcturus Studio server.")


if __name__ == "__main__":
    main()
