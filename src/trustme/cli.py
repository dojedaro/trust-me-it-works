"""Command line: validate tasks, list provider models, run experiments, summarize results."""

from __future__ import annotations

import argparse
import os
import sys
import tomllib
from pathlib import Path

from .models import list_models
from .runner import VARIANTS, fake_models, load_traces, models_from_config, run_experiment, summarize
from .sandbox import run_tests
from .tasks import load_tasks

ROOT = Path(__file__).resolve().parents[2]


def load_dotenv(path: Path) -> None:
    """Minimal .env loader (KEY=value lines), so API keys never live in the code or the shell history."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def cmd_validate(args: argparse.Namespace) -> int:
    """Criterion 1+2: every task has >=5 hidden tests, the reference passes all, the naive fails >=1."""
    tasks = load_tasks(args.tasks)
    problems = []
    for t in tasks:
        ref = run_tests(t.reference, t.hidden_test)
        naive = run_tests(t.naive, t.hidden_test)
        issues = []
        if ref.total < 5:
            issues.append(f"only {ref.total} hidden tests (need >= 5)")
        if not ref.all_passed:
            issues.append("reference fails: " + ref.summary())
        if naive.all_passed:
            issues.append("naive solution passes every test (the trap is not tested)")
        if not t.trap.strip():
            issues.append("missing trap description")
        mark = "FAIL" if issues else "ok"
        print(f"{mark:4} {t.room}/{t.id}: reference {ref.passed}/{ref.total}, naive {naive.passed}/{naive.total}")
        problems += [f"  {t.id}: {i}" for i in issues]
    rooms = sorted({t.room for t in tasks})
    print(f"\n{len(tasks)} tasks in {len(rooms)} rooms: {', '.join(rooms)}")
    if problems:
        print("\n".join(problems))
        return 1
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    cfg = tomllib.loads(args.config.read_text(encoding="utf-8"))
    p = cfg["providers"][args.provider]
    for model_id in list_models(p["base_url"], p["api_key_env"]):
        print(model_id)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    tasks = load_tasks(args.tasks, only=args.only.split(",") if args.only else None)
    if not tasks:
        print("no tasks matched", file=sys.stderr)
        return 1
    if args.fake:
        models, max_iters = fake_models(tasks), args.max_iters or 5
    else:
        models, run_cfg = models_from_config(args.config)
        max_iters = args.max_iters or run_cfg["max_iters"]
    variants = args.variants.split(",")
    out = args.out / args.name
    print(f"Running {len(variants)} variant(s) x {len(tasks)} task(s) -> {out}")
    run_experiment(tasks, variants, models, out, max_iters=max_iters)
    print_summary(out)
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    print_summary(args.run_dir)
    return 0


def print_summary(run_dir: Path) -> None:
    rows = summarize(load_traces(run_dir))
    if not rows:
        print("no traces found")
        return
    cols = list(rows[0])
    widths = {c: max(len(c), *(len(str(r[c])) for r in rows)) for c in cols}
    print("\n" + "  ".join(c.ljust(widths[c]) for c in cols))
    for r in rows:
        print("  ".join(str(r[c]).ljust(widths[c]) for c in cols))


def main(argv: list[str] | None = None) -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(prog="trustme", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="check every task is fair (reference passes, naive fails)")
    p.add_argument("--tasks", type=Path, default=ROOT / "tasks")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("models", help="list model IDs a provider offers")
    p.add_argument("--config", type=Path, default=ROOT / "configs" / "free.toml")
    p.add_argument("--provider", default="groq")
    p.set_defaults(func=cmd_models)

    p = sub.add_parser("run", help="run variants over tasks and save traces")
    p.add_argument("--config", type=Path, default=ROOT / "configs" / "free.toml")
    p.add_argument("--tasks", type=Path, default=ROOT / "tasks")
    p.add_argument("--variants", default="A,B,C,D,E", help="comma-separated, from: " + ", ".join(VARIANTS))
    p.add_argument("--only", help="comma-separated task ids or room names")
    p.add_argument("--name", default="dev", help="run name (subfolder of --out)")
    p.add_argument("--out", type=Path, default=ROOT / "runs")
    p.add_argument("--max-iters", type=int)
    p.add_argument("--fake", action="store_true", help="use scripted fake models (no API, no cost)")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("summarize", help="print headline numbers for a run")
    p.add_argument("run_dir", type=Path)
    p.set_defaults(func=cmd_summarize)

    args = parser.parse_args(argv)
    return args.func(args)
