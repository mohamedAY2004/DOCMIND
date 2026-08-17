"""Development-only trusted portal server for the one-time-code SSO bridge.

The signing secret stays in this process. In production, the real campus
portal performs the same server-to-server ticket request after authenticating
its own user.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
API_URL = os.environ.get("DOCMIND_API_URL", "http://localhost:5000/api")
APP_URL = os.environ.get("DOCMIND_APP_URL", "http://localhost:5173")
USER_ID = os.environ.get("PORTAL_DEMO_USER_ID", "")
SECRET = os.environ.get("PORTAL_SSO_SECRET", "")


class PortalHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/sso":
            return super().do_GET()
        state = urllib.parse.parse_qs(parsed.query).get("state", [""])[0]
        if not state or not USER_ID or len(SECRET) < 32:
            self.send_error(500, "Set PORTAL_DEMO_USER_ID and a 32+ character PORTAL_SSO_SECRET.")
            return
        issued_at = int(time.time())
        message = f"{state}.{USER_ID}.{issued_at}".encode()
        signature = hmac.new(SECRET.encode(), message, hashlib.sha256).hexdigest()
        payload = json.dumps({
            "state": state,
            "userId": USER_ID,
            "issuedAt": issued_at,
            "signature": signature,
        }).encode()
        request = urllib.request.Request(
            f"{API_URL}/auth/sso/ticket",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                ticket = json.loads(response.read())
        except (urllib.error.URLError, ValueError) as exc:
            self.send_error(502, f"DocMind ticket exchange failed: {exc}")
            return
        query = urllib.parse.urlencode({"state": state, "code": ticket["code"]})
        self.send_response(302)
        self.send_header("Location", f"{APP_URL}/?{query}")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8080), PortalHandler).serve_forever()
