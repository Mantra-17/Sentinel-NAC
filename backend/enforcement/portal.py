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

PORTAL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NETWORK_ACCESS_DENIED // SENTINEL-NAC</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        
        body {
            margin: 0;
            padding: 0;
            background-color: #000;
            color: #fff;
            font-family: 'Inter', sans-serif;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            text-transform: uppercase;
        }

        .container {
            width: 100%;
            max-width: 600px;
            padding: 40px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(255, 255, 255, 0.02);
            position: relative;
        }

        .header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 40px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 20px;
        }

        .alert-icon {
            width: 50px;
            height: 50px;
            border: 1px solid #ef4444;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ef4444;
            font-size: 24px;
            font-weight: 900;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
            70% { box-shadow: 0 0 0 15px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }

        .status-badge {
            font-size: 10px;
            font-weight: 900;
            letter-spacing: 0.2em;
            color: #ef4444;
            background: rgba(239, 68, 68, 0.1);
            padding: 4px 12px;
            border: 1px solid rgba(239, 68, 68, 0.2);
            display: inline-block;
            margin-bottom: 10px;
        }

        h1 {
            font-size: 40px;
            font-weight: 900;
            margin: 0;
            letter-spacing: -0.05em;
            line-height: 0.9;
        }

        .content {
            margin-top: 30px;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.4);
            letter-spacing: 0.05em;
            line-height: 1.6;
        }

        .details {
            margin-top: 40px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.03);
            border-left: 2px solid #ef4444;
        }

        .details-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 10px;
            font-weight: 700;
        }

        .footer {
            margin-top: 40px;
            font-size: 9px;
            color: rgba(255, 255, 255, 0.2);
            text-align: center;
            letter-spacing: 0.3em;
        }

        .glitch-bar {
            position: absolute;
            top: 0;
            left: 0;
            height: 2px;
            width: 100%;
            background: #ef4444;
            opacity: 0.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="glitch-bar"></div>
        <div class="header">
            <div class="alert-icon">!</div>
            <div>
                <div class="status-badge">ROGUE_DEVICE_IDENTIFIED</div>
                <h1>ACCESS_DENIED</h1>
            </div>
        </div>
        <div class="content">
            Your device has been isolated from the network. This system is protected by <strong>SENTINEL-NAC Zero-Trust</strong> policies. Unauthorized connection attempts have been logged and reported to the system administrator.
        </div>
        <div class="details">
            <div class="details-row">
                <span>SYSTEM_NODE</span>
                <span>SGP_SECURE_LABS_01</span>
            </div>
            <div class="details-row">
                <span>ENFORCEMENT</span>
                <span>QUARANTINE_LEVEL_3</span>
            </div>
            <div class="details-row">
                <span>OPERATOR</span>
                <span>MANTRA_PATEL</span>
            </div>
        </div>
        <div class="footer">
            SENTINEL-NAC // SECURE_NETWORK_ENFORCEMENT // V1.0
        </div>
    </div>
</body>
</html>
"""

class PortalHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(PORTAL_HTML.encode("utf-8"))

    def log_message(self, format, *args):
        # Suppress standard logging to avoid cluttering terminal
        pass

class CaptivePortalServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
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
        except Exception as e:
            logger.error("Failed to start Captive Portal Server: %s", e)

    def stop(self):
        """Shutdown the server."""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            logger.info("Captive Portal Server stopped.")
