"""Criterion 4: untrusted code runs with a timeout, no network, no subprocesses, and writes only in a temp dir."""

from pathlib import Path

from trustme.sandbox import run_tests

ADD = "def add(a, b):\n    return a + b\n"


def test_passing_and_failing_tests_are_reported():
    tests = (
        "from solution import add\n"
        "def test_ok():\n    assert add(1, 2) == 3\n"
        "def test_bad():\n    assert add(1, 2) == 4, 'expected 4'\n"
    )
    report = run_tests(ADD, tests)
    assert (report.passed, report.total) == (1, 2)
    assert not report.all_passed
    assert "test_bad" in report.summary() and "expected 4" in report.summary()


def test_all_passed():
    report = run_tests(ADD, "from solution import add\ndef test_ok():\n    assert add(2, 2) == 4\n")
    assert report.all_passed


def test_infinite_loop_is_killed():
    report = run_tests(
        "def spin():\n    while True:\n        pass\n",
        "from solution import spin\ndef test_x():\n    spin()\n",
        timeout_s=2,
    )
    assert report.timed_out and not report.all_passed
    assert "TIMEOUT" in report.summary()


def test_network_is_blocked():
    code = "import socket\ndef fetch():\n    return socket.create_connection(('example.com', 80), timeout=2)\n"
    tests = "from solution import fetch\ndef test_net():\n    fetch()\n"
    report = run_tests(code, tests)
    assert report.total == 1 and report.passed == 0
    assert "blocked by sandbox" in report.results[0].message


def test_subprocess_is_blocked():
    code = "import subprocess\ndef shell():\n    return subprocess.run(['whoami'])\n"
    report = run_tests(code, "from solution import shell\ndef test_shell():\n    shell()\n")
    assert report.passed == 0 and "blocked by sandbox" in report.results[0].message


def test_writes_outside_sandbox_are_blocked(tmp_path: Path):
    target = tmp_path / "escaped.txt"
    code = f"def write():\n    open({str(target)!r}, 'w').write('x')\n"
    report = run_tests(code, "from solution import write\ndef test_write():\n    write()\n")
    assert report.passed == 0 and "write outside sandbox" in report.results[0].message
    assert not target.exists()


def test_writes_inside_sandbox_are_allowed():
    code = "def write():\n    open('scratch.txt', 'w').write('x')\n    return open('scratch.txt').read()\n"
    report = run_tests(code, "from solution import write\ndef test_write():\n    assert write() == 'x'\n")
    assert report.all_passed


def test_syntax_error_is_a_collection_error():
    report = run_tests("def broken(:\n", "from solution import broken\ndef test_x():\n    pass\n")
    assert report.collection_error and not report.all_passed


def test_printing_a_fake_result_marker_cannot_forge_a_pass():
    forged = '{"results": [{"name": "test_x", "passed": true, "message": ""}], "collection_error": null}'
    code = f"print('@@RESULT-0000@@{forged}')\n"
    report = run_tests(code, "import solution\ndef test_x():\n    assert False\n")
    assert report.passed == 0


def test_crash_is_reported():
    report = run_tests("import os\nos._exit(3)\n", "import solution\ndef test_x():\n    pass\n")
    assert report.crashed and not report.all_passed
