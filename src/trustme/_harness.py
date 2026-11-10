"""Runs inside the sandbox subprocess. Copied into the temp dir; never imported by the package.

Usage: python -I _harness.py <nonce> <test_module>
Installs best-effort guards, imports the test module, runs every test_* function, and prints
the results as JSON after a random nonce so stray prints from the code under test are ignored.
"""

import builtins
import io
import json
import os
import socket
import subprocess
import sys
import traceback

ROOT = os.path.realpath(os.getcwd())
sys.path.insert(0, ROOT)
NONCE = sys.argv[1]
TEST_MODULE = sys.argv[2]


def _blocked(*args, **kwargs):
    raise PermissionError("blocked by sandbox")


# Network: no sockets, no DNS.
socket.socket.connect = _blocked
socket.socket.connect_ex = _blocked
socket.create_connection = _blocked
socket.getaddrinfo = _blocked

# Processes: no shelling out.
subprocess.Popen = _blocked
os.system = _blocked
for _name in ("fork", "execv", "execve", "spawnv", "spawnve", "startfile", "popen"):
    if hasattr(os, _name):
        setattr(os, _name, _blocked)


# Files: writes and deletes only inside the sandbox directory.
def _inside(path):
    full = os.path.realpath(os.path.join(ROOT, os.fspath(path)))
    return full == ROOT or full.startswith(ROOT + os.sep)


_real_open = builtins.open


def _guarded_open(file, mode="r", *args, **kwargs):
    if isinstance(file, int) or not any(c in mode for c in "wax+") or _inside(file):
        return _real_open(file, mode, *args, **kwargs)
    raise PermissionError(f"sandbox: write outside sandbox dir blocked: {file}")


builtins.open = _guarded_open
io.open = _guarded_open


def _guard_path_fn(real):
    def guarded(path, *a, **k):
        if not _inside(path):
            raise PermissionError(f"sandbox: {real.__name__} outside sandbox dir blocked")
        return real(path, *a, **k)

    return guarded


for _name in ("remove", "unlink", "rmdir", "rename", "replace", "mkdir", "makedirs"):
    setattr(os, _name, _guard_path_fn(getattr(os, _name)))

results = []
collection_error = None
try:
    module = __import__(TEST_MODULE)
except BaseException:  # noqa: BLE001 - untrusted code can raise anything at import time
    collection_error = traceback.format_exc(limit=3)[-2000:]
else:
    for name in sorted(n for n in dir(module) if n.startswith("test_")):
        fn = getattr(module, name)
        if not callable(fn):
            continue
        try:
            fn()
            results.append({"name": name, "passed": True, "message": ""})
        except BaseException as e:  # noqa: BLE001 - untrusted code can raise anything
            msg = f"{type(e).__name__}: {e}" if str(e) else type(e).__name__
            results.append({"name": name, "passed": False, "message": msg[:1000]})

sys.stdout.write("\n" + NONCE + json.dumps({"results": results, "collection_error": collection_error}) + "\n")
sys.stdout.flush()
