"""Build the 5 variants from a config file, run them over tasks, and save one JSON trace per run."""

from __future__ import annotations

import json
import math
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from . import prompts
from .loop import Checker, DisputeChecker, Loop, NoChecker, OracleChecker, ScoreChecker, TestWriterChecker
from .models import CallBudget, FakeModel, Model, OpenAICompatModel
from .tasks import Task

VARIANTS = {
    "A": "single pass (no checker)",
    "B": "self-check: the maker scores its own code",
    "C": "cross-check: a different model scores the code",
    "D": "devil's advocate: a different model writes tests that run",
    "E": "oracle: hidden-test failures shown to the maker (upper bound)",
    "F": "devil's advocate with disputes: the maker may dispute a test, the checker rules",
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
        if system in (prompts.DISPUTE_SYSTEM, prompts.RULING_SYSTEM):
            return "{}"  # no disputes: every failing test stands
        if system == prompts.SCORE_SYSTEM:
            return '{"scores": {"correctness": 9, "edge_cases": 9, "spec_compliance": 9}, "weakest": "none"}'
        for prompt, task in by_prompt.items():
            if user == prompt:
                return f"PLAN: write the obvious solution\n```python\n{task.naive}```"
            if user.startswith(prompt):
                return f"PLAN: fix the reported failure\n```python\n{task.reference}```"
        raise RuntimeError("fake model got an unknown task")

    return Models(FakeModel(respond, name="fake-maker"), FakeModel(respond, name="fake-checker"))


def build_loop(variant: str, models: Models, max_iters: int, stop_when_unchanged: bool = False) -> Loop:
    checker: Checker
    if variant == "A":
        return Loop(models.maker, NoChecker(), max_iters=1)
    if variant == "B":
        return Loop(
            models.maker,
            ScoreChecker(models.maker),
            max_iters,
            allow_self_check=True,
            stop_when_unchanged=stop_when_unchanged,
        )
    if variant == "C":
        checker = ScoreChecker(models.checker)
    elif variant == "D":
        checker = TestWriterChecker(models.checker)
    elif variant == "E":
        checker = OracleChecker()
    elif variant == "F":
        checker = DisputeChecker(models.checker, maker=models.maker)
    else:
        raise ValueError(f"unknown variant {variant!r}; choose from {sorted(VARIANTS)}")
    return Loop(models.maker, checker, max_iters, stop_when_unchanged=stop_when_unchanged)


def run_experiment(
    tasks: list[Task],
    variants: list[str],
    models: Models,
    out_dir: Path,
    max_iters: int = 5,
    log: Callable[[str], None] = print,
    samples: int = 1,
    stop_when_unchanged: bool = False,
) -> list[Path]:
    """Run every (sample, variant, task). Existing traces are skipped, so an interrupted run resumes.

    Samples are the outer loop, so a run stopped early (say, by a daily rate limit) still covers every
    task and variant at least once, instead of every sample of only the first variants.
    """
    written = []
    for sample in range(samples):
        for variant in variants:
            loop = build_loop(variant, models, max_iters, stop_when_unchanged)
            for task in tasks:
                path = out_dir / variant / f"{task.id}__s{sample}.json"
                if path.exists():
                    continue
                trace = loop.run(task, variant=variant, sample=sample)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(trace.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
                written.append(path)
                status = "correct" if trace.final_correct else "WRONG"
                log(
                    f"[s{sample} {variant}] {task.id}: {trace.final_decision} after "
                    f"{len(trace.iterations)} iter(s), {status}"
                )
    return written


def load_traces(run_dir: Path) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(run_dir.glob("*/*.json"))]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """95% Wilson score interval for a proportion k/n. Sound for small n, unlike the normal approximation."""
    if n == 0:
        return None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)


def _checker_test_stats(ts: list[dict]) -> dict:
    """How often a test-writing checker's tests were themselves wrong (they fail the correct reference),
    and, with disputes, whether the withdrawn tests were the wrong ones."""
    total = wrong = withdrawn = withdrawn_wrong = 0
    for t in ts:
        for it in t["iterations"]:
            truth = it.get("checker_tests_truth")
            if not truth:
                continue
            bad = {f["name"] for f in truth["failures"]}
            total += truth["total"]
            wrong += len(bad)
            for name in it["checker_details"].get("withdrawn", []):
                withdrawn += 1
                withdrawn_wrong += name in bad
    if not total:
        return {}
    out: dict = {"checker_tests": total, "wrong_tests": wrong, "wrong_test_rate": round(wrong / total, 3)}
    if withdrawn:
        # A withdrawn test that passes the reference was a correct test the maker argued away.
        out |= {"withdrawn": withdrawn, "withdrawn_correct_tests": withdrawn - withdrawn_wrong}
    return out


def summarize(traces: list[dict]) -> list[dict]:
    """Per-variant headline numbers, over every (task, sample) trace.

    false_final:   the checker said FINAL, but the code fails hidden tests (a confident mistake).
    false_alarms:  iterations where the checker rejected code that already passed every hidden test.
    broke_working: the first attempt was correct but the final answer is not ("fixing" made it worse).
    *_ci:          95% Wilson intervals.
    """
    rows = []
    for variant in sorted({t["variant"] for t in traces}):
        ts = [t for t in traces if t["variant"] == variant]
        finals = [t for t in ts if t["final_decision"] == "FINAL"]
        false_finals = [t for t in finals if not t["final_correct"]]
        first_ok = [t for t in ts if t["iterations"][0]["ground_truth"]["all_passed"]]
        correct = sum(t["final_correct"] for t in ts)
        rows.append(
            {
                "variant": variant,
                "runs": len(ts),
                "tasks": len({t["task_id"] for t in ts}),
                "first_try_correct": len(first_ok),
                "final_correct": correct,
                "final_correct_rate": round(correct / len(ts), 3),
                "final_correct_ci": wilson(correct, len(ts)),
                "said_final": len(finals),
                "false_final": len(false_finals),
                "false_final_rate": round(len(false_finals) / len(finals), 3) if finals else None,
                "false_final_ci": wilson(len(false_finals), len(finals)),
                "stood_by_answer": sum(t["final_decision"] == "UNCHANGED" for t in ts),
                "false_alarms": sum(
                    it["verdict"] == "ITERATING" and it["ground_truth"]["all_passed"]
                    for t in ts
                    for it in t["iterations"]
                ),
                "broke_working": sum(not t["final_correct"] for t in first_ok),
                "avg_iterations": round(sum(len(t["iterations"]) for t in ts) / len(ts), 2),
                "model_calls": sum(
                    it["maker_usage"]["calls"] + it["checker_usage"]["calls"] for t in ts for it in t["iterations"]
                ),
                "truncated_replies": sum(
                    it["maker_usage"].get("truncated", 0) + it["checker_usage"].get("truncated", 0)
                    for t in ts
                    for it in t["iterations"]
                ),
                **_checker_test_stats(ts),
            }
        )
    return rows


def by_task(traces: list[dict], variant: str = "A") -> list[dict]:
    """Per-task first-attempt pass rate for one variant. Used to calibrate task difficulty."""
    rows = []
    for task_id in sorted({t["task_id"] for t in traces if t["variant"] == variant}):
        ts = [t for t in traces if t["variant"] == variant and t["task_id"] == task_id]
        ok = sum(t["iterations"][0]["ground_truth"]["all_passed"] for t in ts)
        rows.append(
            {"task": task_id, "room": ts[0]["room"], "samples": len(ts), "first_try_pass_rate": round(ok / len(ts), 2)}
        )
    return rows
