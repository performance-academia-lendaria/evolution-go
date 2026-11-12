"""Exercise pool probes against the actual webhook marker allowlist."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pool_connections as pools
import receiver


class PoolProbeContractTest(unittest.TestCase):
    def test_warmup_and_cycle_probes_match_receiver_allowlist(self):
        accounts = {role: {"id": role, "token": "test-only"} for role in ("target", "sender")}
        delivered = set()

        def send(source, destination, marker):
            # The real receiver discards unrecognized text, even if delivered.
            if receiver.MARKER.fullmatch(marker):
                delivered.add((destination["id"], marker))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs" / "investigations").mkdir(parents=True)
            with patch.object(pools.lab, "ROOT", root), patch.object(pools.lab, "STATE", root), \
                    patch.object(pools.lab, "owned", return_value=True), \
                    patch.object(pools.lab, "request", return_value={"status": "active"}), \
                    patch.object(pools.lab, "docker", return_value=subprocess.CompletedProcess([], 0, "image-id", "")), \
                    patch.object(pools.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "revision", "")), \
                    patch.object(pools.experiment, "instances", return_value=accounts), \
                    patch.object(pools.experiment, "authenticated", return_value=True), \
                    patch.object(pools.experiment, "send", side_effect=send), \
                    patch.object(pools.experiment, "received", side_effect=lambda account, marker: (account["id"], marker) in delivered), \
                    patch.object(pools.experiment, "wait_for", side_effect=lambda predicate, *args: bool(predicate())), \
                    patch.object(pools.experiment, "log_counts", return_value={"connected": 1, "offline_completed": 1, "automatic_restart": 0}), \
                    patch.object(pools, "connections", return_value={"total": 3, "active": 0, "idle": 3}), \
                    patch.object(pools.time, "sleep"), redirect_stdout(io.StringIO()):
                pools.run(SimpleNamespace(label="after", cycles=20, expect_stable=True))
        self.assertEqual(len(delivered), 22)


if __name__ == "__main__":
    unittest.main()
