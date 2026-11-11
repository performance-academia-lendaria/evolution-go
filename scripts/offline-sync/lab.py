#!/usr/bin/env python3
"""Bootstrap an isolated local lab; never use existing credentials or devices."""

import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "build" / "offline-sync-lab"
PROJECT = "evo-offline-sync-lab"
LABEL = "evolution-go.offline-sync-lab=true"
IMAGE = "tuanmedeiros/evolution-go:0.7.2-0.1.0"
API_URL = "http://127.0.0.1:18080"
CONTAINERS = [PROJECT + "-api", PROJECT + "-receiver", PROJECT + "-postgres"]
NETWORKS = [PROJECT + "-egress", PROJECT + "-data"]
DOCKER = []


class LabError(Exception):
    pass


def docker(*args, required=True):
    # Capture all output: Docker errors can include environment/credential values.
    result = subprocess.run(DOCKER + list(args), capture_output=True, text=True)
    if required and result.returncode:
        raise LabError("Docker operation failed (%s); raw output withheld." % args[0])
    return result


def local_docker():
    # Bind to an explicit Unix socket so DOCKER_HOST/DOCKER_CONTEXT cannot redirect
    # later operations. Reject SSH and TCP daemons, including remote production.
    context = subprocess.run(
        ["docker", "context", "show"], capture_output=True, text=True, check=True
    ).stdout.strip()
    endpoint = subprocess.run(
        ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}", context],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if not endpoint.startswith("unix://"):
        raise LabError("A local Docker Unix socket is required; refusing this daemon.")
    DOCKER.extend(["docker", "--host", endpoint])
    docker("info", "--format", "{{.OperatingSystem}}")


def owned(kind, name):
    result = docker(kind, "inspect", "--format", '{{index .Labels "evolution-go.offline-sync-lab"}}'
                    if kind == "network" else
                    '{{index .Config.Labels "evolution-go.offline-sync-lab"}}',
                    name, required=False)
    if result.returncode:
        return False
    if result.stdout.strip() != "true":
        raise LabError("Name collision with a resource not owned by this lab: " + name)
    return True


def private_file(path, content):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(content)


def request(path):
    # Fixed loopback URL and no environment proxies. Never print response bodies.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(API_URL + path, timeout=5) as response:
        return json.load(response)


def status():
    result = {"api_url": API_URL, "resources": {}}
    for name in CONTAINERS:
        if owned("container", name):
            state = docker("container", "inspect", "--format", "{{.State.Status}}", name)
            result["resources"][name] = state.stdout.strip()
        else:
            result["resources"][name] = "absent"
    if result["resources"][PROJECT + "-api"] == "running":
        try:
            # Select only the status; /license/status may also include key fragments.
            license_status = request("/license/status").get("status")
            result["license"] = license_status if license_status in ("active", "inactive") else "unknown"
        except (OSError, ValueError, urllib.error.URLError):
            result["license"] = "unavailable"
    else:
        result["license"] = "unavailable"
    print(json.dumps(result, indent=2))
    return result


def up():
    if STATE.exists():
        raise LabError("Lab state already exists. Use status; do not overwrite or reinitialize it.")
    for name in CONTAINERS:
        if owned("container", name):
            raise LabError("Lab container already exists. Use status or down first.")
    for name in NETWORKS:
        if owned("network", name):
            raise LabError("Lab network already exists. Use down first.")
    # Use existing local image IDs; do not pull a mutable reference for the baseline.
    images = {}
    for image in (IMAGE, "postgres:16-alpine", "python:3.12-slim"):
        info = docker("image", "inspect", "--format", "{{.Id}}", image)
        images[image] = info.stdout.strip()

    STATE.mkdir(parents=True, mode=0o700)
    (STATE / "events").mkdir(mode=0o700)
    password = secrets.token_hex(32)
    admin_key = secrets.token_hex(32)
    private_file(STATE / "postgres.env", "POSTGRES_USER=lab\nPOSTGRES_PASSWORD=" + password + "\n")
    database = "postgres://lab:" + password + "@" + PROJECT + "-postgres:5432/"
    private_file(STATE / "api.env", "\n".join([
        "SERVER_PORT=8080", "GLOBAL_API_KEY=" + admin_key,
        "POSTGRES_USERS_DB=" + database + "offline_sync_instances?sslmode=disable",
        "POSTGRES_AUTH_DB=" + database + "offline_sync_auth?sslmode=disable",
        "DATABASE_SAVE_MESSAGES=false", "CONNECT_ON_STARTUP=false",
        "WEBHOOK_FILES=false", "AMQP_GLOBAL_ENABLED=false", "NATS_GLOBAL_ENABLED=false",
        "CLIENT_NAME=Offline Sync Lab", "OS_NAME=Chrome", "LOG_TYPE=console",
        "QRCODE_MAX_COUNT=0", "DEBUG_ENABLED=false", "",
    ]))
    private_file(STATE / "identity.json", json.dumps({
        "baseline_image": IMAGE, "images": images,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": "Local image; production digest and source equivalence need separate verification.",
    }, indent=2) + "\n")

    docker("network", "create", "--internal", "--label", LABEL, NETWORKS[1])
    docker("network", "create", "--label", LABEL, NETWORKS[0])
    docker("run", "-d", "--name", CONTAINERS[2], "--label", LABEL,
           "--network", NETWORKS[1], "--env-file", str(STATE / "postgres.env"),
           "--tmpfs", "/var/lib/postgresql/data:rw", images["postgres:16-alpine"])
    for _ in range(60):
        ready = docker("exec", CONTAINERS[2], "pg_isready", "-U", "lab", required=False)
        if ready.returncode == 0:
            break
        time.sleep(1)
    else:
        raise LabError("Temporary PostgreSQL did not become ready. Use status or down.")

    docker("run", "-d", "--name", CONTAINERS[1], "--label", LABEL,
           "--network", NETWORKS[1], "--read-only", "--tmpfs", "/tmp",
           "--mount", "type=bind,src=" + str(Path(__file__).with_name("receiver.py")) + ",dst=/receiver.py,readonly",
           "--mount", "type=bind,src=" + str(STATE / "events") + ",dst=/events",
           images["python:3.12-slim"], "python", "-B", "/receiver.py")
    docker("run", "-d", "--name", CONTAINERS[0], "--label", LABEL,
           "--platform", "linux/amd64",
           "--network", "name=" + NETWORKS[0] + ",gw-priority=1",
           "--network", "name=" + NETWORKS[1] + ",gw-priority=0",
           "--publish", "127.0.0.1:18080:8080", "--env-file", str(STATE / "api.env"),
           images[IMAGE])
    for _ in range(90):
        try:
            request("/license/status")
            break
        except (OSError, ValueError, urllib.error.URLError):
            time.sleep(1)
    result = status()
    if result["license"] != "active":
        raise LabError("STOP: local license is not active. Ask Tuan before any activation or workaround.")
    print("Bootstrap ready. Pairing and reconnection measurements have not been run.")


def down():
    # Only our labelled resources are eligible, on the explicitly local daemon.
    # PostgreSQL uses tmpfs: removing its container irreversibly erases lab data.
    for name in CONTAINERS:
        if owned("container", name):
            docker("rm", "-f", "-v", name)
    for name in NETWORKS:
        if owned("network", name):
            docker("network", "rm", name)
    print("Lab containers and networks removed; local state files retained for explicit cleanup.")


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["up", "status", "down"])
    args = parser.parse_args()
    local_docker()
    {"up": up, "status": status, "down": down}[args.command]()


if __name__ == "__main__":
    try:
        main()
    except (LabError, subprocess.SubprocessError) as error:
        # Never echo arbitrary subprocess output, HTTP bodies or exception details.
        print(str(error) if isinstance(error, LabError) else "Local command failed; raw output withheld.", file=sys.stderr)
        sys.exit(1)
