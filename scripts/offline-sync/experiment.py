#!/usr/bin/env python3
"""Measure real WhatsApp reconnects against the explicitly local disposable lab."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error

import lab


def utc(epoch=None):
    return datetime.fromtimestamp(time.time() if epoch is None else epoch, timezone.utc).isoformat().replace("+00:00", "Z")


def instances():
    return json.loads((lab.STATE / "instances.json").read_text())


def instance_state(instance):
    state = lab.request("/instance/status", instance["token"]).get("data", {})
    return {"connected": state.get("Connected") is True, "logged_in": state.get("LoggedIn") is True}


def authenticated(instance):
    state = instance_state(instance)
    return state["connected"] and state["logged_in"]


def events():
    path = lab.STATE / "events" / "events.jsonl"
    if not path.exists():
        return []
    # The receiver appends records. An incomplete last line is not a record yet.
    lines = path.read_text().splitlines(keepends=True)
    return [json.loads(line) for line in lines if line.endswith("\n")]


def received(instance, marker):
    identity = hashlib.sha256(instance["id"].encode()).hexdigest()
    return [row for row in events() if row.get("instance_id_sha256") == identity
            and row.get("event") == "Message" and row.get("from_me") is False
            and row.get("marker") == marker]


def wait_for(predicate, timeout, interval=0.2):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return bool(predicate())


def send(source, destination, marker):
    if not authenticated(source):
        raise lab.LabError("Test sender is unauthenticated; message not sent.")
    # Resolve the test account locally. Never print or persist its phone/JID.
    info = lab.request("/instance/info/" + destination["id"], lab.admin_key()).get("data", {})
    jid = info.get("jid") or ""
    user, separator, server = jid.partition("@")
    if not separator or server != "s.whatsapp.net":
        raise lab.LabError("Saved test recipient is not a phone JID; stop before guessing.")
    number = user.split(":", 1)[0] + "@s.whatsapp.net"
    started = time.time()
    result = lab.request("/send/text", source["token"], {"number": number, "text": marker,
                         "formatJid": False}, timeout=30)
    if result.get("message") != "success":
        raise lab.LabError("Local send was not acknowledged; response withheld.")
    return {"marker": marker, "request_utc": utc(started), "accepted_utc": utc(),
            "elapsed_seconds": round(time.time() - started, 3), "accepted": True}


def log_counts(target, start, until=None):
    command = ["logs", "--timestamps", "--since", start]
    if until is not None:
        command += ["--until", until]
    raw = lab.docker(*command, lab.CONTAINERS[0])
    counts = {"connected": 0, "offline_preview": 0, "offline_completed": 0,
              "automatic_restart": 0, "process_handler_panics": 0, "process_stream_errors": 0}
    # Full lines are neither saved nor returned. Process-level library errors have
    # no instance ID, so do not attribute them to the target or call them its rate.
    for line in (raw.stdout + raw.stderr).splitlines():
        if "Event handler panicked" in line:
            counts["process_handler_panics"] += 1
        if "stream:error" in line:
            counts["process_stream_errors"] += 1
        if target["id"] not in line:
            continue
        for key, marker in (("connected", "events.Connected to Whatsapp"),
                            ("offline_preview", "Unhandled event *events.OfflineSyncPreview"),
                            ("offline_completed", "Event: OfflineSyncCompleted,"),
                            ("automatic_restart", "Disconnected detected, restarting instance")):
            if marker in line:
                counts[key] += 1
    return counts


def checkpoint(report, json_path, markdown_path):
    lab.private_file(json_path, json.dumps(report, indent=2) + "\n")
    rows = ["# Local WhatsApp reconnect experiment", "",
            "Status: **" + report["status"] + "**", "",
            "- Run: `" + report["run"] + "`; label: `" + report["label"] + "`.",
            "- Started: " + report["started_utc"] + ".",
            "- Image ID: `" + report["image_id"] + "`.",
            "- Method: " + ("real TCP closure through target-only CONNECT proxy; application's Disconnected handler reconnects"
                              if report.get("method") == "socket" else
                              "local POST /instance/reconnect invokes ReconnectClient on target only") + ".",
            "- Recovery/observation window: " + str(report["recovery_seconds"]) + " seconds.",
            "- Initial/before marker timeout: 30 seconds. Target API restart delay is the unchanged application default (2 seconds).",
            "- A during marker is confirmed only if target was offline at request and still offline after sender acknowledgement.",
            "- Markers are synthetic; account identifiers, tokens and raw logs are excluded.", "",
            "| Cycle | During send confirmed offline | Connected after | Preview | Completed | Before/during/after delivered | Target outbound delivered | Result |",
            "|---|---|---|---|---|---|---|---|"]
    for cycle in report["cycles"]:
        counts = cycle.get("logs", {})
        delivery = cycle.get("received", {})
        rows.append("| {cycle} | {during} | {connected} | {preview} | {completed} | {delivery} | {outbound} | {result} |".format(
            cycle=cycle["cycle"], during=cycle.get("during_confirmed", False),
            connected=cycle.get("reconnected", False), preview=counts.get("offline_preview", 0),
            completed=counts.get("offline_completed", 0),
            delivery="/".join(str(bool(delivery.get(phase))) for phase in ("before", "during", "after")),
            outbound=cycle.get("outbound_received", False), result=cycle.get("result", "in_progress")))
    if report.get("stop_reason"):
        rows += ["", "Stop reason: " + report["stop_reason"]]
    if report.get("method") == "socket":
        rows += ["", "Socket outage: " + str(report["down_seconds"]) + " seconds; independent gate restore within 20 seconds.",
                 "", "| Cycle | Tunnels closed | Disconnected-triggered restarts | Sender remained authenticated | Gate restored |",
                 "|---|---|---|---|---|"]
        for cycle in report["cycles"]:
            rows.append("| %s | %s | %s | %s | %s |" % (
                cycle["cycle"], cycle.get("proxy_drop", {}).get("closed_tunnels", "pending"),
                cycle.get("logs", {}).get("automatic_restart", 0),
                cycle.get("sender_remained_authenticated", "pending"),
                cycle.get("proxy_restored", {}).get("gate_open", "pending")))
    lab.private_file(markdown_path, "\n".join(rows) + "\n")


def run(args):
    accounts = instances()
    target, sender = accounts["target"], accounts["sender"]
    for name in lab.CONTAINERS:
        if not lab.owned("container", name):
            raise lab.LabError("All labelled lab containers are required.")
    if lab.request("/license/status").get("status") != "active":
        raise lab.LabError("STOP: local license is inactive.")
    if not authenticated(target) or not authenticated(sender):
        raise lab.LabError("STOP: both test accounts must be authenticated before the experiment.")
    if args.method == "socket":
        expected = json.loads((lab.STATE / "proxy.json").read_text())
        routes = lab.proxy_routes(accounts)
        for role, route in routes.items():
            target_matches = all(route.get(field) == expected[field] for field in ("protocol", "host", "port")) and route["has_auth"]
            if (role == "target" and not target_matches) or (role == "sender" and route["host"]):
                raise lab.LabError("STOP: target-only proxy routing could not be verified.")
        stats = lab.proxy_control()
        if not stats["gate_open"] or not stats["active_tunnels"] or stats["rejected_auth"]:
            raise lab.LabError("STOP: target proxy is not healthy; do not run a fake socket test.")
    run_id = secrets.token_hex(4)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    report = {"run": run_id, "label": args.label, "method": args.method, "harness_commit": revision,
              "down_seconds": args.down_seconds if args.method == "socket" else None,
              "status": "preflight", "started_utc": utc(),
              "image_id": lab.docker("container", "inspect", "--format", "{{.Image}}", lab.CONTAINERS[0]).stdout.strip(),
              "recovery_seconds": args.recovery_seconds, "cycles": []}
    output = lab.STATE / "results"
    output.mkdir(exist_ok=True, mode=0o700)
    prefix = args.label + ("-socket" if args.method == "socket" else "")
    json_path = output / (prefix + "-" + run_id + ".json")
    markdown_path = lab.ROOT / "docs" / "investigations" / ("2026-11-11-offline-sync-" + prefix + "-" + run_id + ".md")
    save = lambda: checkpoint(report, json_path, markdown_path)
    save()
    print("Experiment report: " + str(markdown_path), flush=True)
    try:
        initial = "EVOSYNC-" + run_id + "-C00-before"
        report["initial_probe"] = send(sender, target, initial)
        if not wait_for(lambda: received(target, initial), 30):
            raise lab.LabError("STOP: initial inbound marker did not reach the webhook; no valid before baseline.")
        report["status"] = "running"
        save()
        for index in range(1, args.cycles + 1):
            started = utc()
            cycle = {"cycle": index, "started_utc": started, "sends": {}, "received": {}}
            report["cycles"].append(cycle)
            save()
            if not authenticated(target) or not authenticated(sender):
                raise lab.LabError("STOP: an account lost authentication before the next cycle.")
            markers = {phase: "EVOSYNC-%s-C%02d-%s" % (run_id, index, phase)
                       for phase in ("before", "during", "after", "outbound")}
            cycle["sends"]["before"] = send(sender, target, markers["before"])
            if not wait_for(lambda: received(target, markers["before"]), 30):
                raise lab.LabError("STOP: before marker was not delivered; cannot start another reconnect.")
            cycle["received"]["before"] = True
            if args.method == "socket":
                # Drop genuine target TCP sockets. Do not call any app reconnect
                # endpoint: its unchanged Disconnected handler must do the work.
                down_at = time.monotonic()
                try:
                    cycle["proxy_drop"] = lab.proxy_control("drop")
                    save()
                    if not cycle["proxy_drop"]["closed_tunnels"]:
                        raise lab.LabError("STOP: no active target socket was closed; invalid cycle.")
                    disconnected = wait_for(lambda: not instance_state(target)["connected"], 5, interval=0.05)
                    cycle["disconnect_observed"] = disconnected
                    if not disconnected:
                        raise lab.LabError("STOP: socket drop did not disconnect target; possible direct fallback.")
                    cycle["sends"]["during"] = send(sender, target, markers["during"])
                    cycle["sender_remained_authenticated"] = authenticated(sender)
                    cycle["during_confirmed"] = (not instance_state(target)["connected"]
                                                  and not lab.proxy_control()["gate_open"])
                    save()
                    time.sleep(max(0, args.down_seconds - (time.monotonic() - down_at)))
                finally:
                    cycle["proxy_restored"] = lab.proxy_control("up")
                    save()
                if not cycle["sender_remained_authenticated"]:
                    raise lab.LabError("STOP: sender lost authentication during target outage.")
            else:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    reconnect = executor.submit(lab.request, "/instance/reconnect", target["token"], {}, 30)
                    disconnected = wait_for(lambda: not instance_state(target)["connected"], 10, interval=0.05)
                    cycle["disconnect_observed"] = disconnected
                    if disconnected:
                        cycle["sends"]["during"] = send(sender, target, markers["during"])
                        cycle["during_confirmed"] = not instance_state(target)["connected"]
                    reconnect.result()
            cycle["reconnected"] = wait_for(lambda: authenticated(target), args.recovery_seconds)
            if not cycle["reconnected"]:
                cycle["result"] = "recovery_failed"
                cycle["logs"] = log_counts(target, started)
                raise lab.LabError("STOP: target failed to authenticate after reconnect; ask Tuan before recovery.")
            cycle["sends"]["after"] = send(sender, target, markers["after"])
            # Also prove target sending independently of inbound delivery.
            cycle["sends"]["outbound"] = send(target, sender, markers["outbound"])
            observation_end = time.monotonic() + args.recovery_seconds
            while time.monotonic() < observation_end:
                cycle["received"].update({phase: bool(received(target, markers[phase]))
                                          for phase in ("during", "after")})
                cycle["outbound_received"] = bool(received(sender, markers["outbound"]))
                cycle["logs"] = log_counts(target, started)
                if all(cycle["received"].values()) and cycle["outbound_received"] and cycle["logs"]["offline_completed"]:
                    break
                save()
                time.sleep(2)
            cycle["finished_utc"] = utc()
            if not cycle.get("during_confirmed"):
                cycle["result"] = "inconclusive_during_window"
                raise lab.LabError("STOP: could not confirm sender acknowledgement during the outage; ask before changing the method.")
            missing = not all(cycle["received"].get(phase) for phase in ("during", "after"))
            if cycle["logs"]["offline_preview"] and not cycle["logs"]["offline_completed"] and missing and cycle["outbound_received"]:
                cycle["result"] = "incident_reproduced"
                report["status"] = "incident_reproduced"
                save()
                print(json.dumps(cycle), flush=True)
                # Preserve the failing session for read-only diagnosis; do not recover it.
                return
            if missing or not cycle["outbound_received"]:
                cycle["result"] = "delivery_failed"
                raise lab.LabError("STOP: delivery failed without the complete incident signature; ask before expanding scope.")
            cycle["result"] = "pass" if cycle["logs"]["offline_completed"] else "delivery_pass_sync_unobserved"
            save()
            print(json.dumps(cycle), flush=True)
        report["status"] = "not_reproduced"
        report["stop_reason"] = ("Required cycles completed without reproducing the full incident. Ask Tuan before any dependency update."
                                 if args.label == "before" else
                                 "Required candidate cycles completed; this establishes local compatibility, not the production incident's cause.")
    except (lab.LabError, OSError, ValueError, KeyboardInterrupt) as error:
        report["status"] = "stopped"
        report["stop_reason"] = str(error) if isinstance(error, lab.LabError) else "Experiment interrupted or local operation failed; raw details withheld."
        save()
        raise lab.LabError(report["stop_reason"]) from None
    finally:
        report["updated_utc"] = utc()
        save()
    print(json.dumps({"status": report["status"], "cycles": len(report["cycles"]), "report": str(markdown_path)}), flush=True)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", choices=["before", "after"], default="before")
    parser.add_argument("--method", choices=["api", "socket"], default="api")
    parser.add_argument("--down-seconds", type=int, default=10)
    parser.add_argument("--cycles", type=int, default=10)
    parser.add_argument("--recovery-seconds", type=int, default=180)
    args = parser.parse_args()
    if args.cycles < 10 or args.cycles > 50 or args.recovery_seconds < 30:
        parser.error("Use 10..50 cycles and at least 30 seconds of recovery observation.")
    if not 5 <= args.down_seconds <= 15:
        parser.error("Use a 5..15 second socket outage below the independent 20 second restore.")
    lab.local_docker()
    with lab.exclusive_experiment():
        run(args)


if __name__ == "__main__":
    try:
        main()
    except lab.LabError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
