#!/usr/bin/env python3
"""Bootstrap an isolated local lab; never use existing credentials or devices."""

import argparse
import base64
from contextlib import contextmanager
import fcntl
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid


ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "build" / "offline-sync-lab"
PROJECT = "evo-offline-sync-lab"
LABEL = "evolution-go.offline-sync-lab=true"
IMAGE = "tuanmedeiros/evolution-go:0.7.2-0.1.0"
API_URL = "http://127.0.0.1:18080"
CONTAINERS = [PROJECT + "-api", PROJECT + "-receiver", PROJECT + "-postgres"]
NETWORKS = [PROJECT + "-egress", PROJECT + "-data"]
PROXY = PROJECT + "-proxy"
DOCKER = []


class LabError(Exception):
    pass


@contextmanager
def exclusive_experiment():
    """Never let a fault test invalidate a simultaneous continuous traffic test."""
    with (STATE / "experiment.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise LabError("STOP: another lab experiment is active.") from None
        yield


def docker(*args, required=True, stdin=None):
    # Capture all output: Docker errors can include environment/credential values.
    result = subprocess.run(DOCKER + list(args), capture_output=True, text=True, input=stdin)
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


def request(path, token=None, payload=None, timeout=15):
    # Fixed loopback URL and no environment proxies. Never print response bodies.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    headers = {"Content-Type": "application/json"}
    if token:
        headers["apikey"] = token
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(API_URL + path, data=body, headers=headers)
    try:
        response = opener.open(req, timeout=timeout)
    except urllib.error.HTTPError as error:
        raise LabError("Local API returned HTTP %d for %s; response withheld." % (error.code, path)) from None
    with response:
        return json.load(response)


def admin_key():
    # Stop before database configuration; consume only the generated lab key.
    with (STATE / "api.env").open() as source:
        for line in source:
            if line.startswith("GLOBAL_API_KEY="):
                return line.rstrip("\r\n").split("=", 1)[1]
    raise LabError("Generated lab admin key is missing.")


def pair():
    """Create two lab instances idempotently and save their current QR images."""
    if request("/license/status").get("status") != "active":
        raise LabError("STOP: local license is not active.")
    if not owned("container", CONTAINERS[0]):
        raise LabError("The labelled lab API is required.")
    path = STATE / "instances.json"
    if path.exists():
        instances = json.loads(path.read_text())
    else:
        instances = {role: {"id": str(uuid.uuid4()), "name": "offline-sync-" + role,
                            "token": secrets.token_hex(32)} for role in ("target", "sender")}
        private_file(path, json.dumps(instances, indent=2) + "\n")
    key = admin_key()
    existing = request("/instance/all", key).get("data", [])
    if not isinstance(existing, list):
        raise LabError("Unexpected local instance listing; refusing to create duplicates.")
    for role, instance in instances.items():
        matches = [row for row in existing if row.get("id") == instance["id"] or row.get("name") == instance["name"]]
        if matches:
            if len(matches) != 1 or matches[0].get("id") != instance["id"] or matches[0].get("token") != instance["token"]:
                raise LabError("Local instance identity collision; refusing to reuse it.")
        else:
            request("/instance/create", key, {"instanceId": instance["id"],
                    "name": instance["name"], "token": instance["token"]})
        state = request("/instance/status", instance["token"]).get("data", {})
        if state.get("LoggedIn"):
            print(role + ": already paired; not requesting another QR.")
            continue
        request("/instance/connect", instance["token"], {
            "webhookUrl": "http://" + PROJECT + "-receiver:8081/webhook",
            "subscribe": ["ALL"], "rabbitmqEnable": "false", "natsEnable": "false",
            "websocketEnable": "false",
        })
        for _ in range(10):
            # /instance/qr may start a second client while /connect is starting.
            # Read the stored QR without invoking that mutating endpoint.
            data = request("/instance/info/" + instance["id"], key).get("data", {})
            encoded = (data.get("qrcode") or "").split("|", 1)[0]
            if encoded:
                if encoded.startswith("data:image/png;base64,"):
                    encoded = encoded.split(",", 1)[1]
                image = base64.b64decode(encoded, validate=True)
                if not image.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise LabError("Unexpected QR format; value withheld.")
                qr_path = STATE / (role + "-qr.png")
                fd = os.open(qr_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(fd, "wb") as target:
                    target.write(image)
                print(role + ": QR saved to " + str(qr_path))
                break
            if data.get("passkeyStage"):
                raise LabError(role + ": passkey flow required; stop and ask Tuan before proceeding.")
            time.sleep(1)
        else:
            raise LabError(role + ": QR not available; stop and inspect sanitized diagnostics.")


def connect_paired():
    """Resume saved lab sessions without requesting QR or creating another device."""
    instances = json.loads((STATE / "instances.json").read_text())
    key = admin_key()
    if request("/license/status").get("status") != "active":
        raise LabError("STOP: local license is not active.")
    for role, instance in instances.items():
        info = request("/instance/info/" + instance["id"], key).get("data", {})
        if not info.get("jid"):
            raise LabError(role + ": no saved pairing; ask Tuan to scan its QR.")
        state = request("/instance/status", instance["token"]).get("data", {})
        if state.get("Connected") and state.get("LoggedIn"):
            print(role + ": already authenticated; left running.")
            continue
        if state.get("Connected"):
            raise LabError(role + ": connected client is unauthenticated; stop before starting another.")
        request("/instance/connect", instance["token"], {
            "webhookUrl": "http://" + PROJECT + "-receiver:8081/webhook",
            "subscribe": ["ALL"], "rabbitmqEnable": "false", "natsEnable": "false",
            "websocketEnable": "false",
        })
        print(role + ": requested connection using saved pairing.")


def proxy_control(action="status"):
    if action not in ("status", "drop", "up"):
        raise LabError("Unsupported local proxy action.")
    if not owned("container", PROXY):
        raise LabError("Labelled local proxy is required.")
    program = ("import json,urllib.request\n"
               "opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))\n"
               "request=urllib.request.Request('http://127.0.0.1:8083/" + action + "',"
               "data=" + ("None" if action == "status" else "b''") + ")\n"
               "with opener.open(request,timeout=5) as response: print(json.dumps(json.load(response)))\n")
    result = docker("exec", PROXY, "python", "-B", "-c", program)
    return json.loads(result.stdout)


def proxy_routes(accounts):
    """Read only non-secret routing fields from the exclusively local test DB.

    Instance Info and All deliberately clear Proxy before returning it, so their
    response cannot prove either the presence or absence of configured routing.
    """
    if not owned("container", CONTAINERS[2]):
        raise LabError("Labelled temporary PostgreSQL is required for route verification.")
    role_by_id = {str(uuid.UUID(value["id"])): role for role, value in accounts.items()}
    identifiers = ",".join("'" + identifier + "'" for identifier in role_by_id)
    query = ("SELECT json_build_object('id',id,'protocol',NULLIF(proxy,'')::jsonb->>'protocol',"
             "'host',NULLIF(proxy,'')::jsonb->>'host','port',NULLIF(proxy,'')::jsonb->>'port',"
             "'has_auth',COALESCE(length(NULLIF(proxy,'')::jsonb->>'username'),0)>0 AND "
             "COALESCE(length(NULLIF(proxy,'')::jsonb->>'password'),0)>0) "
             "FROM instances WHERE id IN (" + identifiers + ");\n")
    raw = docker("exec", "-i", CONTAINERS[2], "psql", "--no-psqlrc", "-X", "-v", "ON_ERROR_STOP=1", "-U", "lab",
                 "-d", "offline_sync_instances", "-Atq", stdin=query)
    routes = {}
    for line in raw.stdout.splitlines():
        value = json.loads(line)
        role = role_by_id[value.pop("id")]
        routes[role] = value
    if set(routes) != set(accounts):
        raise LabError("Expected test instance routing records were not found.")
    return routes


def socket_setup():
    """Prepare the fault proxy, test it, then route only the target through it."""
    if request("/license/status").get("status") != "active":
        raise LabError("STOP: local license is inactive.")
    accounts = json.loads((STATE / "instances.json").read_text())
    key = admin_key()
    for instance in accounts.values():
        data = request("/instance/status", instance["token"]).get("data", {})
        if not (data.get("Connected") and data.get("LoggedIn")):
            raise LabError("Both saved test accounts must be authenticated before setup.")
    routes = proxy_routes(accounts)
    if routes["sender"]["host"]:
        raise LabError("Sender has a proxy; refusing to alter or reuse it.")
    config_path = STATE / "proxy.json"
    if config_path.exists():
        config = json.loads(config_path.read_text())
    else:
        config = {"protocol": "http", "host": PROXY, "port": "8082", "username": "lab",
                  "password": secrets.token_hex(24)}
        private_file(config_path, json.dumps(config, indent=2) + "\n")
    if not owned("container", PROXY):
        private_file(STATE / "proxy.env", "LAB_PROXY_PASSWORD=" + config["password"] + "\n")
        identity = json.loads((STATE / "identity.json").read_text())
        docker("run", "-d", "--name", PROXY, "--label", LABEL, "--read-only", "--tmpfs", "/tmp",
               "--network", "name=" + NETWORKS[0] + ",gw-priority=1",
               "--network", "name=" + NETWORKS[1] + ",gw-priority=0",
               "--env-file", str(STATE / "proxy.env"),
               "--mount", "type=bind,src=" + str(Path(__file__).with_name("fault_proxy.py")) + ",dst=/proxy.py,readonly",
               identity["images"]["python:3.12-slim"], "python", "-B", "/proxy.py")
        for _ in range(30):
            try:
                proxy_control()
                break
            except LabError:
                time.sleep(0.2)
        else:
            raise LabError("Local proxy did not become ready.")
    validated = STATE / "proxy-validated.json"
    if not validated.exists():
        smoke = docker("exec", "-i", PROXY, "python", "-B", "-",
                       stdin=Path(__file__).with_name("proxy_smoke.py").read_text())
        print(smoke.stdout.strip(), flush=True)
        private_file(validated, json.dumps({"validated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                           "smoke": "loopback EOF, held CONNECT, manual restore, 20 s watchdog"}) + "\n")
    current = routes["target"]
    matches = all(current.get(field) == config[field] for field in ("protocol", "host", "port")) and current["has_auth"]
    if current["host"] and not matches:
        raise LabError("Target has an unexpected proxy; refusing to overwrite it.")
    if not matches:
        # This route starts its own reconnect to apply settings. Do not call
        # /instance/reconnect again and do not count this preparation as a cycle.
        request("/instance/proxy/" + accounts["target"]["id"], key, config)
    for _ in range(60):
        state = request("/instance/status", accounts["target"]["token"]).get("data", {})
        stats = proxy_control()
        if stats["rejected_auth"]:
            raise LabError("Proxy authentication rejected; stop before any direct fallback.")
        if state.get("Connected") and state.get("LoggedIn") and stats["active_tunnels"] > 0:
            print("Target authenticated through local fault proxy; sender configuration unchanged.")
            print(json.dumps(stats))
            return
        time.sleep(0.5)
    raise LabError("Target did not authenticate through proxy; stop before recovery.")


def qr_page(instances=None, port=18081):
    """Show live QRs without invoking /instance/qr, which can restart paired clients."""
    if instances is None:
        instances = json.loads((STATE / "instances.json").read_text())
    key = admin_key()
    page = b'''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pareamento do laboratorio Evolution Go</title>
<style>body{font:18px system-ui;max-width:960px;margin:32px auto;padding:16px}
main{display:flex;gap:40px;flex-wrap:wrap}section{min-width:320px}img{width:320px;height:320px}
.state{min-height:2em}code{font-size:14px}</style>
<h1>Pareamento dos dois numeros de teste</h1><p>Use um numero exclusivo de teste
diferente em cada QR. WhatsApp &rarr; Dispositivos conectados &rarr; Conectar dispositivo.</p>
<main><section><h2>Receptor (target)</h2><div id="target-state" class="state"></div>
<img id="target-qr" alt="QR do receptor"></section>
<section><h2>Remetente (sender)</h2><div id="sender-state" class="state"></div>
<img id="sender-qr" alt="QR do remetente"></section></main>
<p id="error"></p><p>Os QRs se atualizam automaticamente. Deixe esta pagina aberta
ate os dois aparecerem como pareados.</p>
<script>async function update(){try{const r=await fetch('/state',{cache:'no-store'});
if(!r.ok)throw Error();const data=await r.json();for(const role of ['target','sender']){
const s=data[role],im=document.getElementById(role+'-qr');
document.getElementById(role+'-state').textContent=s.logged_in?
(s.connected?'Pareado e conectado':'Pareado; aguardando conexao'):
(s.registered?'Pareamento registrado; aguardando autenticacao':'Aguardando leitura do QR');
im.hidden=s.logged_in||s.registered||!s.qr;if(s.qr)im.src=s.qr;}
document.getElementById('error').textContent='';}catch(e){document.getElementById('error').textContent=
'Nao foi possivel consultar o laboratorio. Avise no chat.';}setTimeout(update,2000);}update();</script>
</html>'''

    class Viewer(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path == "/":
                body, content_type = page, "text/html; charset=utf-8"
            elif self.path == "/state":
                result = {}
                try:
                    for role, instance in instances.items():
                        state = request("/instance/status", instance["token"]).get("data", {})
                        paired = state.get("LoggedIn") is True
                        info = request("/instance/info/" + instance["id"], key).get("data", {})
                        registered = bool(info.get("jid"))
                        qr = ""
                        if not paired and not registered:
                            # Stored field is PNG data URI + '|' + raw pairing code.
                            qr = (info.get("qrcode") or "").split("|", 1)[0]
                            if qr and not qr.startswith("data:image/png;base64,"):
                                qr = "data:image/png;base64," + qr
                        result[role] = {"connected": state.get("Connected") is True,
                                        "logged_in": paired, "registered": registered, "qr": qr}
                except (LabError, OSError, ValueError):
                    self.send_error(503)
                    return
                body = json.dumps(result).encode()
                content_type = "application/json"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = HTTPServer(("127.0.0.1", port), Viewer)
    print("Live pairing page: http://127.0.0.1:" + str(port), flush=True)
    server.serve_forever()


def status():
    result = {"api_url": API_URL, "resources": {}}
    for name in CONTAINERS:
        if owned("container", name):
            state = docker("container", "inspect", "--format", "{{.State.Status}}", name)
            result["resources"][name] = state.stdout.strip()
        else:
            result["resources"][name] = "absent"
    if owned("container", PROXY):
        result["resources"][PROXY] = docker("container", "inspect", "--format", "{{.State.Status}}", PROXY).stdout.strip()
    if result["resources"][PROJECT + "-api"] == "running":
        try:
            # Select only the status; /license/status may also include key fragments.
            license_status = request("/license/status").get("status")
            result["license"] = license_status if license_status in ("active", "inactive") else "unknown"
        except (OSError, ValueError, urllib.error.URLError):
            result["license"] = "unavailable"
    else:
        result["license"] = "unavailable"
    if result["license"] == "active" and (STATE / "instances.json").exists():
        result["instances"] = {}
        for role, instance in json.loads((STATE / "instances.json").read_text()).items():
            data = request("/instance/status", instance["token"]).get("data", {})
            result["instances"][role] = {"connected": data.get("Connected") is True,
                                         "logged_in": data.get("LoggedIn") is True}
    print(json.dumps(result, indent=2))
    return result


def up():
    if STATE.exists():
        raise LabError("Lab state already exists. Use status; do not overwrite or reinitialize it.")
    for name in (CONTAINERS[0], PROXY, CONTAINERS[1], CONTAINERS[2]):
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
    for name in (CONTAINERS[0], PROXY, CONTAINERS[1], CONTAINERS[2]):
        if owned("container", name):
            docker("rm", "-f", "-v", name)
    for name in NETWORKS:
        if owned("network", name):
            docker("network", "rm", name)
    print("Lab containers and networks removed; local state files retained for explicit cleanup.")


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["up", "status", "pair", "connect", "qr-page", "socket-setup", "down"])
    args = parser.parse_args()
    local_docker()
    {"up": up, "status": status, "pair": pair, "connect": connect_paired,
     "qr-page": qr_page, "socket-setup": socket_setup, "down": down}[args.command]()


if __name__ == "__main__":
    try:
        main()
    except (LabError, subprocess.SubprocessError) as error:
        # Never echo arbitrary subprocess output, HTTP bodies or exception details.
        print(str(error) if isinstance(error, LabError) else "Local command failed; raw output withheld.", file=sys.stderr)
        sys.exit(1)
