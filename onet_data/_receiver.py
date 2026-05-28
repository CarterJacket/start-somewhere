#!/usr/bin/env python3
"""Simple HTTP server to receive file data from the browser."""
import http.server
import json
import os
import sys

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

class FileReceiver(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = json.loads(body)
        
        filename = data.get('filename', '')
        content = data.get('content', '')
        
        if not filename or not content:
            self.send_response(400)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'Missing filename or content')
            return
        
        # Sanitize filename
        safe_name = os.path.basename(filename)
        output_path = os.path.join(OUTPUT_DIR, safe_name)
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        lines = content.count('\n')
        msg = f"Wrote {safe_name}: {len(content)} chars, {lines} lines"
        print(msg)
        
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(msg.encode())
    
    def log_message(self, format, *args):
        print(format % args, file=sys.stderr)

PORT = 18765
print(f"Starting file receiver on port {PORT}...")
server = http.server.HTTPServer(('0.0.0.0', PORT), FileReceiver)
server.serve_forever()
