from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"ok": True, "msg": "pong"}).encode()
        self.send_response(200)
        self.send_header("content-type","application/json")
        self.end_headers()
        self.wfile.write(body)
