"""
Sentinel-NAC: Captive Portal Server
File: backend/enforcement/portal.py
Purpose: Serve a "Rogue Device Notification" page to quarantined devices.
"""

import http.server
import socketserver
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)

PORTAL_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TERMINAL_LOCKDOWN // SENTINEL-NAC</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&display=swap');
        
        body {
            margin: 0;
            padding: 0;
            background-color: #050505;
            color: #fff;
            font-family: 'JetBrains Mono', monospace;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .glass-panel {
            width: 100%;
            max-width: 700px;
            padding: 60px;
            background: rgba(255, 255, 255, 0.01);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            position: relative;
            box-shadow: 0 40px 100px rgba(0,0,0,0.8);
        }

        .scanner-line {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, #ef4444, transparent);
            animation: scan 3s linear infinite;
        }

        @keyframes scan {
            0% { top: 0; opacity: 0; }
            50% { opacity: 1; }
            100% { top: 100%; opacity: 0; }
        }

        .lock-icon {
            font-size: 14px;
            font-weight: 800;
            color: #ef4444;
            letter-spacing: 0.5em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .lock-icon::before, .lock-icon::after {
            content: '';
            flex: 1;
            height: 1px;
            background: rgba(239, 68, 68, 0.2);
        }

        h1 {
            font-size: 52px;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.04em;
            line-height: 1;
            background: linear-gradient(180deg, #fff 0%, rgba(255,255,255,0.4) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .alert-sub {
            font-size: 10px;
            color: #ef4444;
            font-weight: 800;
            letter-spacing: 0.4em;
            margin-top: 5px;
            opacity: 0.8;
        }

        .message {
            margin-top: 40px;
            font-size: 13px;
            color: rgba(255, 255, 255, 0.5);
            line-height: 1.8;
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            padding-left: 25px;
        }

        .data-grid {
            margin-top: 50px;
            display: grid;
            grid-template-cols: 1fr 1fr;
            gap: 20px;
        }

        .data-item {
            padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.03);
            background: rgba(255, 255, 255, 0.01);
        }

        .label {
            font-size: 8px;
            color: rgba(255, 255, 255, 0.2);
            font-weight: 800;
            letter-spacing: 0.2em;
            margin-bottom: 5px;
        }

        .value {
            font-size: 11px;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 700;
        }

        .footer {
            margin-top: 60px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 8px;
            color: rgba(255, 255, 255, 0.1);
            letter-spacing: 0.2em;
        }

        .noise {
            position: absolute;
            inset: 0;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.6' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
            opacity: 0.03;
            pointer-events: none;
        }
    </style>
</head>
<body>
    <div class="noise"></div>
    <div class="glass-panel">
        <div class="scanner-line"></div>
        <div class="lock-icon">ESTABLISHING_QUARANTINE</div>
        <h1>ACCESS_DENIED</h1>
        <div class="alert-sub">ROGUE_NODE_DETECTED_0x442</div>
        
        <div class="message">
            This network is actively monitored by <strong>SENTINEL-NAC</strong>. Your device hardware signature does not match any authorized profiles in the root registry. Access to external gateways has been restricted.
        </div>

        <div class="data-grid">
            <div class="data-item">
                <div class="label">ENFORCEMENT_PROTOCOL</div>
                <div class="value">ARP_ISOLATION_v2.1</div>
            </div>
            <div class="data-item">
                <div class="label">THREAT_LEVEL</div>
                <div class="value" style="color: #ef4444;">CRITICAL</div>
            </div>
            <div class="data-item">
                <div class="label">GATEWAY_BLOCK</div>
                <div class="value">192.168.0.1 // ACTIVE</div>
            </div>
            <div class="data-item">
                <div class="label">SYSTEM_ADMIN</div>
                <div class="value">{admin_name}</div>
            </div>
        </div>

        <div class="footer">
            <span>SGP_SECURE_LABS // 2026</span>
            <span>POWERED_BY_SENTINEL_ENGINE</span>
        </div>
    </div>
</body>
</html>
"""

class PortalHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        from config.settings import SYSTEM_ADMIN_NAME
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = PORTAL_HTML_TEMPLATE.format(admin_name=SYSTEM_ADMIN_NAME)
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        # Suppress standard logging to avoid cluttering terminal
        pass

class CaptivePortalServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 80):
        self.host = host
        self.port = port
        self.httpd: Optional[socketserver.TCPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self):
        """Start the server in a background thread."""
        try:
            # Reusable address to avoid "Address already in use" errors on restart
            socketserver.TCPServer.allow_reuse_address = True
            self.httpd = socketserver.TCPServer((self.host, self.port), PortalHandler)
            
            self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.thread.start()
            logger.info("Captive Portal Server started on %s:%d", self.host, self.port)
        except PermissionError:
            logger.error("CRITICAL: Permission denied for Port %d. Did you run with 'sudo'?", self.port)
        except OSError as e:
            if e.errno == 48: # Address already in use
                logger.error("CRITICAL: Port %d is already occupied by another service (Apache/Nginx?).", self.port)
            else:
                logger.error("Failed to start Captive Portal Server: %s", e)
        except Exception as e:
            logger.error("Unexpected error starting Captive Portal: %s", e)

    def stop(self):
        """Shutdown the server."""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            logger.info("Captive Portal Server stopped.")
