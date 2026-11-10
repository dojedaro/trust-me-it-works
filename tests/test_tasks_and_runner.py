"""Criteria 1-2 (fair tasks) and the runner's resume + summary behaviour."""

from pathlib import Path

import pytest

from trustme.runner import fake_models, load_traces, run_experiment, summarize
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
    written = run_experiment(tasks, ["A", "E"], fake_models(tasks), tmp_path, log=logs.append)
    assert len(written) == 4
    assert run_experiment(tasks, ["A", "E"], fake_models(tasks), tmp_path, log=logs.append) == []  # resume

    rows = {r["variant"]: r for r in summarize(load_traces(tmp_path))}
    assert rows["A"]["false_final"] == 2 and rows["A"]["false_final_rate"] == 1.0
    assert rows["E"]["final_correct"] == 2 and rows["E"]["false_final"] == 0
