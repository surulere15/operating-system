"""
Agent Lightning Dashboard Server
Serves the dashboard UI and connects to the LightningStore.

Usage:
    python3.11 dashboard_server.py --port 8080
"""

import argparse
import json
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

import agentlightning as agl


class DashboardHandler(SimpleHTTPRequestHandler):
    """Serve the dashboard static files and proxy store API."""
    
    def __init__(self, *args, store=None, **kwargs):
        self.store = store
        super().__init__(*args, directory=str(Path(__file__).parent / "build"), **kwargs)
    
    def do_GET(self):
        # API routes
        if self.path.startswith('/api/'):
            self._handle_api()
            return
        
        # Serve static files
        if self.path == '/':
            self.path = '/index.html'
        super().do_GET()
    
    def _handle_api(self):
        """Handle API requests by proxying to the store."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {"status": "ok", "store": "connected" if self.store else "disconnected"}
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass


def run_dashboard(port: int = 8080, store_address: str = "http://localhost:9999"):
    """Run the dashboard server."""
    
    # Create store connection
    store = agl.LightningStoreClient(store_address)
    
    # Create handler with store reference
    def handler(*args, **kwargs):
        DashboardHandler(*args, store=store, **kwargs)
    
    server = HTTPServer(('0.0.0.0', port), handler)
    
    print(f"⚡ Agent Lightning Dashboard")
    print(f"   URL: http://localhost:{port}")
    print(f"   Store: {store_address}")
    print(f"   Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent Lightning Dashboard Server")
    parser.add_argument("--port", type=int, default=8080, help="Dashboard port")
    parser.add_argument("--store", type=str, default="http://localhost:9999", help="Store address")
    args = parser.parse_args()
    
    run_dashboard(args.port, args.store)
