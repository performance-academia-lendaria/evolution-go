"""Regression fixtures use the application's emitted log format, no real logs."""

import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import experiment


class CompletionCounterTest(unittest.TestCase):
    def test_counts_handled_completion_and_ignores_other_instance(self):
        raw = "\n".join([
            "[target] Unhandled event *events.OfflineSyncPreview: &{Total:1}",
            "[target] ===== DISPATCHING WEBHOOK ===== Event: OfflineSyncCompleted, Queue: target.offlinesynccompleted, DataSize: 100 bytes",
            "[sender] ===== DISPATCHING WEBHOOK ===== Event: OfflineSyncCompleted, Queue: sender.offlinesynccompleted, DataSize: 100 bytes",
        ])
        with patch.object(experiment.lab, "docker", return_value=subprocess.CompletedProcess([], 0, raw, "")):
            counts = experiment.log_counts({"id": "target"}, "2026-11-11T00:00:00Z")
        self.assertEqual(counts["offline_preview"], 1)
        self.assertEqual(counts["offline_completed"], 1)

    def test_unobserved_outage_cannot_be_classified_as_reproduction(self):
        accounts = {role: {"id": role, "token": "test-only"} for role in ("target", "sender")}
        args = SimpleNamespace(label="before", method="api", cycles=1, down_seconds=10, recovery_seconds=1)
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(experiment.lab, "STATE", Path(directory)), \
                patch.object(experiment.lab, "ROOT", Path(directory)), \
                patch.object(experiment, "instances", return_value=accounts), \
                patch.object(experiment.lab, "owned", return_value=True), \
                patch.object(experiment.lab, "request", return_value={"status": "active"}), \
                patch.object(experiment.lab, "docker", return_value=subprocess.CompletedProcess([], 0, "test-image", "")), \
                patch.object(experiment.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "test-revision", "")), \
                patch.object(experiment, "authenticated", return_value=True), \
                patch.object(experiment, "send", return_value={"accepted": True}), \
                patch.object(experiment, "wait_for", side_effect=[True, True, False, True]), \
                patch.object(experiment, "received", side_effect=lambda account, marker: marker.endswith("outbound")), \
                patch.object(experiment, "log_counts", return_value={"offline_preview": 1, "offline_completed": 0}), \
                patch.object(experiment, "checkpoint"), \
                patch.object(experiment.time, "monotonic", side_effect=[0, 0, 2]), \
                patch.object(experiment.time, "sleep"):
            with self.assertRaisesRegex(experiment.lab.LabError, "could not confirm"):
                experiment.run(args)


if __name__ == "__main__":
    unittest.main()
