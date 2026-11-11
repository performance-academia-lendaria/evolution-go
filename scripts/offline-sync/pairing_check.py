#!/usr/bin/env python3
"""Prepare one separate local companion to validate fresh candidate QR pairing."""

import json
import os
import secrets
import sys
import uuid

import experiment
import lab


def main():
    os.umask(0o077)
    lab.local_docker()
    with lab.exclusive_experiment():
        for name in lab.CONTAINERS:
            if not lab.owned("container", name):
                raise lab.LabError("STOP: expected local lab resources absent.")
        if lab.request("/license/status").get("status") != "active":
            raise lab.LabError("STOP: local license inactive.")
        path = lab.STATE / "pairing-check.json"
        if not path.exists():
            lab.private_file(path, json.dumps({"id": str(uuid.uuid4()), "name": "offline-sync-qr-check",
                                               "token": secrets.token_hex(32)}) + "\n")
        instance = json.loads(path.read_text())
        existing = lab.request("/instance/all", lab.admin_key()).get("data", [])
        matches = [row for row in existing if row.get("id") == instance["id"] or row.get("name") == instance["name"]]
        if matches:
            if len(matches) != 1 or matches[0].get("id") != instance["id"] or matches[0].get("token") != instance["token"]:
                raise lab.LabError("STOP: separate QR instance identity collision.")
        else:
            lab.request("/instance/create", lab.admin_key(), {"instanceId": instance["id"],
                        "name": instance["name"], "token": instance["token"]})
        state = experiment.instance_state(instance)
        info = lab.request("/instance/info/" + instance["id"], lab.admin_key()).get("data", {})
        if info.get("jid"):
            print("QR check already has saved pairing; no new QR requested.")
        elif not state["connected"]:
            lab.request("/instance/connect", instance["token"], {
                "webhookUrl": "http://" + lab.PROJECT + "-receiver:8081/webhook",
                "subscribe": ["ALL"], "rabbitmqEnable": "false", "natsEnable": "false", "websocketEnable": "false"})
        print("Only target QR on this separate page is new; sender remains paired. Use the target test phone.", flush=True)
    # Read-only page stays available while independent traffic tests run later.
    lab.qr_page({"target": instance, "sender": experiment.instances()["sender"]}, port=18082)


if __name__ == "__main__":
    try:
        main()
    except lab.LabError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
