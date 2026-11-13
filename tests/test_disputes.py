"""Variant F (disputes), the stop-when-unchanged rule, and the wrong-test metric. Fake models, no API."""

import json
from pathlib import Path

from trustme import prompts
from trustme.loop import DisputeChecker, Loop, TestWriterChecker
from trustme.models import FakeModel
from trustme.runner import summarize
from trustme.tasks import load_task

TASK = load_task(Path(__file__).parents[1] / "tasks" / "time" / "iso_week")

# One right test (the ISO year differs from the calendar year) and one wrong one (bad expected value).
TESTS = """```python
from solution import iso_week
def test_new_year():
    assert iso_week('2024-12-30') == '2025-W01'
def test_wrong_expectation():
    assert iso_week('2026-11-10') == '2026-W45'
```"""


def answer(code: str) -> str:
    return f"PLAN: try this\n```python\n{code}```"


def decisions(**kw: str) -> str:
    return json.dumps({name: {"action": action, "reason": "because"} for name, action in kw.items()})


def router(tests: list[str], rulings: list[str]):
    """A fake checker that answers by role: write tests, or rule on disputes."""
    tests, rulings = list(tests), list(rulings)

    def respond(system: str, user: str) -> str:
        return (tests if system == prompts.TESTWRITER_SYSTEM else rulings).pop(0)

    return respond


def maker_router(code: list[str], disputes: list[str]):
    code, disputes = list(code), list(disputes)

    def respond(system: str, user: str) -> str:
        return (disputes if system == prompts.DISPUTE_SYSTEM else code).pop(0)

    return respond


def test_withdrawing_a_wrong_test_avoids_a_false_alarm():
    maker = FakeModel(maker_router([answer(TASK.reference)], [decisions(test_wrong_expectation="dispute")]), name="m")
    checker = FakeModel(router([TESTS], [decisions(test_wrong_expectation="withdraw")]), name="c")
    trace = Loop(maker, DisputeChecker(checker, maker=maker)).run(TASK, "F")

    assert trace.final_decision == "FINAL" and trace.final_correct
    it = trace.iterations[0]
    assert it.checker_details["withdrawn"] == ["test_wrong_expectation"]
    # The withdrawn test really was wrong: it fails the correct reference too.
    assert [f["name"] for f in it.checker_tests_truth["failures"]] == ["test_wrong_expectation"]


def test_upheld_dispute_sends_the_ruling_back_to_the_maker():
    maker = FakeModel(
        maker_router(
            [answer(TASK.naive), answer(TASK.reference)],
            [decisions(test_new_year="dispute"), decisions(test_wrong_expectation="dispute")],
        ),
        name="m",
    )
    checker = FakeModel(
        router([TESTS, TESTS], [decisions(test_new_year="uphold"), decisions(test_wrong_expectation="withdraw")]),
        name="c",
    )
    trace = Loop(maker, DisputeChecker(checker, maker=maker)).run(TASK, "F")
    assert [it.verdict for it in trace.iterations] == ["ITERATING", "FINAL"]
    revise_prompt = [u for s, u in maker.calls if s == prompts.MAKER_SYSTEM][1]
    assert "upheld test_new_year" in revise_prompt


def test_garbled_dispute_reply_never_removes_a_test():
    maker = FakeModel(maker_router([answer(TASK.reference)], ["I disagree with everything!"]), name="m")
    checker = FakeModel(router([TESTS], []), name="c")
    trace = Loop(maker, DisputeChecker(checker, maker=maker), max_iters=1).run(TASK, "F")
    assert trace.iterations[0].verdict == "ITERATING"
    assert trace.iterations[0].checker_details["withdrawn"] == []
    assert len(checker.calls) == 1  # nothing disputed, so no ruling call


def test_parse_decisions_defaults_to_the_safe_action():
    names = {"test_a", "test_b"}
    out = prompts.parse_decisions(
        '{"test_a": {"action": "dispute", "reason": "x"}, "test_c": {}}', names, ("accept", "dispute")
    )
    assert out["test_a"]["action"] == "dispute" and out["test_b"]["action"] == "accept"
    assert all(
        v["action"] == "uphold" for v in prompts.parse_decisions("{not json", names, ("uphold", "withdraw")).values()
    )
    assert (
        prompts.parse_decisions('{"test_a": {"action": "delete"}}', names, ("uphold", "withdraw"))["test_a"]["action"]
        == "uphold"
    )


def test_maker_standing_by_its_code_stops_the_loop():
    maker = FakeModel([answer(TASK.reference)] * 3, name="m")
    checker = FakeModel([TESTS] * 3, name="c")
    trace = Loop(maker, TestWriterChecker(checker), max_iters=5, stop_when_unchanged=True).run(TASK, "D")
    assert [it.verdict for it in trace.iterations] == ["ITERATING", "UNCHANGED"]
    assert trace.final_decision == "UNCHANGED" and trace.final_correct
    assert len(checker.calls) == 1  # the checker wasn't asked the same question twice


def test_without_the_rule_the_loop_runs_to_the_cap():
    maker = FakeModel([answer(TASK.reference)] * 3, name="m")
    checker = FakeModel([TESTS] * 3, name="c")
    trace = Loop(maker, TestWriterChecker(checker), max_iters=3).run(TASK, "D")
    assert trace.final_decision == "CAP_REACHED" and len(checker.calls) == 3


def test_summary_counts_wrong_tests_and_wrongly_withdrawn_ones():
    maker = FakeModel(
        maker_router([answer(TASK.reference)], [decisions(test_new_year="dispute", test_wrong_expectation="dispute")]),
        name="m",
    )
    checker = FakeModel(
        router([TESTS], [decisions(test_new_year="withdraw", test_wrong_expectation="withdraw")]), name="c"
    )
    loop = Loop(maker, DisputeChecker(checker, maker=maker), max_iters=1)
    trace = loop.run(TASK, "F").to_dict()
    # Pretend the checker was also talked out of test_new_year, a correct test (the reference passes it).
    trace["iterations"][0]["checker_details"]["withdrawn"] = ["test_new_year", "test_wrong_expectation"]
    (row,) = summarize([trace])
    assert row["checker_tests"] == 2 and row["wrong_tests"] == 1 and row["wrong_test_rate"] == 0.5
    assert row["withdrawn"] == 2 and row["withdrawn_correct_tests"] == 1
