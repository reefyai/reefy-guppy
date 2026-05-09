#!/usr/bin/env python3
"""Guppy - tiny test app for reefy devices."""

import http.server
import os
import socket
import time

PORT = 8080


def get_uptime():
    try:
        with open('/proc/uptime') as f:
            secs = float(f.read().split()[0])
        h, r = divmod(int(secs), 3600)
        m, s = divmod(r, 60)
        return f"{h}h {m}m {s}s"
    except Exception:
        return "n/a"


def get_memory():
    try:
        info = {}
        with open('/proc/meminfo') as f:
            for line in f:
                parts = line.split()
                if parts[0] in ('MemTotal:', 'MemAvailable:'):
                    info[parts[0]] = int(parts[1])
        total = info.get('MemTotal:', 0) // 1024
        avail = info.get('MemAvailable:', 0) // 1024
        used = total - avail
        return f"{used}M / {total}M"
    except Exception:
        return "n/a"


def get_load():
    try:
        with open('/proc/loadavg') as f:
            return f.read().split()[:3]
    except Exception:
        return ["n/a"]


def get_disk():
    try:
        st = os.statvfs('/config')
        total = st.f_blocks * st.f_frsize // (1024 * 1024)
        free = st.f_bavail * st.f_frsize // (1024 * 1024)
        used = total - free
        return f"{used}M / {total}M"
    except Exception:
        return "n/a"


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        rows = [
            ("Hostname", socket.gethostname()),
            ("Status", '<span style="color:#34d399">Running</span>'),
            ("Uptime", get_uptime()),
            ("Memory", get_memory()),
            ("Load", " ".join(get_load())),
            ("Disk /config", get_disk()),
            ("Time", time.strftime("%Y-%m-%d %H:%M:%S %Z")),
            ("Kernel", os.uname().release),
            ("Python", os.sys.version.split()[0]),
        ]
        table = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows)
        html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width">
<title>Guppy</title>
<style>
body {{ background:#111; color:#e0e0e0; font-family:system-ui; max-width:480px; margin:40px auto; padding:0 20px }}
h1 {{ color:#34d399; font-size:1.4rem }}
table {{ width:100%; border-collapse:collapse; margin-top:1rem }}
td {{ padding:8px 0; border-bottom:1px solid #222; font-size:0.9rem }}
td:first-child {{ color:#888; width:40% }}
.footer {{ margin-top:2rem; color:#444; font-size:0.75rem; text-align:center }}
</style>
</head><body>
<h1>Guppy is alive!</h1>
<table>{table}</table>
<div class="footer">reefy.ai test app</div>
</body></html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, fmt, *args):
        pass  # silence request logs


if __name__ == "__main__":
    print(f"[guppy] Listening on port {PORT}")
    http.server.HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
