"""The loop engine, run with scripted fake models (no API)."""

import json
from pathlib import Path

import pytest

from trustme import prompts
from trustme.loop import ConfigError, Loop, NoChecker, OracleChecker, ScoreChecker, TestWriterChecker
from trustme.models import BudgetExceeded, CallBudget, FakeModel
from trustme.tasks import load_task

TASK = load_task(Path(__file__).parents[1] / "tasks" / "time" / "iso_week")


def answer(code: str) -> str:
    return f"PLAN: try this\n```python\n{code}```"


def scores(n: int) -> str:
    return json.dumps({"scores": dict.fromkeys(prompts.CRITERIA, n), "weakest": "x"})


def test_single_pass_records_ground_truth():
    trace = Loop(FakeModel([answer(TASK.naive)]), NoChecker(), max_iters=1).run(TASK, "A")
    assert trace.final_decision == "FINAL"
    assert len(trace.iterations) == 1
    assert trace.iterations[0].plan == "try this"
    assert trace.final_correct is False  # the naive solution falls into the trap
    assert trace.iterations[0].ground_truth["passed"] < trace.iterations[0].ground_truth["total"]


def test_maker_cannot_be_checker_by_accident():
    maker = FakeModel([], name="same-model")
    with pytest.raises(ConfigError):
        Loop(maker, ScoreChecker(maker))
    with pytest.raises(ConfigError):  # same model name, different object
        Loop(maker, ScoreChecker(FakeModel([], name="same-model")))
    Loop(maker, ScoreChecker(maker), allow_self_check=True)  # the deliberate baseline is allowed


def test_low_score_triggers_revision_with_feedback():
    maker = FakeModel([answer(TASK.naive), answer(TASK.reference)], name="maker")
    checker = FakeModel([scores(5), scores(9)], name="checker")
    trace = Loop(maker, ScoreChecker(checker), max_iters=5).run(TASK, "C")
    assert [it.verdict for it in trace.iterations] == ["ITERATING", "FINAL"]
    assert trace.final_decision == "FINAL" and trace.final_correct
    assert "Scores:" in maker.calls[1][1]  # the reviewer's feedback reached the maker


def test_confident_mistake_is_recorded_as_false_final():
    trace = Loop(FakeModel([answer(TASK.naive)], name="m"), ScoreChecker(FakeModel([scores(10)], name="c"))).run(TASK)
    assert trace.final_decision == "FINAL" and not trace.final_correct


def test_cap_reached():
    maker = FakeModel([answer(TASK.naive)] * 3, name="maker")
    checker = FakeModel([scores(3)] * 3, name="checker")
    trace = Loop(maker, ScoreChecker(checker), max_iters=3).run(TASK)
    assert trace.final_decision == "CAP_REACHED" and len(trace.iterations) == 3


def test_unparsable_review_keeps_iterating_and_is_recorded():
    maker = FakeModel([answer(TASK.reference)] * 2, name="maker")
    checker = FakeModel(["looks great!", scores(9)], name="checker")
    trace = Loop(maker, ScoreChecker(checker), max_iters=3).run(TASK)
    assert "parse_error" in trace.iterations[0].checker_details
    assert trace.final_decision == "FINAL"


def test_devils_advocate_tests_are_executed():
    breaking_test = (
        "```python\nfrom solution import iso_week\n"
        "def test_new_year():\n    assert iso_week('2024-12-30') == '2025-W01'\n```"
    )
    maker = FakeModel([answer(TASK.naive), answer(TASK.reference)], name="maker")
    checker = FakeModel([breaking_test, breaking_test], name="checker")
    trace = Loop(maker, TestWriterChecker(checker)).run(TASK, "D")
    assert [it.verdict for it in trace.iterations] == ["ITERATING", "FINAL"]
    assert trace.iterations[0].checker_details["report"]["failures"][0]["name"] == "test_new_year"
    assert trace.final_correct


def test_oracle_shows_hidden_failures_to_maker():
    maker = FakeModel([answer(TASK.naive), answer(TASK.reference)], name="maker")
    trace = Loop(maker, OracleChecker()).run(TASK, "E")
    assert trace.final_correct and len(trace.iterations) == 2
    assert "tests passed" in maker.calls[1][1]


def test_call_budget_is_a_hard_cap():
    budget = CallBudget(max_calls=2)
    budget.spend()
    budget.spend()
    with pytest.raises(BudgetExceeded):
        budget.spend()


def test_parsing_helpers():
    assert prompts.extract_code("x\n```python\nprint(1)\n```\n") == "print(1)\n"
    assert prompts.extract_code("print(2)") == "print(2)\n"
    assert prompts.extract_plan("PLAN: do it\n```\n```") == "do it"
    s, weakest = prompts.parse_scores('Sure! {"scores": {"correctness": 8, "edge_cases": 7, "spec_compliance": 9}}')
    assert s == {"correctness": 8, "edge_cases": 7, "spec_compliance": 9} and weakest == ""
    with pytest.raises(ValueError):
        prompts.parse_scores('{"scores": {"correctness": 11, "edge_cases": 7, "spec_compliance": 9}}')
