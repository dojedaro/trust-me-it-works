"""Criteria 1-2 (fair tasks) and the runner's resume + summary behaviour."""

from pathlib import Path

import pytest

from trustme.runner import by_task, fake_models, load_traces, run_experiment, summarize, wilson
from trustme.sandbox import run_tests
from trustme.tasks import load_tasks

TASKS = load_tasks(Path(__file__).parents[1] / "tasks")


def test_every_room_has_tasks():
    assert len(TASKS) >= 12
    assert {t.room for t in TASKS} == {"korea", "time", "games", "money", "text", "spec"}


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.id)
def test_task_is_fair(task):
    ref = run_tests(task.reference, task.hidden_test)
    naive = run_tests(task.naive, task.hidden_test)
    assert ref.total >= 5, "each task needs at least 5 hidden tests"
    assert ref.all_passed, ref.summary()
    assert not naive.all_passed, "the naive solution must fall into the trap"
    assert task.trap.strip()
    assert "hidden" not in task.render_prompt().lower()


def test_fake_experiment_resumes_and_summarizes(tmp_path: Path):
    tasks = TASKS[:2]
    logs: list[str] = []
    written = run_experiment(tasks, ["A", "E"], fake_models(tasks), tmp_path, log=logs.append, samples=2)
    assert len(written) == 8
    assert (tmp_path / "A" / f"{tasks[0].id}__s1.json").exists()
    assert run_experiment(tasks, ["A", "E"], fake_models(tasks), tmp_path, log=logs.append, samples=2) == []

    rows = {r["variant"]: r for r in summarize(load_traces(tmp_path))}
    assert rows["A"]["runs"] == 4 and rows["A"]["tasks"] == 2
    assert rows["A"]["false_final"] == 4 and rows["A"]["false_final_rate"] == 1.0
    assert rows["E"]["final_correct"] == 4 and rows["E"]["false_final"] == 0
    assert [r["first_try_pass_rate"] for r in by_task(load_traces(tmp_path), "A")] == [0.0, 0.0]


def _it(verdict: str, correct: bool) -> dict:
    usage = {"calls": 1, "truncated": 0}
    return {"verdict": verdict, "ground_truth": {"all_passed": correct}, "maker_usage": usage, "checker_usage": usage}


def test_false_alarm_and_broke_working_metrics():
    trace = {
        "task_id": "t",
        "variant": "D",
        "final_decision": "FINAL",
        "final_correct": False,
        # correct first try, checker rejects it anyway (false alarm), maker "fixes" it into a bug,
        # then the checker approves the broken code (false FINAL)
        "iterations": [_it("ITERATING", True), _it("FINAL", False)],
    }
    (row,) = summarize([trace])
    assert row["false_alarms"] == 1
    assert row["broke_working"] == 1
    assert row["false_final"] == 1


def test_wilson_interval():
    assert wilson(0, 0) is None
    lo, hi = wilson(0, 10)
    assert lo == 0.0 and 0.25 < hi < 0.35  # 0/10 still leaves up to ~31% plausible
    lo, hi = wilson(5, 10)
    assert lo < 0.5 < hi


def test_fake_run_of_every_variant(tmp_path: Path):
    tasks = TASKS[:1]
    run_experiment(tasks, list("ABCDEF"), fake_models(tasks), tmp_path, log=lambda _: None, stop_when_unchanged=True)
    rows = {r["variant"]: r for r in summarize(load_traces(tmp_path))}
    assert set(rows) == set("ABCDEF")
    # The fake checker's smoke test is correct, so it never counts as a wrong test.
    assert rows["D"]["wrong_test_rate"] == 0.0
