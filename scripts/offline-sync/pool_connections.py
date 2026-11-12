#!/usr/bin/env python3
"""Count real local auth-DB sessions across sequential target reconnections."""

import argparse
import json
import secrets
import subprocess
import sys
import time

import experiment
import lab


def connections():
    # Use postgres, not the measured database: the observer must not count itself.
    # Never collect query text, client addresses, credentials or connection strings.
    sql = """SELECT json_build_object(
        'total', count(*),
        'active', count(*) FILTER (WHERE state = 'active'),
        'idle', count(*) FILTER (WHERE state = 'idle'),
        'idle_in_transaction', count(*) FILTER (WHERE state LIKE 'idle in transaction%')
    ) FROM pg_stat_activity WHERE datname = 'offline_sync_auth';"""
    result = lab.docker("exec", lab.CONTAINERS[2], "psql", "-U", "lab", "-d", "postgres",
                        "-At", "-v", "ON_ERROR_STOP=1", "-c", sql)
    return {"utc": experiment.utc(), **json.loads(result.stdout)}


def checkpoint(report, json_path, markdown_path):
    lab.private_file(json_path, json.dumps(report, indent=2) + "\n")
    lines = ["# Local PostgreSQL auth connection experiment", "",
             "Status: **" + report["status"] + "**", "",
             "- Run: `" + report["run"] + "`; label: `" + report["label"] + "`.",
             "- Image: `" + report["image_id"] + "`.",
             "- Harness commit: `" + report["harness_commit"] + "`.",
             "- Started: " + report["started_utc"] + ".",
             "- Method: target-only `/instance/reconnect`; sender stays online.",
             "- Observer: maintenance database `postgres`; measured database `offline_sync_auth`.",
             "- Settling: 10s initially, 3s after each cycle, 30s finally.", "",
             "| Sample | Total | Active | Idle | Sync complete | Probe delivered |",
             "|---|---:|---:|---:|---|---|"]
    for label, sample in [("initial", report.get("initial"))] + [
        (str(row["cycle"]), row.get("connections")) for row in report["cycles"]
    ] + [("final", report.get("final"))]:
        if sample is not None:
            cycle = next((row for row in report["cycles"] if str(row["cycle"]) == label), {})
            lines.append("| %s | %d | %d | %d | %s | %s |" % (
                label, sample["total"], sample["active"], sample["idle"],
                cycle.get("sync_complete", "—"), cycle.get("delivered", "—")))
    if "delta" in report:
        lines += ["", "Final minus initial: **%+d** connections." % report["delta"],
                  "Verdict: `" + report["status"] + "` (counts observed over this run only)."]
    if report.get("stop_reason"):
        lines += ["", "Stop reason: " + report["stop_reason"]]
    lines += ["", "No production database was consulted. Session query text, message content,",
              "phone numbers and credentials were neither recorded nor printed."]
    lab.private_file(markdown_path, "\n".join(lines) + "\n")


def run(args):
    for name in lab.CONTAINERS:
        if not lab.owned("container", name):
            raise lab.LabError("STOP: labelled local lab containers are required.")
    if lab.request("/license/status").get("status") != "active":
        raise lab.LabError("STOP: local license is inactive.")
    accounts = experiment.instances()
    target, sender = accounts["target"], accounts["sender"]
    if not all(experiment.authenticated(account) for account in (target, sender)):
        raise lab.LabError("STOP: both saved test devices must be authenticated.")
    run_id = secrets.token_hex(4)
    report = {"run": run_id, "label": args.label, "status": "running", "cycles": [],
              "started_utc": experiment.utc(), "requested_cycles": args.cycles,
              "harness_commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                                text=True, check=True).stdout.strip(),
              "image_id": lab.docker("container", "inspect", "--format", "{{.Image}}",
                                      lab.CONTAINERS[0]).stdout.strip()}
    output = lab.STATE / "results"
    output.mkdir(exist_ok=True, mode=0o700)
    json_path = output / ("pools-" + args.label + "-" + run_id + ".json")
    markdown_path = lab.ROOT / "docs" / "investigations" / (
        "2026-11-11-auth-pools-" + args.label + "-" + run_id + ".md")
    save = lambda: checkpoint(report, json_path, markdown_path)
    save()
    print("Pool report: " + str(markdown_path), flush=True)
    try:
        # Warm up both directions before the initial sample, so lazy SQL opens
        # needed for normal message traffic do not appear as a reconnect leak.
        for source, destination in ((sender, target), (target, sender)):
            marker = "EVOSYNC-" + run_id + "-warmup-" + ("in" if destination is target else "out")
            experiment.send(source, destination, marker)
            if not experiment.wait_for(lambda: experiment.received(destination, marker), 30):
                raise lab.LabError("STOP: warm-up delivery failed; no valid baseline.")
        time.sleep(10)
        report["initial"] = connections()
        save()
        print(json.dumps({"sample": "initial", **report["initial"]}), flush=True)
        for index in range(1, args.cycles + 1):
            row = {"cycle": index, "started_utc": experiment.utc()}
            report["cycles"].append(row)
            save()
            if not all(experiment.authenticated(account) for account in (target, sender)):
                raise lab.LabError("STOP: a test account lost authentication before reconnect.")
            lab.request("/instance/reconnect", target["token"], {}, timeout=30)
            if not experiment.wait_for(lambda: experiment.authenticated(target), 60):
                raise lab.LabError("STOP: target did not authenticate after reconnect.")
            row["sync_complete"] = experiment.wait_for(
                lambda: experiment.log_counts(target, row["started_utc"])["offline_completed"] > 0, 60, 1)
            if not row["sync_complete"]:
                raise lab.LabError("STOP: target offline synchronization did not complete.")
            marker = "EVOSYNC-%s-pool-%02d" % (run_id, index)
            experiment.send(sender, target, marker)
            row["delivered"] = experiment.wait_for(lambda: experiment.received(target, marker), 30)
            if not row["delivered"]:
                raise lab.LabError("STOP: post-reconnect probe was not delivered.")
            time.sleep(3)
            row["logs"] = experiment.log_counts(target, row["started_utc"])
            row["sender_authenticated"] = experiment.authenticated(sender)
            row["connections"] = connections()
            save()
            print(json.dumps(row), flush=True)
            if not row["sender_authenticated"] or row["logs"]["connected"] != 1 or row["logs"]["automatic_restart"]:
                raise lab.LabError("STOP: unexpected disconnection confounded the sequential reconnect test.")
        time.sleep(30)
        report["final"] = connections()
        report["delta"] = report["final"]["total"] - report["initial"]["total"]
        report["status"] = "growth_observed" if report["delta"] > 0 else "stable"
        report["finished_utc"] = experiment.utc()
    except (lab.LabError, OSError, ValueError, KeyboardInterrupt) as error:
        report["status"] = "stopped"
        report["stop_reason"] = str(error) if isinstance(error, lab.LabError) else "Local operation failed; raw details withheld."
        raise lab.LabError(report["stop_reason"]) from None
    finally:
        save()
    print(json.dumps({"status": report["status"], "initial": report["initial"]["total"],
                      "final": report["final"]["total"], "delta": report["delta"]}), flush=True)
    if args.expect_stable and report["status"] != "stable":
        raise lab.LabError("FAIL: auth database connections grew across reconnects.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", choices=("before", "after"), required=True)
    parser.add_argument("--cycles", type=int, default=20)
    parser.add_argument("--expect-stable", action="store_true")
    args = parser.parse_args()
    if args.cycles < 10:
        parser.error("at least ten sequential reconnects are required")
    try:
        lab.local_docker()
        with lab.exclusive_experiment():
            run(args)
    except (lab.LabError, OSError, ValueError) as error:
        print(str(error) if isinstance(error, lab.LabError) else "Local operation failed; raw details withheld.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
