"""Run untrusted, model-written code against tests in an isolated subprocess.

Isolation is best-effort (no Docker on the dev machine): a fresh temp directory, `python -I`,
a minimal environment, a hard timeout, an output cap, and in-process guards (see _harness.py)
that block sockets, subprocesses, and file writes outside the temp directory.

This is fine for our own controlled experiments. It is NOT a security boundary against
deliberately hostile code (e.g. ctypes can bypass the guards). Phase 2 moves this into Docker.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_TIMEOUT_S = 10.0
MAX_OUTPUT_BYTES = 200_000
_HARNESS_PATH = Path(__file__).with_name("_harness.py")


@dataclass
class TestResult:
    name: str
    passed: bool
    message: str = ""


@dataclass
class TestReport:
    results: list[TestResult] = field(default_factory=list)
    collection_error: str | None = None
    timed_out: bool = False
    crashed: bool = False
    stderr: str = ""

    @property
    def passed(self) -> int:
        return sum(r.passed for r in self.results)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def all_passed(self) -> bool:
        return self.total > 0 and self.passed == self.total and not (self.timed_out or self.crashed)

    def summary(self, max_failures: int = 5) -> str:
        """Human-readable feedback, e.g. to show a model which tests failed."""
        if self.timed_out:
            return "TIMEOUT: the code did not finish within the time limit (infinite loop?)."
        if self.collection_error:
            return "ERROR while importing the code or tests:\n" + self.collection_error
        if self.crashed:
            return "CRASH: the test process died.\n" + self.stderr[-1500:]
        if self.total == 0:
            return "No test_* functions were found."
        lines = [f"{self.passed}/{self.total} tests passed."]
        lines += [f"- {r.name}: {r.message}" for r in self.results if not r.passed][:max_failures]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "total": self.total,
            "all_passed": self.all_passed,
            "timed_out": self.timed_out,
            "crashed": self.crashed,
            "collection_error": self.collection_error,
            "failures": [{"name": r.name, "message": r.message} for r in self.results if not r.passed],
        }


def run_tests(solution_code: str, test_code: str, timeout_s: float = DEFAULT_TIMEOUT_S) -> TestReport:
    """Write `solution.py` and a test module to a fresh temp dir and run every `test_*` function."""
    nonce = "@@RESULT-" + secrets.token_hex(8) + "@@"
    env = {"PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
    if "SYSTEMROOT" in os.environ:  # Windows needs it for Python's startup
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    with tempfile.TemporaryDirectory(prefix="trustme-", ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        (root / "solution.py").write_text(solution_code, encoding="utf-8")
        (root / "test_cases.py").write_text(test_code, encoding="utf-8")
        shutil.copy(_HARNESS_PATH, root / "_harness.py")
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "_harness.py", nonce, "test_cases"],
                cwd=root,
                capture_output=True,
                timeout=timeout_s,
                stdin=subprocess.DEVNULL,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return TestReport(timed_out=True)
    stdout = proc.stdout[-MAX_OUTPUT_BYTES:].decode("utf-8", "replace")
    stderr = proc.stderr[-MAX_OUTPUT_BYTES:].decode("utf-8", "replace")
    marker = stdout.rfind(nonce)
    if marker == -1:
        return TestReport(crashed=True, stderr=stderr)
    payload = json.loads(stdout[marker + len(nonce) :].splitlines()[0])
    return TestReport(
        results=[TestResult(**r) for r in payload["results"]],
        collection_error=payload["collection_error"],
        stderr=stderr,
    )
