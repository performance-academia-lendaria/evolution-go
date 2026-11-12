#!/usr/bin/env python3
"""Run inside the proxy before configuring WhatsApp; all traffic is loopback."""

import base64
import json
import os
import socket
import threading
import time
import urllib.request


def control(path):
    request = urllib.request.Request("http://127.0.0.1:8083" + path,
                                     data=b"" if path != "/status" else None)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def connect():
    channel = socket.create_connection(("127.0.0.1", 8082), timeout=5)
    auth = base64.b64encode(("lab:" + os.environ["LAB_PROXY_PASSWORD"]).encode()).decode()
    channel.sendall(("CONNECT 127.0.0.1:443 HTTP/1.1\r\nHost: 127.0.0.1:443\r\n"
                     "Proxy-Authorization: Basic " + auth + "\r\n\r\n").encode())
    response = b""
    while not response.endswith(b"\r\n\r\n"):
        chunk = channel.recv(1)
        assert chunk
        response += chunk
    assert response.startswith(b"HTTP/1.1 200 ")
    return channel


def echo_connection(channel):
    try:
        while True:
            data = channel.recv(4096)
            if not data:
                return
            channel.sendall(data)
    finally:
        channel.close()


listener = socket.socket()
listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listener.bind(("127.0.0.1", 443))
listener.listen()


def echo_server():
    while True:
        try:
            channel, _ = listener.accept()
        except OSError:
            return
        threading.Thread(target=echo_connection, args=(channel,), daemon=True).start()


threading.Thread(target=echo_server, daemon=True).start()
first = None
second = []
connected = threading.Event()
try:
    assert control("/status")["active_tunnels"] == 0
    first = connect()
    first.sendall(b"synthetic-loopback-probe")
    assert first.recv(4096) == b"synthetic-loopback-probe"
    dropped = control("/drop")
    assert dropped["closed_tunnels"] == 1 and not dropped["gate_open"]
    assert first.recv(1) == b""

    def during_outage():
        second.append(connect())
        connected.set()

    worker = threading.Thread(target=during_outage, daemon=True)
    worker.start()
    time.sleep(0.2)
    assert not connected.is_set(), "CONNECT must remain blocked during the outage"
    control("/up")
    worker.join(timeout=5)
    assert connected.is_set()
    second[0].sendall(b"synthetic-restored-probe")
    assert second[0].recv(4096) == b"synthetic-restored-probe"
    print("PASS: TCP forwarding, real socket EOF, CONNECT held during outage, restore.")
    second[0].close()
    control("/drop")
    deadline = time.monotonic() + 23
    while time.monotonic() < deadline and not control("/status")["gate_open"]:
        time.sleep(0.5)
    assert control("/status")["gate_open"], "independent watchdog must restore within 20 seconds"
    print("PASS: independent watchdog restored the gate after 20 seconds.")
finally:
    control("/up")
    if first:
        first.close()
    for channel in second:
        channel.close()
    listener.close()
