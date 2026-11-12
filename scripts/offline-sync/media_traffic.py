#!/usr/bin/env python3
"""Verify synthetic text/image/audio delivery and continuous local lab traffic."""

import argparse
import base64
import hashlib
import io
import json
import math
import os
import secrets
import struct
import subprocess
import sys
import time
import wave
import zlib

import experiment
import lab
from recovery_monitor import RecoveryMonitor


def fixtures():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 32, 32, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress((b"\x00" + b"\x40\x80\xc0" * 32) * 32)) + chunk(b"IEND", b""))
    audio = io.BytesIO()
    with wave.open(audio, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(b"".join(struct.pack("<h", int(1800 * math.sin(2 * math.pi * 440 * i / 16000)))
                                    for i in range(16000)))
    return {"image": png, "audio": audio.getvalue()}


def send(source, destination, kind, marker, files, timeout=60):
    # Recipient lookup and credentials stay in memory; output contains hashes only.
    info = lab.request("/instance/info/" + destination["id"], lab.admin_key()).get("data", {})
    user, separator, server = (info.get("jid") or "").partition("@")
    if not separator or server != "s.whatsapp.net":
        raise lab.LabError("STOP: recipient has no saved test phone JID.")
    payload = {"number": user.split(":", 1)[0] + "@s.whatsapp.net", "formatJid": False}
    path = "/send/text" if kind == "text" else "/send/media"
    if kind == "text":
        payload["text"] = marker
    else:
        payload.update(type=kind, url=base64.b64encode(files[kind]).decode(),
                       caption=marker if kind == "image" else "", filename="synthetic." + ("png" if kind == "image" else "wav"))
    started = time.time()
    result = lab.request(path, source["token"], payload, timeout=timeout)
    identifier = result.get("data", {}).get("Info", {}).get("ID")
    if result.get("message") != "success" or not isinstance(identifier, str) or not identifier:
        raise lab.LabError("STOP: send was not acknowledged with an ID; response withheld.")
    return {"kind": kind, "request_utc": experiment.utc(started), "accepted_utc": experiment.utc(),
            "message_id_sha256": hashlib.sha256(identifier.encode()).hexdigest(),
            "destination_sha256": hashlib.sha256(destination["id"].encode()).hexdigest(),
            "delivered": False}


def delivered(row):
    return next((event for event in experiment.events()
                 if event.get("instance_id_sha256") == row["destination_sha256"]
                 and event.get("message_id_sha256") == row["message_id_sha256"]
                 and event.get("event") == "Message" and event.get("from_me") is False
                 and event.get("kind") == row["kind"]), None)


def save(report, json_path, markdown_path):
    lab.private_file(json_path, json.dumps(report, indent=2) + "\n")
    lines = ["# Local media and continuous traffic verification", "",
             "Status: **" + report["status"] + "**", "",
             "- Run: `" + report["run"] + "`; label: `" + report["label"] + "`.",
             "- Image: `" + report["image_id"] + "`.",
             "- Harness commit: `" + report["harness_commit"] + "`.",
             "- Started: " + report["started_utc"] + ".",
             "- Requested duration: %s seconds; interval: %s seconds." % (report["duration_seconds"], report["interval_seconds"]),
             ("- Controlled preflight: one induced target outage, excluded from natural-drop rates."
              if report.get("controlled_preflight") else
              "- Only synthetic content, between two exclusive test accounts; no forced outages."),
             "- PNG solid color; WAV 1-second tone sent through normal local audio conversion.",
             "- Delivery requires matching hashed ID, incoming Message and correct media kind.",
             "- Authentication sampled every 2 seconds between batches and before each send.", "",
             "| Batch | Text delivered | Image delivered | Audio delivered |", "|---|---|---|---|"]
    for batch in report["batches"]:
        lines.append("| %s | %s | %s | %s |" % (batch["batch"], *[
            "%s/2" % sum(row["delivered"] for row in batch["messages"] if row["kind"] == kind)
            for kind in ("text", "image", "audio")]))
    for field in ("recovery_seconds", "drop_counts", "recovered_drops", "drops", "interrupted_send_attempts",
                  "recovery_probe_failures", "last_health_utc", "drops_per_hour",
                  "observed_until_utc", "stop_target_logs", "stop_sender_logs",
                  "finished_utc", "elapsed_seconds", "authentication_samples", "stop_reason", "target_logs", "sender_logs"):
        if field in report:
            lines += ["", "- " + field + ": " + json.dumps(report[field])]
    lab.private_file(markdown_path, "\n".join(lines) + "\n")


def run(args):
    for name in lab.CONTAINERS:
        if not lab.owned("container", name):
            raise lab.LabError("STOP: all labelled lab containers are required.")
    if lab.request("/license/status").get("status") != "active":
        raise lab.LabError("STOP: local license inactive.")
    accounts = experiment.instances()
    target, sender = accounts["target"], accounts["sender"]
    files = fixtures()
    run_id = secrets.token_hex(4)
    started = time.monotonic()
    started_epoch = time.time()
    report = {"run": run_id, "label": args.label, "started_epoch": started_epoch,
              "started_utc": experiment.utc(started_epoch), "status": "running",
              "harness_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=lab.ROOT,
                                                capture_output=True, text=True, check=True).stdout.strip(),
              "image_id": lab.docker("container", "inspect", "--format", "{{.Image}}", lab.CONTAINERS[0]).stdout.strip(),
              "duration_seconds": args.duration_seconds, "interval_seconds": args.interval_seconds,
              "authentication_samples": 0, "batches": [], "recovery_seconds": args.recovery_seconds,
              "interrupted_send_attempts": 0}
    output = lab.STATE / "results"
    output.mkdir(exist_ok=True, mode=0o700)
    prefix = "media-" + args.label + "-" + run_id
    json_path = output / (prefix + ".json")
    markdown_path = lab.ROOT / "docs" / "investigations" / ("2026-11-11-offline-sync-" + prefix + ".md")
    checkpoint = lambda: save(report, json_path, markdown_path)

    monitor = None
    if args.recovery_seconds:
        if not all(experiment.authenticated(account) for account in accounts.values()):
            raise lab.LabError("STOP: both test accounts must start authenticated.")

        def probe(role, timeout):
            other = "sender" if role == "target" else "target"
            return send(accounts[other], accounts[role], "text",
                        "EVOSYNC-%s-C99-after" % run_id, files, timeout=timeout)

        monitor = RecoveryMonitor(accounts, report, checkpoint, probe, delivered, args.recovery_seconds)

    def check_auth():
        if monitor is not None:
            monitor.check()
            return
        if not experiment.authenticated(target) or not experiment.authenticated(sender):
            raise lab.LabError("STOP: authentication lost; preserve sessions and ask Tuan before recovery.")
        report["authentication_samples"] += 1

    checkpoint()
    print("Media report: " + str(markdown_path), flush=True)
    try:
        next_batch = started
        while True:
            check_auth()
            if time.monotonic() >= next_batch:
                batch = {"batch": len(report["batches"]) + 1, "started_utc": experiment.utc(), "messages": []}
                report["batches"].append(batch)
                for source, destination, phase in ((sender, target, "before"), (target, sender, "outbound")):
                    for kind in ("text", "image", "audio"):
                        check_auth()
                        marker = "EVOSYNC-%s-C%02d-%s" % (run_id, batch["batch"], phase)
                        try:
                            row = send(source, destination, kind, marker, files)
                        except (lab.LabError, OSError):
                            if monitor is None:
                                raise
                            drops_before = len(report["drops"])
                            check_auth()
                            if len(report["drops"]) == drops_before:
                                raise
                            # Retry only after a newly observed, proven recovery.
                            # The failed request had no acknowledged ID to track.
                            report["interrupted_send_attempts"] += 1
                            checkpoint()
                            row = send(source, destination, kind, marker, files)
                        batch["messages"].append(row)
                        checkpoint()
                        def arrived():
                            check_auth()
                            return delivered(row)

                        if not experiment.wait_for(arrived, 30):
                            raise lab.LabError("STOP: acknowledged synthetic message missing from webhook; preserve session.")
                        row["delivered"] = True
                        row["received_utc"] = experiment.utc(delivered(row)["received_utc"])
                        checkpoint()
                print(json.dumps({"batch": batch["batch"], "delivered": len(batch["messages"]),
                                  "elapsed_seconds": round(time.monotonic() - started, 3)}), flush=True)
                next_batch += args.interval_seconds
            if time.monotonic() - started >= args.duration_seconds:
                break
            # Short polling keeps interruptions responsive and samples account health.
            time.sleep(min(2, max(0, next_batch - time.monotonic())))
        if monitor is not None:
            monitor.finalize()
            if report["target_logs"]["process_handler_panics"]:
                raise lab.LabError("STOP: event handler panic during continuous traffic.")
        else:
            report["target_logs"] = experiment.log_counts(target, report["started_utc"])
            report["sender_logs"] = experiment.log_counts(sender, report["started_utc"])
            if any(report[role][key] for role in ("target_logs", "sender_logs")
                   for key in ("automatic_restart", "process_handler_panics", "process_stream_errors")):
                raise lab.LabError("STOP: reconnect, panic or stream error during continuous traffic; inspect sanitized counts.")
        report["status"] = "pass"
    except (lab.LabError, OSError, ValueError, KeyboardInterrupt) as error:
        report["status"] = "stopped"
        report["stop_reason"] = str(error) if isinstance(error, lab.LabError) else "Local verification interrupted; raw details withheld."
        raise lab.LabError(report["stop_reason"]) from None
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        report["finished_utc"] = experiment.utc()
        if monitor is not None:
            report["drops_per_hour"] = {role: round(count * 3600 / max(report["elapsed_seconds"], 1), 3)
                                         for role, count in report.get("drop_counts", {}).items()}
        if report["status"] != "pass":
            for role, account in accounts.items():
                try:
                    report["stop_" + role + "_logs"] = experiment.log_counts(account, report["started_utc"])
                except lab.LabError:
                    report["final_log_counts_unavailable"] = True
        checkpoint()
    print(json.dumps({"status": report["status"], "batches": len(report["batches"]),
                      "elapsed_seconds": report["elapsed_seconds"]}), flush=True)


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", choices=("before", "after"), required=True)
    parser.add_argument("--duration-seconds", type=int, default=0)
    parser.add_argument("--interval-seconds", type=int, default=300)
    parser.add_argument("--recovery-seconds", type=int, choices=(0, 60), default=0,
                        help="Explicitly allow natural drops only with reconnection, sync and inbound proof within60s.")
    args = parser.parse_args()
    if args.duration_seconds < 0 or args.interval_seconds < 1:
        parser.error("Duration must be nonnegative and interval positive.")
    lab.local_docker()
    try:
        with lab.exclusive_experiment():
            run(args)
    except lab.LabError as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
