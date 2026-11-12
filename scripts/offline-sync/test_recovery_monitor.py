"""Recovery decisions use event timestamps and real delivery evidence, not sleeps."""

from contextlib import ExitStack
import hashlib
import subprocess
import unittest
from unittest.mock import patch

import lab
from recovery_monitor import RecoveryMonitor, lifecycle_events


class Clock:
    now = 10.0

    def sleep(self, seconds):
        self.now += seconds


class RecoveryTest(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.accounts = {role: {"id": role} for role in ("target", "sender")}
        self.report = {"authentication_samples": 0, "started_utc": "start"}
        self.timeline = []
        self.online_at = {"target": 13, "sender": 0}
        self.allow_delivery = True
        self.probes = []
        self.logged = {"target": 0, "sender": 0}
        self.log_windows = []
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch("recovery_monitor.time.time", side_effect=lambda: self.clock.now))
        self.stack.enter_context(patch("recovery_monitor.time.sleep", side_effect=self.clock.sleep))
        self.stack.enter_context(patch("recovery_monitor.experiment.events", side_effect=lambda: [
            event for available, event in self.timeline if available <= self.clock.now
            and event["event"] != "OfflineSyncCompleted"]))
        self.stack.enter_context(patch("recovery_monitor.lifecycle_events", side_effect=lambda *args: [
            (role, event["event"], event.get("log_epoch", event["received_utc"])) for available, event in self.timeline
            for role in self.accounts if available <= self.clock.now
            and event["instance_id_sha256"] == hashlib.sha256(role.encode()).hexdigest()]))
        self.stack.enter_context(patch("recovery_monitor.experiment.authenticated", side_effect=lambda account:
                                      self.clock.now >= self.online_at[account["id"]]))
        def counts(account, start, until=None):
            self.log_windows.append(until)
            return {"automatic_restart": self.logged[account["id"]]}
        self.stack.enter_context(patch("recovery_monitor.experiment.log_counts", side_effect=counts))
        self.monitor = RecoveryMonitor(self.accounts, self.report, lambda: None,
                                       self.send_probe, self.delivered, 60)

    def event(self, role, name, epoch, available=None, log_epoch=None):
        self.timeline.append((epoch if available is None else available, {
            "instance_id_sha256": hashlib.sha256(role.encode()).hexdigest(),
            "event": name, "received_utc": epoch,
            **({"log_epoch": log_epoch} if log_epoch is not None else {})}))

    def healthy_recovery(self, role="target", down=11, up=13, complete=14):
        self.event(role, "Disconnected", down)
        self.event(role, "Connected", up)
        self.event(role, "OfflineSyncCompleted", complete)

    def send_probe(self, role, timeout):
        self.assertGreater(timeout, 0)
        self.assertLessEqual(timeout, 20)
        row = {"role": role, "received_at": self.clock.now + 0.5, "delivered": False}
        self.probes.append(row)
        return row

    def delivered(self, row):
        if self.allow_delivery and self.clock.now >= row["received_at"]:
            return {"received_utc": row["received_at"]}
        return None

    def test_waits_for_sync_and_inbound_delivery_after_authentication_loss(self):
        self.healthy_recovery()
        self.clock.now = 11
        self.monitor.check()
        self.assertEqual(len(self.report["drops"]), 1)
        drop = self.report["drops"][0]
        self.assertTrue(drop["recovered"])
        self.assertEqual(drop["recovery_seconds"], 3.5)

    def test_counts_brief_drop_recovered_between_authentication_samples(self):
        self.healthy_recovery()
        self.clock.now = 15
        self.monitor.check()
        self.assertEqual(len(self.report["drops"]), 1)
        self.assertTrue(self.report["drops"][0]["recovered"])

    def test_missing_sync_fails_within_sixty_seconds(self):
        self.event("target", "Disconnected", 11)
        self.event("target", "Connected", 13)
        self.clock.now = 11
        with self.assertRaisesRegex(lab.LabError, "recovery limit"):
            self.monitor.check()
        self.assertEqual(self.clock.now, 71)
        self.assertEqual(self.probes, [])

    def test_authenticated_and_synced_without_delivery_fails(self):
        self.healthy_recovery()
        self.allow_delivery = False
        self.clock.now = 11
        with self.assertRaisesRegex(lab.LabError, "recovery limit"):
            self.monitor.check()
        self.assertFalse(self.report["drops"][0]["recovered"])

    def test_both_devices_require_their_own_inbound_probe(self):
        self.healthy_recovery()
        self.healthy_recovery("sender", down=12, up=13, complete=15)
        self.online_at["sender"] = 13
        self.clock.now = 11
        self.monitor.check()
        self.assertEqual({row["role"] for row in self.probes}, {"target", "sender"})
        self.assertTrue(all(row["recovered"] for row in self.report["drops"]))

    def test_late_disconnect_webhook_merges_with_status_sample(self):
        self.event("target", "Disconnected", 11, available=14)
        self.event("target", "Connected", 13)
        self.event("target", "OfflineSyncCompleted", 15)
        self.clock.now = 12
        self.monitor.check()
        self.assertEqual(len(self.report["drops"]), 1)
        self.assertEqual(self.report["drops"][0]["disconnected_epoch"], 11)

    def test_disconnect_receipt_after_recovery_does_not_count_another_drop(self):
        self.event("target", "Connected", 13)
        self.event("target", "OfflineSyncCompleted", 14)
        self.clock.now = 12
        self.monitor.check()
        self.event("target", "Disconnected", 15, log_epoch=12)
        self.clock.now = 15
        self.monitor.check()
        self.assertEqual(len(self.report["drops"]), 1)

    def test_restart_log_without_observed_drop_cannot_pass(self):
        self.online_at["target"] = 0
        self.logged["target"] = 1
        self.report.update(target_logs={"automatic_restart": 1}, sender_logs={"automatic_restart": 0})
        with self.assertRaisesRegex(lab.LabError, "coverage is incomplete"):
            self.monitor.finalize()

    def test_final_counters_include_recovery_observed_during_finalization(self):
        self.healthy_recovery()
        self.clock.now = 11
        self.logged["target"] = 1
        self.report.update(target_logs={"automatic_restart": 0}, sender_logs={"automatic_restart": 0})
        self.monitor.finalize()
        self.assertEqual(self.report["drop_counts"]["target"], 1)
        self.assertEqual(self.report["target_logs"]["automatic_restart"], 1)
        self.assertEqual(len(set(self.log_windows)), 1)
        self.assertIsNotNone(self.log_windows[0])
        self.assertEqual(self.log_windows, [self.report["observed_until_utc"]] * 2)

    def test_late_event_cannot_hide_a_recovery_exceeding_sixty_seconds(self):
        self.online_at["target"] = 71
        self.event("target", "Connected", 71)
        self.event("target", "OfflineSyncCompleted", 72)
        self.clock.now = 70
        self.monitor.check()
        self.event("target", "Disconnected", 11, available=73)
        self.clock.now = 73
        with self.assertRaisesRegex(lab.LabError, "recovery limit"):
            self.monitor.check()


class CompletionLogTest(unittest.TestCase):
    def test_reads_handled_completion_timestamp_and_filters_other_instances(self):
        lines = "\n".join([
            "2026-11-12T01:00:00.123456789Z [target-device] ===== DISPATCHING WEBHOOK ===== Event: OfflineSyncCompleted, Queue: example",
            "2026-11-12T01:00:01.000000000Z [unrelated-device] Event: OfflineSyncCompleted, Queue: example",
            "2026-11-12T01:00:02.000000000Z [sender-device] Unhandled event *events.OfflineSyncPreview: &{Total:1}",
        ])
        with patch("recovery_monitor.lab.docker", return_value=subprocess.CompletedProcess([], 0, lines, "")) as docker:
            rows = lifecycle_events({"target": {"id": "target-device"}, "sender": {"id": "sender-device"}}, "start", "end")
        self.assertIn("--until", docker.call_args.args)
        self.assertEqual(docker.call_args.args[docker.call_args.args.index("--until") + 1], "end")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "target")
        self.assertEqual(rows[0][1], "OfflineSyncCompleted")
        self.assertAlmostEqual(rows[0][2] % 1, 0.123456, places=6)


if __name__ == "__main__":
    unittest.main()
