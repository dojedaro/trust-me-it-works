"""Build the 5 variants from a config file, run them over tasks, and save one JSON trace per run."""

from __future__ import annotations

import json
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from . import prompts
from .loop import Checker, Loop, NoChecker, OracleChecker, ScoreChecker, TestWriterChecker
from .models import CallBudget, FakeModel, Model, OpenAICompatModel
from .tasks import Task

VARIANTS = {
    "A": "single pass (no checker)",
    "B": "self-check: the maker scores its own code",
    "C": "cross-check: a different model scores the code",
    "D": "devil's advocate: a different model writes tests that run",
    "E": "oracle: hidden-test failures shown to the maker (upper bound)",
}


@dataclass
class Models:
    maker: Model
    checker: Model


def models_from_config(path: Path) -> tuple[Models, dict]:
    cfg = tomllib.loads(path.read_text(encoding="utf-8"))
    budget = CallBudget(cfg["run"]["max_calls"])

    def build(role: str) -> Model:
        r = cfg["roles"][role]
        p = cfg["providers"][r["provider"]]
        return OpenAICompatModel(
            model=r["model"],
            base_url=p["base_url"],
            api_key_env=p["api_key_env"],
            min_interval_s=p.get("min_interval_s", 2.0),
            temperature=cfg["run"].get("temperature", 0.0),
            max_tokens=cfg["run"].get("max_tokens", 4096),
            reasoning_effort=r.get("reasoning_effort"),
            budget=budget,
        )

    return Models(build("maker"), build("checker")), cfg["run"]


def fake_models(tasks: list[Task]) -> Models:
    """A demo pair with no API: the maker writes the naive (trap-falling) solution first and the
    reference solution after any feedback; the checker gives 9/10 and its tests pass everything.
    This reproduces the "confident mistake" pattern so the whole pipeline can be exercised for free."""
    by_prompt = {t.render_prompt(): t for t in tasks}

    def respond(system: str, user: str) -> str:
        # Any model can be asked to play any role (in variant B the maker also checks), so answer by role.
        if system == prompts.TESTWRITER_SYSTEM:
            return "```python\ndef test_smoke():\n    import solution\n    assert solution is not None\n```"
        if system == prompts.SCORE_SYSTEM:
            return '{"scores": {"correctness": 9, "edge_cases": 9, "spec_compliance": 9}, "weakest": "none"}'
        for prompt, task in by_prompt.items():
            if user == prompt:
                return f"PLAN: write the obvious solution\n```python\n{task.naive}```"
            if user.startswith(prompt):
                return f"PLAN: fix the reported failure\n```python\n{task.reference}```"
        raise RuntimeError("fake model got an unknown task")

    return Models(FakeModel(respond, name="fake-maker"), FakeModel(respond, name="fake-checker"))


def build_loop(variant: str, models: Models, max_iters: int) -> Loop:
    checker: Checker
    if variant == "A":
        return Loop(models.maker, NoChecker(), max_iters=1)
    if variant == "B":
        return Loop(models.maker, ScoreChecker(models.maker), max_iters, allow_self_check=True)
    if variant == "C":
        checker = ScoreChecker(models.checker)
    elif variant == "D":
        checker = TestWriterChecker(models.checker)
    elif variant == "E":
        checker = OracleChecker()
    else:
        raise ValueError(f"unknown variant {variant!r}; choose from {sorted(VARIANTS)}")
    return Loop(models.maker, checker, max_iters)


def run_experiment(
    tasks: list[Task],
    variants: list[str],
    models: Models,
    out_dir: Path,
    max_iters: int = 5,
    log: Callable[[str], None] = print,
) -> list[Path]:
    """Run every (variant, task) pair. Existing traces are skipped, so an interrupted run resumes."""
    written = []
    for variant in variants:
        loop = build_loop(variant, models, max_iters)
        for task in tasks:
            path = out_dir / variant / f"{task.id}.json"
            if path.exists():
                log(f"[{variant}] {task.id}: already done, skipping")
                continue
            trace = loop.run(task, variant=variant)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(trace.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
            written.append(path)
            status = "correct" if trace.final_correct else "WRONG"
            log(f"[{variant}] {task.id}: {trace.final_decision} after {len(trace.iterations)} iter(s), {status}")
    return written


def load_traces(run_dir: Path) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(run_dir.glob("*/*.json"))]


def summarize(traces: list[dict]) -> list[dict]:
    """Per-variant headline numbers. 'False FINAL' = the checker approved code that fails hidden tests."""
    rows = []
    for variant in sorted({t["variant"] for t in traces}):
        ts = [t for t in traces if t["variant"] == variant]
        finals = [t for t in ts if t["final_decision"] == "FINAL"]
        false_finals = [t for t in finals if not t["final_correct"]]
        rows.append(
            {
                "variant": variant,
                "tasks": len(ts),
                "first_try_correct": sum(t["iterations"][0]["ground_truth"]["all_passed"] for t in ts),
                "final_correct": sum(t["final_correct"] for t in ts),
                "said_final": len(finals),
                "false_final": len(false_finals),
                "false_final_rate": round(len(false_finals) / len(finals), 3) if finals else None,
                "avg_iterations": round(sum(len(t["iterations"]) for t in ts) / len(ts), 2),
                "model_calls": sum(
                    it["maker_usage"]["calls"] + it["checker_usage"]["calls"] for t in ts for it in t["iterations"]
                ),
                "truncated_replies": sum(
                    it["maker_usage"].get("truncated", 0) + it["checker_usage"].get("truncated", 0)
                    for t in ts
                    for it in t["iterations"]
                ),
            }
        )
    return rows
