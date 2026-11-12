#!/usr/bin/env python3
"""Disposable CONNECT tunnel for one test account; never inspect TLS payloads."""

import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import os
import select
import socket
import threading


GATE = threading.Event()
GATE.set()
LOCK = threading.Lock()
TUNNELS = set()
ACCEPTED = 0
REJECTED = 0
WATCHDOG = None
PASSWORD = os.environ["LAB_PROXY_PASSWORD"]
AUTH = "Basic " + base64.b64encode(("lab:" + PASSWORD).encode()).decode()


def close_socket(stream):
    try:
        stream.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    stream.close()


def snapshot():
    with LOCK:
        return {"gate_open": GATE.is_set(), "active_tunnels": len(TUNNELS),
                "accepted_tunnels": ACCEPTED, "rejected_auth": REJECTED}


def restore():
    global WATCHDOG
    with LOCK:
        if WATCHDOG:
            WATCHDOG.cancel()
            WATCHDOG = None
        GATE.set()


class QuietHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass


class TunnelHandler(QuietHandler):
    protocol_version = "HTTP/1.1"
    rbufsize = 0

    def do_CONNECT(self):
        global ACCEPTED, REJECTED
        self.close_connection = True
        if not hmac.compare_digest(self.headers.get("Proxy-Authorization", ""), AUTH):
            with LOCK:
                REJECTED += 1
            self.send_error(407)
            return
        host, separator, port = self.path.rpartition(":")
        if not separator or not host or port != "443":
            self.send_error(400)
            return
        pair = None
        upstream = None
        try:
            # Hold new CONNECTs during the outage instead of returning a failure
            # that the unchanged application would not retry. Independent restore
            # always opens the gate within 20 s, below this 25 s wait.
            while GATE.wait(25):
                upstream = socket.create_connection((host, 443), timeout=10)
                with LOCK:
                    if GATE.is_set():
                        pair = (self.connection, upstream)
                        TUNNELS.add(pair)
                        ACCEPTED += 1
                        break
                close_socket(upstream)
                upstream = None
            if pair is None:
                self.send_error(503)
                return
            self.send_response(200, "Connection Established")
            self.end_headers()
            self.wfile.flush()
            # Opaque bytes only. No host names, request headers or payload logging.
            while True:
                readable, _, _ = select.select(pair, [], [], 1)
                for stream in readable:
                    chunk = stream.recv(65536)
                    if not chunk:
                        return
                    (upstream if stream is self.connection else self.connection).sendall(chunk)
        except (OSError, ValueError):
            return
        finally:
            if pair:
                with LOCK:
                    TUNNELS.discard(pair)
            if upstream:
                close_socket(upstream)
            close_socket(self.connection)


class ControlHandler(QuietHandler):
    def do_GET(self):
        if self.path != "/status":
            self.send_error(404)
            return
        self.respond(snapshot())

    def do_POST(self):
        global WATCHDOG
        if self.path == "/up":
            restore()
            self.respond(snapshot())
        elif self.path == "/drop":
            with LOCK:
                if not GATE.is_set():
                    self.send_error(409)
                    return
                GATE.clear()
                active = list(TUNNELS)
                TUNNELS.clear()
                WATCHDOG = threading.Timer(20, restore)
                WATCHDOG.daemon = True
                WATCHDOG.start()
            for pair in active:
                for stream in pair:
                    close_socket(stream)
            result = snapshot()
            result.update({"closed_tunnels": len(active), "auto_restore_seconds": 20})
            self.respond(result)
        else:
            self.send_error(404)

    def respond(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    # Control can only be reached inside this container (docker exec), not by the
    # API, sender, host port or another container on either network.
    control = ThreadingHTTPServer(("127.0.0.1", 8083), ControlHandler)
    threading.Thread(target=control.serve_forever, daemon=True).start()
    proxy = ThreadingHTTPServer(("0.0.0.0", 8082), TunnelHandler)
    print("Local test tunnel ready; payload logging disabled.", flush=True)
    proxy.serve_forever()
