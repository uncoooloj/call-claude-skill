#!/usr/bin/env python3
"""Tests for call_claude.py CLI resolution and invocation."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from typing import List


SCRIPT = Path(__file__).with_name("call_claude.py")


def write_fake_claude(directory: Path, body: str) -> Path:
    path = directory / "claude"
    path.write_text(f"#!{sys.executable}\n" + textwrap.dedent(body), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


class CallClaudeTests(unittest.TestCase):
    def run_helper(self, args: List[str], path_dirs: List[Path]) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["PATH"] = os.pathsep.join(str(path) for path in path_dirs)
        env["CALL_CLAUDE_DISABLE_KNOWN_PATHS"] = "1"
        for key in ("CLAUDE_BIN", "CLAUDE_PATH", "CMUX_CUSTOM_CLAUDE_PATH"):
            env.pop(key, None)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def test_invokes_first_valid_claude(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp)
            write_fake_claude(
                good,
                """
                import sys
                if "--version" in sys.argv:
                    print("2.0.0 (Claude Code)")
                else:
                    print("ok")
                """,
            )
            result = self.run_helper(["--prompt", "hello"], [good])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "ok")

    def test_skips_broken_wrapper_and_uses_next_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as broken_tmp, tempfile.TemporaryDirectory() as good_tmp:
            broken = Path(broken_tmp)
            good = Path(good_tmp)
            write_fake_claude(
                broken,
                """
                import sys
                print("Error: claude not found in PATH", file=sys.stderr)
                sys.exit(127)
                """,
            )
            write_fake_claude(
                good,
                """
                import sys
                if "--version" in sys.argv:
                    print("2.0.0 (Claude Code)")
                else:
                    print("ok")
                """,
            )
            result = self.run_helper(["--prompt", "hello"], [broken, good])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "ok")

    def test_reports_no_usable_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp)
            result = self.run_helper(["--prompt", "hello"], [empty])
            self.assertEqual(result.returncode, 127)
            self.assertIn("No usable Claude CLI", result.stderr)

    def test_diagnose_prints_selected_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp)
            candidate = write_fake_claude(
                good,
                """
                import sys
                if "--version" in sys.argv:
                    print("2.0.0 (Claude Code)")
                else:
                    print("ok")
                """,
            )
            result = self.run_helper(["--diagnose"], [good])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), str(candidate))
            self.assertIn("OK", result.stderr)

    def test_timeout_surfaces_home_write_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp)
            write_fake_claude(
                good,
                """
                import sys
                import time
                if "--version" in sys.argv:
                    print("2.0.0 (Claude Code)")
                else:
                    print("Error: EPERM: operation not permitted, open '/Users/example/.claude.json'", file=sys.stderr, flush=True)
                    time.sleep(5)
                """,
            )
            result = self.run_helper(["--prompt", "hello", "--timeout", "1"], [good])
            self.assertEqual(result.returncode, 124)
            self.assertIn("Hint: Claude tried to write", result.stderr)


if __name__ == "__main__":
    unittest.main()
