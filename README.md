# Trust Me, It Works

[![CI](https://github.com/dojedaro/trust-me-it-works/actions/workflows/ci.yml/badge.svg)](https://github.com/dojedaro/trust-me-it-works/actions/workflows/ci.yml)

**Can an AI tell when its own code is wrong?**

A popular prompting pattern asks a model to work in a loop: *plan, write, score your own work 1–10,
and stop when every score is 8 or higher.* The flaw is that the model that wrote the code is the one
grading it, so "FINAL, 9/10" can mean "the model is satisfied", not "the code is correct".

This project measures how often that happens, and which kinds of checker actually catch the mistakes.
Every iteration of every run is checked against **hidden tests the models never see**, so we always
know whether the checker was right.

> **Status:** first full results below (12 novel tasks × 2 samples × 6 variants, Claude Haiku 4.5 maker,
> Claude Sonnet 5.5 checker, $3.82 total). Every number comes from saved traces in `runs/`.

## Results

| Variant | Final correct | Checker approved wrong code | False alarms (rejected correct code) |
|---|---|---|---|
| A. Single pass | 58% (14/24) | n/a (no checker; 10 of 24 wrong) | 0 |
| B. Self-check | 71% (17/24) | **4 of 17 (24%)** | 15 |
| C. Cross-check (Sonnet scores) | **96% (23/24)** | 1 of 20 (5%) | 20 |
| D. Devil's advocate (Sonnet writes tests) | 92% (22/24) | 1 of 23 (4%) | 8 |
| E. Oracle (hidden-test failures shown) | 92% (22/24) | 0 of 22 | 0 |
| F. Devil's advocate + disputes | 92% (22/24) | 2 of 24 (8%) | 9 |

- **Self-checking approved wrong code in 4 of 17 cases; a different checker in 1 of 20.** The samples are
  small and the 95% intervals overlap (10–47% vs. 1–24%), so this is a strong hint, not a proven gap.
- **The checker's quality decides everything:** only 2.6% of Sonnet 5.5's tests were wrong (19 of 726),
  against 31% for gpt-oss-120b in the pilot.
- **The maker never pushed back:** in variant F it saw 117 failing tests and disputed none, though 23
  of the tests in that variant were themselves wrong. Disputes added cost and changed nothing.
- **Picky reviewers still helped:** cross-checking rejected correct code 20 times, but revisions broke
  working code only once.
- With 24 runs per variant the 95% intervals are wide (C: 80–99%, D/E/F: 74–98%), so C vs. D/E/F is
  not a real difference; A and B vs. the rest is.

## The experiment

The same small model writes the code in every variant. Only the checker changes:

| Variant | Checker | Question |
|---|---|---|
| **A. Single pass** | none | How good is one attempt? |
| **B. Self-check** | the maker scores its own code | Does self-reflection help? How often is "FINAL" wrong? |
| **C. Cross-check** | a different, larger model scores the code | Does a second opinion help? |
| **D. Devil's advocate** | a different model writes tests to break the code, and they run | Can AI hunt bugs better than it can grade them? |
| **E. Oracle** | hidden-test failures are shown to the maker | Upper bound with perfect feedback |
| **F. Devil's advocate with disputes** | as D, but the maker may dispute a failing test and the checker rules on it | Do disputes cut false alarms, or let the maker argue away real bugs? |

The key number is the **false FINAL rate**: how often a checker approved code that fails the hidden tests.
Every rate is reported with a 95% Wilson interval over 2 samples per task, because a single run per
task is noise: in the pilot, the same prompt to the same model at temperature 0 gave different results.

Other metrics, all computed from saved traces:

- **False alarms:** the checker rejected code that already passed every hidden test.
- **Broke working code:** the first attempt was correct and the final one isn't.
- **Wrong checker tests:** for test-writing checkers (D, F), each test is also run against our correct
  reference solution; a test that fails it is itself wrong. In the pilot, **23 of 75 (31%)** of the
  bug hunter's tests were wrong. Recorded for analysis, never shown to the models.
- **Withdrawn correct tests (F):** disputes that talked the checker out of a test that was right.

**Loop rule under test:** when the maker answers feedback with identical code, the loop stops instead
of asking the checker the same question again (in the pilot, 8 of 38 revisions were unchanged).

Models: [`configs/claude.toml`](configs/claude.toml) (used for the results above) or the $0
[`configs/free.toml`](configs/free.toml) (Groq free tier; its ~200k tokens/day limit makes a full run take days).

**Choosing the maker.** First-try pass rate on the 12 novel tasks: gpt-oss-20b 72% (42/58), Claude Haiku 4.5
67% (24/36), Claude Haiku 5.5 92% at low effort and 100% at medium. Haiku 5.5 left checkers nothing to catch,
so Haiku 4.5 writes the code.

**Caveats this design carries.** The maker was chosen after calibrating on the same 12 tasks the
experiment then ran on, so the tasks were picked to be hard for this maker. Checkers and maker are
both Claude models and may share blind spots. Two samples per task means the 24 runs per variant are
not 24 independent tasks. The clearest result is single pass vs. any checker
with real feedback (A: 58% correct, 39–76%; C: 96%, 80–99%), where the intervals don't overlap. Self-checking
(B: 71%, 51–85%) overlaps with C to F, and C to F are indistinguishable from each other.

## The Trap Room

24 original tasks in 6 rooms, in two tiers. The Claude results above use the 12 novel tasks:

- **Classic (12):** each hides one well-known trap, such as bowling's 10th frame or the A-2-3-4-5 straight.
- **Novel (12):** familiar problems with a changed rule or an easy-to-miss requirement, so the model's
  prior points the wrong way. Examples: bowling with no 10th-frame bonus, no-ad tennis, adding months
  with a sticky end of month, Korean particles after numbers (10을, 1000000000000를), ISO durations where
  `PT1M` is a minute and `P1M` is invalid, and SemVer precedence.

### Calibration: does the model fall for the traps?

Single attempts by the maker (gpt-oss-20b), 5 per task:

| Tier | First-try pass rate |
|---|---|
| Classic | **95%** (53 of 56 runs) |
| Novel | **72%** (42 of 58 runs) |

The pilot's maker solved every classic task on the first try, so the classic tier alone couldn't show
whether a checker helps. The novel tier is where checkers have something to catch. The two 0% tasks
were checked by hand to make sure they're fair: the spec states the rule, and the model misses it (for
example it writes "서울으로" although the spec says ㄹ takes 로).

Classic-tier traps:

| Room | Tasks | Trap examples |
|---|---|---|
| Korea | Hangul decomposition, initial-consonant search | conjoining vs. compatibility jamo; ㄱ ≠ ㄲ |
| Time | ISO week label, business days | 2024-12-30 is in 2025-W01; holidays on weekends |
| Games | bowling score, poker straight | 10th-frame bonus rolls; A-2-3-4-5 is five-high |
| Money | bill splitting, receipt rounding | lost cents with floats; `round(2.675, 2) == 2.67` |
| Text | case/encoding-insensitive compare, palindromes | `ß` vs `SS`; decomposed accents |
| Spec | leaderboard, dedupe | "must not modify the input"; unhashable items |

Each task folder has `task.toml` (prompt and trap note), `hidden_test.py` (≥5 tests), `reference.py`
(a correct solution) and `naive.py` (the obvious solution that falls into the trap). CI checks that every
reference passes all hidden tests and every naive solution fails at least one.

## Run it

```bash
python -m venv .venv && .venv/Scripts/activate      # Windows; on macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"

python -m trustme validate                 # every task is fair
python -m trustme run --fake               # full pipeline with scripted models, no API key needed
pytest                                     # harness, sandbox and loop-engine tests

# Reproduce the published results (Claude; about $4)
pip install -e ".[claude]"
echo ANTHROPIC_API_KEY=... >> .env
python -m trustme run --config configs/claude.toml --only novel --name my-run

# Or $0 on Groq's free tier (slow: ~200k tokens/day)
cp .env.example .env                       # then paste a free Groq API key into .env
python -m trustme models                   # check which model IDs Groq currently offers
python -m trustme run --variants A,B --only korea --name dev
python -m trustme summarize runs/dev
```

Runs save one JSON trace per (variant, task) in `runs/<name>/`. Interrupted runs resume where they stopped.

## How the loop works

```
for each iteration (max 5):
    PLAN + DO   maker writes solution.py
    VERIFY      checker returns FINAL or ITERATING, plus feedback
    TRUTH       hidden tests run and are recorded (never shown to the maker, except in variant E)
    DECIDE      stop on FINAL, otherwise send the feedback back to the maker
```

The engine refuses to use the same model as maker and checker unless the variant explicitly allows it
(only variant B, the baseline being measured).

## Sandbox and its limits

Model-written code runs in a separate Python process with a fresh temp directory, `python -I`, a
minimal environment, a 10-second timeout, and guards that block network access, subprocesses and file
writes outside the temp directory. These guards are tested, but they are **best-effort**: they are fine for
running our own experiments, not a security boundary against deliberately hostile code. A Docker-based
sandbox is planned for a public live demo.

## License

MIT
