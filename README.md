# Trust Me, It Works

**Can an AI tell when its own code is wrong?**

A popular prompting pattern asks a model to work in a loop: *plan, write, score your own work 1–10,
and stop when every score is 8 or higher.* The flaw is that the model that wrote the code is the one
grading it, so "FINAL, 9/10" can mean "the model is satisfied", not "the code is correct".

This project measures how often that happens, and which kinds of checker actually catch the mistakes.
Every iteration of every run is checked against **hidden tests the models never see**, so we always
know whether the checker was right.

> **Status:** the harness, sandbox and the first 12 tasks are done and tested. Real model runs are next.
> No results are reported yet; every number in this README will come from saved run data.

## The experiment

The same small model writes the code in every variant. Only the checker changes:

| Variant | Checker | Question |
|---|---|---|
| **A. Single pass** | none | How good is one attempt? |
| **B. Self-check** | the maker scores its own code | Does self-reflection help? How often is "FINAL" wrong? |
| **C. Cross-check** | a different, larger model scores the code | Does a second opinion help? |
| **D. Devil's advocate** | a different model writes tests to break the code, and they run | Can AI hunt bugs better than it can grade them? |
| **E. Oracle** | hidden-test failures are shown to the maker | Upper bound with perfect feedback |

The key number is the **false FINAL rate**: how often a checker approved code that fails the hidden tests.

Models are open-weight models served on Groq's free tier (see [`configs/free.toml`](configs/free.toml)),
so the whole study can be reproduced at no cost.

## The Trap Room

Original tasks, written for this project so the models can't have memorized them. Each looks easy and
hides one well-known trap:

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
