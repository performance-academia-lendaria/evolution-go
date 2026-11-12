"""Observe natural test-account drops and require sync plus a timely inbound probe."""

import hashlib
import time

import experiment
import lab


class RecoveryMonitor:
    def __init__(self, accounts, report, checkpoint, send_probe, delivered, seconds):
        self.accounts = accounts
        self.report = report
        self.checkpoint = checkpoint
        self.send_probe = send_probe
        self.delivered = delivered
        self.seconds = seconds
        self.started = time.time()
        self.identities = {hashlib.sha256(account["id"].encode()).hexdigest(): role
                           for role, account in accounts.items()}
        self.seen_disconnects = set()
        report["drops"] = []

    def _drop(self, role, epoch, origin):
        row = {"role": role, "disconnected_epoch": epoch, "origin": origin,
               "recovered": False, "probe": None}
        self.report["drops"].append(row)
        return row

    def _observe(self):
        signals = {role: {"Connected": [], "OfflineSyncCompleted": []} for role in self.accounts}
        for index, event in enumerate(experiment.events()):
            role = self.identities.get(event.get("instance_id_sha256"))
            epoch = event.get("received_utc", 0)
            if role is None or epoch < self.started:
                continue
            name = event.get("event")
            if name == "Disconnected" and index not in self.seen_disconnects:
                self.seen_disconnects.add(index)
                # A status sample can notice a drop before its async webhook.
                # Merge that observation rather than counting one drop twice.
                sampled = next((row for row in self.report["drops"]
                                if row["role"] == role and row["origin"] == "authentication_sample"
                                and epoch <= row.get("recovered_epoch", time.time())), None)
                if sampled is None:
                    sampled = self._drop(role, epoch, "Disconnected")
                else:
                    sampled["origin"] = "Disconnected+authentication_sample"
                    sampled["disconnected_epoch"] = min(sampled["disconnected_epoch"], epoch)
                    if sampled["recovered"]:
                        sampled["recovery_seconds"] = round(sampled["recovered_epoch"] - sampled["disconnected_epoch"], 3)
                        if sampled["recovery_seconds"] > self.seconds:
                            sampled["recovered"] = False
                            self.checkpoint()
                            raise lab.LabError("STOP: a late drop event proves recovery exceeded the recovery limit.")
            elif name in signals[role]:
                signals[role][name].append(epoch)
        states = {role: experiment.authenticated(account) for role, account in self.accounts.items()}
        self.report["authentication_samples"] += 1
        for role, authenticated in states.items():
            if not authenticated and not any(row["role"] == role and not row["recovered"]
                                             for row in self.report["drops"]):
                self._drop(role, time.time(), "authentication_sample")
        self.report["drop_counts"] = {role: sum(row["role"] == role for row in self.report["drops"])
                                      for role in self.accounts}
        self.report["recovered_drops"] = sum(row["recovered"] for row in self.report["drops"])
        self.report["last_health_utc"] = experiment.utc()
        self.checkpoint()
        return signals, states

    def check(self):
        """Return only when all observed drops have a complete recovery proof."""
        while True:
            signals, states = self._observe()
            pending = [row for row in self.report["drops"] if not row["recovered"]]
            if not pending:
                return
            for row in pending:
                since = row["disconnected_epoch"]
                deadline = since + self.seconds
                connected = next((t for t in signals[row["role"]]["Connected"] if t >= since), None)
                completed = next((t for t in signals[row["role"]]["OfflineSyncCompleted"] if t >= since), None)
                row["connected_epoch"], row["sync_completed_epoch"] = connected, completed
                if all(states.values()) and connected is not None and completed is not None:
                    if row["probe"] is None and time.time() < deadline:
                        # Bound the HTTP call by the earliest unresolved deadline.
                        remaining = min(item["disconnected_epoch"] + self.seconds for item in pending) - time.time()
                        if remaining > 0:
                            try:
                                row["probe"] = self.send_probe(row["role"], min(20, remaining))
                            except (lab.LabError, OSError):
                                # A second drop may interrupt this synthetic probe.
                                # Rescan both accounts, keeping the original deadline.
                                self.report["recovery_probe_failures"] = self.report.get("recovery_probe_failures", 0) + 1
                    event = self.delivered(row["probe"]) if row["probe"] else None
                    if event is not None:
                        recovered = max(connected, completed, event["received_utc"])
                        if recovered <= deadline:
                            row.update(recovered=True, recovered_epoch=recovered,
                                       recovery_seconds=round(recovered - since, 3))
                            row["probe"]["delivered"] = True
                self.checkpoint()
                if not row["recovered"] and time.time() >= deadline:
                    raise lab.LabError("STOP: a natural drop lacked reconnection, sync or delivery within the recovery limit.")
            if all(row["recovered"] for row in pending):
                # Scan once more: another drop may have arrived while sending probes.
                continue
            time.sleep(0.5)

    def finalize(self):
        self.check()
        self.report["drop_counts"] = {role: sum(row["role"] == role for row in self.report["drops"])
                                      for role in self.accounts}
        self.report["recovered_drops"] = sum(row["recovered"] for row in self.report["drops"])
        for role in self.accounts:
            logged = self.report[role + "_logs"]["automatic_restart"]
            if logged != self.report["drop_counts"][role]:
                raise lab.LabError("STOP: logged reconnect count differs from observed drops; recovery coverage is incomplete.")
