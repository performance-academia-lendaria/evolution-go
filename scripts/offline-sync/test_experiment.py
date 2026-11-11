"""Regression fixtures use the application's emitted log format, no real logs."""

import subprocess
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


if __name__ == "__main__":
    unittest.main()
