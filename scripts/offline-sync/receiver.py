#!/usr/bin/env python3
"""Local-only webhook receiver. Persist an allowlist of metadata, never payloads."""

import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import time


EVENTS = {"Connected", "Disconnected", "Message", "Receipt", "SendMessage", "PairSuccess"}
MARKER = re.compile(r"EVOSYNC-[a-f0-9]{8}-C[0-9]{2}-(before|during|after)")


class Receiver(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        if self.path != "/webhook":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4 * 1024 * 1024:
                self.send_error(413)
                return
            payload = json.loads(self.rfile.read(length))
            data = payload.get("data", {})
            info = data.get("Info", {}) if isinstance(data, dict) else {}
            message = data.get("Message", {}) if isinstance(data, dict) else {}
            event = payload.get("event")
            record = {"received_utc": time.time(), "event": event if event in EVENTS else "Other"}
            if event == "Message":
                identifier = str(info.get("ID", ""))
                record["message_id_sha256"] = hashlib.sha256(identifier.encode()).hexdigest() if identifier else None
                record["from_me"] = info.get("IsFromMe") is True
                record["kind"] = "other"
                for field, kind in (("audioMessage", "audio"), ("imageMessage", "image"),
                                    ("conversation", "text"), ("extendedTextMessage", "text")):
                    if field in message:
                        record["kind"] = kind
                        break
                extended = message.get("extendedTextMessage", {})
                text = message.get("conversation") or (extended.get("text") if isinstance(extended, dict) else "") or ""
                record["marker"] = text if isinstance(text, str) and MARKER.fullmatch(text) else None
            with Path("/events/events.jsonl").open("a") as handle:
                handle.write(json.dumps(record) + "\n")
        except (ValueError, AttributeError, TypeError):
            self.send_error(400)
            return
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    os.umask(0o077)
    server = HTTPServer(("0.0.0.0", 8081), Receiver)
    server.timeout = 10
    server.serve_forever()
