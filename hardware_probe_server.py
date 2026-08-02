#!/usr/bin/env python3
"""Run one hardware probe, then serve its immutable result on port 8080."""

from __future__ import annotations

import importlib
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

probe = importlib.import_module(os.environ['REEFY_HARDWARE_PROBE'])
try:
    RESULT = {'ok': True, **probe.run()}
except Exception as error:
    RESULT = {
        'ok': False,
        'error_type': type(error).__name__,
        'error': str(error),
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(RESULT, sort_keys=True).encode()
        self.send_response(200 if RESULT['ok'] else 503)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


print(json.dumps(RESULT, sort_keys=True), flush=True)
HTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
