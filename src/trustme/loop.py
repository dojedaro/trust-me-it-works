"""The self-checking loop: PLAN -> DO -> VERIFY -> DECIDE, with hidden-test ground truth every iteration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal, Protocol

from . import prompts
from .models import Completion, Model
from .sandbox import TestReport, run_tests
from .tasks import Task

Verdict = Literal["FINAL", "ITERATING", "UNCHANGED"]


class ConfigError(ValueError):
    pass


@dataclass
class Usage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    truncated: int = 0  # replies cut off at the max_tokens cap

    def add(self, c: Completion) -> None:
        self.calls += 1
        self.input_tokens += c.input_tokens
        self.output_tokens += c.output_tokens
        self.truncated += c.truncated


@dataclass
class CheckResult:
    verdict: Verdict
    feedback: str
    details: dict = field(default_factory=dict)
    usage: Usage = field(default_factory=Usage)


class Checker(Protocol):
    kind: str
    model: Model | None

    def check(self, task: Task, code: str) -> CheckResult: ...


@dataclass
class NoChecker:
    """Variant A: accept the first attempt."""

    kind: str = "none"
    model: Model | None = None

    def check(self, task: Task, code: str) -> CheckResult:
        return CheckResult("FINAL", "", {})


@dataclass
class ScoreChecker:
    """Variants B and C: a model scores the code 1-10 per criterion. FINAL iff every score >= 8."""

    model: Model
    kind: str = "score"

    def check(self, task: Task, code: str) -> CheckResult:
        usage = Usage()
        c = self.model.complete(prompts.SCORE_SYSTEM, prompts.SCORE_USER.format(task=task.render_prompt(), code=code))
        usage.add(c)
        try:
            scores, weakest = prompts.parse_scores(c.text)
        except (ValueError, KeyError, TypeError) as e:
            # An unparsable review is no evidence the code is right: keep iterating, and record it.
            return CheckResult(
                "ITERATING",
                "The review could not be parsed. Re-check the solution against every requirement.",
                {"parse_error": str(e), "raw": c.text[:2000]},
                usage,
            )
        verdict: Verdict = "FINAL" if min(scores.values()) >= prompts.PASS_SCORE else "ITERATING"
        lowest = min(scores, key=lambda k: scores[k])
        feedback = f"Scores: {scores}. Weakest criterion: {lowest}. Problem: {weakest}"
        return CheckResult(verdict, feedback, {"scores": scores, "weakest": weakest}, usage)


@dataclass
class TestWriterChecker:
    """Variant D (devil's advocate): a model writes tests to break the code, and we run them."""

    __test__ = False  # not a pytest class

    model: Model
    kind: str = "tests"

    def check(self, task: Task, code: str) -> CheckResult:
        usage = Usage()
        user = prompts.TESTWRITER_USER.format(task=task.render_prompt(), code=code)
        c = self.model.complete(prompts.TESTWRITER_SYSTEM, user)
        usage.add(c)
        tests = prompts.extract_code(c.text)
        report = run_tests(code, tests)
        verdict: Verdict = "FINAL" if report.all_passed else "ITERATING"
        feedback = "The reviewer wrote tests against your code.\n" + report.summary()
        return CheckResult(verdict, feedback, {"tests": tests, "report": report.to_dict()}, usage)


@dataclass
class DisputeChecker:
    """Variant F (devil's advocate with disputes): like D, but the maker may dispute a failing test.

    1. The checker writes tests to break the code, and they run.
    2. For each failing test, the maker accepts it or disputes it with a reason.
    3. The checker rules on each dispute: uphold the test or withdraw it.
    4. Withdrawn tests no longer count. FINAL iff every remaining test passes.

    A loop design choice under test: it should cut false alarms caused by wrong tests, but a persuasive
    maker might also talk the checker out of a test that was right.
    """

    model: Model  # the checker
    maker: Model
    kind: str = "tests+disputes"

    def check(self, task: Task, code: str) -> CheckResult:
        usage = Usage()
        c = self.model.complete(
            prompts.TESTWRITER_SYSTEM, prompts.TESTWRITER_USER.format(task=task.render_prompt(), code=code)
        )
        usage.add(c)
        tests = prompts.extract_code(c.text)
        report = run_tests(code, tests)
        details: dict = {"tests": tests, "report": report.to_dict(), "disputes": {}, "rulings": {}, "withdrawn": []}
        failing = [r for r in report.results if not r.passed]
        if report.all_passed or not failing:
            # Nothing to dispute: a crash or import error is not a single test the maker can argue with.
            verdict: Verdict = "FINAL" if report.all_passed else "ITERATING"
            return CheckResult(
                verdict, "The reviewer wrote tests against your code.\n" + report.summary(), details, usage
            )

        failures = "\n".join(f"- {r.name}: {r.message}" for r in failing)
        d = self.maker.complete(
            prompts.DISPUTE_SYSTEM,
            prompts.DISPUTE_USER.format(task=task.render_prompt(), code=code, tests=tests, failures=failures),
        )
        usage.add(d)
        disputes = prompts.parse_decisions(d.text, {r.name for r in failing}, ("accept", "dispute"))
        details["disputes"] = disputes
        disputed = {name: v["reason"] for name, v in disputes.items() if v["action"] == "dispute"}

        withdrawn: set[str] = set()
        if disputed:
            claims = "\n".join(f"- {name}: {reason}" for name, reason in disputed.items())
            r = self.model.complete(
                prompts.RULING_SYSTEM,
                prompts.RULING_USER.format(task=task.render_prompt(), code=code, tests=tests, disputes=claims),
            )
            usage.add(r)
            rulings = prompts.parse_decisions(r.text, set(disputed), ("uphold", "withdraw"))
            details["rulings"] = rulings
            withdrawn = {name for name, v in rulings.items() if v["action"] == "withdraw"}
        details["withdrawn"] = sorted(withdrawn)

        upheld = [r for r in failing if r.name not in withdrawn]
        if not upheld:
            return CheckResult("FINAL", "Every failing test was withdrawn after your disputes.", details, usage)
        lines = [f"The reviewer's tests: {report.passed}/{report.total} passed, {len(withdrawn)} withdrawn on review."]
        lines += [f"- {r.name}: {r.message}" for r in upheld][:5]
        for r in upheld:
            if r.name in disputed:
                reason = details["rulings"].get(r.name, {}).get("reason", "")
                lines.append(f"The reviewer upheld {r.name} after your dispute: {reason}")
        return CheckResult("ITERATING", "\n".join(lines), details, usage)


@dataclass
class OracleChecker:
    """Variant E: our hidden tests, with failures shown to the maker. An upper bound, not a fair checker."""

    kind: str = "oracle"
    model: Model | None = None

    def check(self, task: Task, code: str) -> CheckResult:
        report = run_tests(code, task.hidden_test)
        verdict: Verdict = "FINAL" if report.all_passed else "ITERATING"
        return CheckResult(verdict, report.summary(), {"report": report.to_dict()})


@dataclass
class Iteration:
    index: int
    plan: str
    code: str
    verdict: Verdict
    feedback: str
    checker_details: dict
    ground_truth: dict
    maker_usage: Usage
    checker_usage: Usage
    checker_tests_truth: dict | None = None


@dataclass
class Trace:
    task_id: str
    room: str
    variant: str
    tier: str
    maker: str
    checker_kind: str
    checker_model: str | None
    max_iters: int
    sample: int = 0
    stop_when_unchanged: bool = False
    iterations: list[Iteration] = field(default_factory=list)
    final_decision: str = ""  # "FINAL", "UNCHANGED" or "CAP_REACHED"
    final_correct: bool = False
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class Loop:
    """Run the loop on one task.

    stop_when_unchanged: if the maker answers feedback by returning identical code, stop instead of asking
    the checker the same question again. The maker is standing by its answer, and another round would only
    spend calls (in the pilot, 8 of 38 devil's-advocate revisions returned identical code).
    """

    def __init__(
        self,
        maker: Model,
        checker: Checker,
        max_iters: int = 5,
        allow_self_check: bool = False,
        stop_when_unchanged: bool = False,
    ):
        if max_iters < 1:
            raise ConfigError("max_iters must be >= 1")
        if checker.model is not None and not allow_self_check and _same_model(maker, checker.model):
            raise ConfigError(
                f"maker and checker are both {maker.name!r}; the maker must not be the checker "
                "(set allow_self_check=True only for the self-check baseline)"
            )
        self.maker = maker
        self.checker = checker
        self.max_iters = max_iters
        self.stop_when_unchanged = stop_when_unchanged

    def run(self, task: Task, variant: str = "", sample: int = 0) -> Trace:
        trace = Trace(
            task_id=task.id,
            room=task.room,
            variant=variant,
            tier=task.tier,
            maker=self.maker.name,
            checker_kind=self.checker.kind,
            checker_model=self.checker.model.name if self.checker.model else None,
            max_iters=self.max_iters,
            sample=sample,
            stop_when_unchanged=self.stop_when_unchanged,
        )
        code, feedback = "", ""
        for i in range(self.max_iters):
            # PLAN + DO
            maker_usage = Usage()
            if i == 0:
                user = task.render_prompt()
            else:
                user = prompts.MAKER_REVISE.format(task=task.render_prompt(), code=code, feedback=feedback)
            reply = self.maker.complete(prompts.MAKER_SYSTEM, user)
            maker_usage.add(reply)
            previous, code = code, prompts.extract_code(reply.text)
            if i > 0 and self.stop_when_unchanged and code.strip() == previous.strip():
                last = trace.iterations[-1]
                trace.iterations.append(
                    Iteration(
                        index=i,
                        plan=prompts.extract_plan(reply.text),
                        code=code,
                        verdict="UNCHANGED",
                        feedback="",
                        checker_details={},
                        ground_truth=last.ground_truth,
                        maker_usage=maker_usage,
                        checker_usage=Usage(),
                    )
                )
                trace.final_decision = "UNCHANGED"
                break
            # VERIFY
            result = self.checker.check(task, code)
            # GROUND TRUTH (recorded, never shown to the maker except by the oracle checker)
            truth: TestReport = run_tests(code, task.hidden_test)
            # A checker that writes tests: run its tests against our correct reference solution.
            # A test that fails the reference is itself wrong. Recorded for analysis, never shown to anyone.
            tests_truth = None
            if "tests" in result.details:
                tests_truth = run_tests(task.reference, result.details["tests"]).to_dict()
            trace.iterations.append(
                Iteration(
                    index=i,
                    plan=prompts.extract_plan(reply.text),
                    code=code,
                    verdict=result.verdict,
                    feedback=result.feedback,
                    checker_details=result.details,
                    ground_truth=truth.to_dict(),
                    maker_usage=maker_usage,
                    checker_usage=result.usage,
                    checker_tests_truth=tests_truth,
                )
            )
            # DECIDE
            if result.verdict == "FINAL":
                trace.final_decision = "FINAL"
                break
            feedback = result.feedback
        else:
            trace.final_decision = "CAP_REACHED"
        trace.final_correct = trace.iterations[-1].ground_truth["all_passed"]
        return trace


def _same_model(a: Model, b: Model) -> bool:
    return a is b or a.name == b.name
