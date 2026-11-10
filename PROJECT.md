# Trust Me, It Works
### Can an AI tell when its own code is wrong?

> Project brief, written in the format of the self-checking loop template it studies.
> Created 2026-11-09 · Status: **Weekend 1 built (harness, sandbox, 12 tasks); real runs next** · Owner: Daniel (`dojedaro`)
>
> **Update 2026-11-10: switched to $0.** Models are open-weight (Llama) on Groq's free tier instead of
> paid Claude. Maker = small model, checker = larger model (`configs/free.toml`). Scope cut to 12 tasks
> (2 per room) for the first release; 36 is the stretch goal. Budget is a hard cap on model *calls*, not dollars.

---

## ▸ THE ORIGINAL TEMPLATE (what this project tests)

```
TASK:              [what to produce]
SUCCESS CRITERIA:  [strict criteria]
LOOP PROTOCOL:     PLAN → DO → VERIFY (score 1-10 per criterion) → DECIDE (all 8+ = FINAL)
RULES:             never done below 8 · fix the weakest score first · don't ask, assume
```

**The weakness:** in VERIFY, the model that did the work grades itself. Models tend to rate their
own output generously, so "FINAL, 9/10" can mean "the model is satisfied", not "the output is
correct". This project measures how often that happens, and which kinds of checker catch it.

**Our rule change:** the maker can't be the checker. Wherever possible, the checker is something
that can't be talked into a pass, such as real tests.

---

## ▸ TASK

Build an open-source experiment, **"Trust Me, It Works"**, that runs the self-checking loop on
original coding tasks and measures whether each kind of checker actually improves correctness.
It publishes the results as a GitHub repo, a README write-up with charts, and a trace viewer on Vercel.

**Deliverables**
1. **Loop engine:** a small Python package. `Loop(maker, checker, max_iters).run(task)` records every
   PLAN / DO / VERIFY / DECIDE step.
2. **The Trap Room:** about 36 original tasks in 6 themed rooms. Each has a prompt, visible examples, and
   hidden tests that target one documented trap.
3. **Experiment runner:** runs all 5 variants on all tasks and stores every iteration as JSON.
4. **Results:** charts plus a README write-up, including the "Hall of Fame of Confident Mistakes".
5. **Trace viewer:** a static site on Vercel to step through any run (no backend needed).

---

## ▸ SUCCESS CRITERIA (strict, no soft passes)

| # | Criterion | How it is checked (objectively, not by self-score) |
|---|-----------|-----------------------------------------------|
| 1 | **Original, trap-based tasks:** 36 tasks across 6 rooms, each with ≥5 hidden tests and a written note on its trap | Script counts tasks and tests; every task has a `trap` field |
| 2 | **Tasks are fair:** a correct reference solution passes 100% of the hidden tests, and a naive solution fails the trap | CI runs `reference.py` (all pass) and `naive.py` (≥1 fail) for every task |
| 3 | **Maker ≠ checker** in every variant except the deliberate self-check baseline | Config validation fails if a variant reuses the maker as the checker by mistake |
| 4 | **Untrusted code is isolated:** model-generated code runs with a timeout, no network, and a temp directory | Sandbox tests: infinite loop gets killed, network access fails, file writes stay in the temp dir |
| 5 | **Reproducible:** one command reproduces the results from the saved traces; model, prompts and seeds are recorded | `make results` rebuilds every chart from `runs/*.json` without API calls |
| 6 | **Honest numbers:** every claim in the README links to the data behind it; sample sizes and costs are reported | Each README number traces to a results table; cost per variant is shown |
| 7 | **Engineering quality:** tests, CI, lint, type hints, MIT license, pinned dependencies | GitHub Actions green |
| 8 | **Budget:** $0, free tier only | Runner enforces a hard cap on model calls (`max_calls`) and records tokens per call |

---

## ▸ LOOP PROTOCOL (the improved version we're testing)

Every iteration of every run:

1. **PLAN:** the maker states the single next step.
2. **DO:** the maker writes or revises the code.
3. **VERIFY:** the **checker** (which depends on the variant, see below) evaluates it:
   - scores each criterion 1–10 and names the weakest point, and/or
   - runs tests and reports the failures.
4. **DECIDE:** "FINAL" if the checker passes it (all scores ≥ 8, or all tests pass); otherwise "ITERATING",
   fixing the weakest point first. Hard cap: **5 iterations**.
5. **GROUND TRUTH (recorded, never shown to the maker except in variant E):** run the hidden tests
   after every iteration, so we always know if the checker was right.

### The 5 variants

| Variant | Maker | Checker | What it answers |
|---|---|---|---|
| **A. Single pass** | Sonnet 5.5 | none | Baseline: how good is one attempt? |
| **B. Self-check** (the original template) | Sonnet 5.5 | Sonnet 5.5 scores itself | Does self-reflection help? How often is "FINAL" wrong? |
| **C. Cross-check** | Sonnet 5.5 | **Opus 5.5** scores it | Does a different, stronger checker help? |
| **D. Devil's advocate** 😈 | Sonnet 5.5 | Opus 5.5 **writes tests to break the code**, and they actually run | Can an AI hunt bugs better than it can grade them? |
| **E. Oracle** | Sonnet 5.5 | **our hidden tests** (feedback shown to the maker) | Upper bound with perfect feedback |

Caveat to state in the write-up: Sonnet and Opus are both Claude models and may share blind spots.
The hidden tests are the only true ground truth.

---

## ▸ THE TRAP ROOM (task design)

All tasks are **written by us**, so the models can't have memorized them. Each looks easy and hides one classic trap.

| Room | Example tasks | The trap |
|---|---|---|
| 🇰🇷 **Korea** | Decompose Hangul syllables into jamo · Korean age vs. international age · format KRW | Unicode arithmetic (0xAC00 base) · the June 2023 legal switch to international age · KRW has no minor unit |
| ⏰ **Time** | Business days between dates · ISO week number · leap year | ISO week 1 can start in December · 1900 is not a leap year, 2000 is · inclusive/exclusive ranges across years |
| 🎳 **Game rules** | Bowling score · poker hand ranking · tennis scoring | Bonus rolls in the 10th frame · A-2-3-4-5 straight ("wheel") · deuce/advantage |
| 🔢 **Money and numbers** | Split a bill fairly · round currency · Roman numerals | Float error (0.1 + 0.2) · splits must sum exactly to the total · banker's vs. half-up rounding |
| 🔤 **Text** | Visible string length · case-insensitive equality · palindromes | 👨‍👩‍👧 is 1 character (grapheme clusters) · German ß → "SS" · accents/combining marks |
| 🧩 **Spec traps** | A single sentence in the spec changes the obvious answer | "Must not modify the input" · "ties keep their original order" (stable) |

**Task file format** (`tasks/<room>/<task_id>/`):
```
task.yaml       # id, room, title, prompt, signature, visible examples, trap description
hidden_test.py  # pytest tests (≥5), the ground truth
reference.py    # correct solution (must pass all hidden tests)
naive.py        # the "obvious" solution (must fail ≥1 trap test)
```

---

## ▸ METRICS & OUTPUTS

- **Pass rate vs. iteration:** per variant, iterations 0 to 5
- **"Confidence vs. Reality":** checker says FINAL vs. hidden tests pass (a 2×2 per variant)
  - **False FINAL rate:** how often the checker approved code that fails hidden tests (the key number)
- **Trap leaderboard:** which traps fooled which checker
- **Cost:** tokens and USD per variant, cost per correctly solved task
- **Hall of Fame of Confident Mistakes:** the highest self-scored answers that failed, with the trap that caught them

---

## ▸ ARCHITECTURE

### Phase 1: Weekend (no Mac mini needed, $0 hosting)
```
This PC (Windows)                               GitHub + Vercel
┌───────────────────────────────┐               ┌──────────────────────────┐
│ runner → loop engine          │──Claude API   │ repo: code, tasks, data  │
│   maker / checker / sandbox   │               │ Vercel: static trace     │
│   (subprocess: timeout,       │──push runs──► │ viewer reading runs/*.json│
│    temp dir, no network)      │               └──────────────────────────┘
└───────────────────────────────┘
```
Docker isn't installed on this PC, so Phase 1 uses an isolated subprocess sandbox (timeout,
temp working dir, network blocked, `python -I`). That's acceptable for our own controlled runs.

### Phase 2: Later, live demo (when the Mac mini is bought)
```
Browser → Vercel (frontend) → Tailscale Funnel / Cloudflare Tunnel → Mac mini
          Mac mini: FastAPI (rate limit, daily $ cap, queue, live streaming)
                    → loop engine → Claude API
                    → Docker sandbox per run (no network, 1 CPU, 512 MB, 10 s timeout)
                    → SQLite (runs, iterations, scores, cost)
```
The Mac mini will be a **dedicated personal machine, separate from the Hopae/Atlas Mac mini**. Never put a public
code-execution endpoint on a machine with work credentials.

### Costs
| Item | Cost |
|---|---|
| Claude API | **The only real ongoing cost.** Dev ≤ $1 (Haiku), final runs ≈ $15–25, live demo has a hard daily cap |
| Docker / OrbStack / Colima | Free for personal use |
| Vercel (Hobby) | Free for a personal, non-commercial portfolio |
| Tailscale Funnel | Free (stable `*.ts.net` address, no domain needed) |
| Domain (optional) | ~$10–15/year |
| Mac mini electricity (Phase 2) | ~$1–2/month |

---

## ▸ RULES (for building this project)

- Never call a criterion done until it is verified by the check in its table, not by opinion.
- Each work session fixes the weakest unmet criterion first.
- The maker is never the checker (except variant B, which exists to be measured).
- Build and test everything with a **fake model first**. Spend real API money only when the harness works.
- Every number in the README must come from saved data. No made-up or rounded-up claims.
- Model IDs live in `configs/free.toml`; verify them with `python -m trustme models` before each real run.

---

## ▸ DECISIONS MADE

- [x] Direction: code agent with real tests, designed as an eval study
- [x] Tasks: **original and as creative as possible** (no public benchmark)
- [x] Maker ≠ checker
- [x] Frontend on **Vercel**; static trace viewer first
- [x] API access: ~~Anthropic only~~ → Groq free tier, open-weight models (2026-11-10)
- [x] Time budget: a weekend for Phase 1
- [x] Mac mini: not owned yet → Phase 2 waits; must be separate from the Hopae Mac mini

## ▸ NEXT STEPS

1. [ ] Scaffold the repo (`pyproject.toml`, `src/trustme/`, `tasks/`, `runs/`, CI)
2. [ ] Loop engine + fake model + sandbox, with tests
3. [ ] Write the Trap Room: 36 tasks with `reference.py` / `naive.py` validation in CI
4. [ ] Dev run on Haiku (≤ $1) → fix the harness
5. [ ] **Needs from Daniel:** Claude API key with ~$25 credit in a local `.env`
6. [ ] Final runs (Sonnet maker, Opus checker) → charts → README write-up
7. [ ] Trace viewer → Vercel; create the public GitHub repo (with Daniel's approval)
8. [ ] Phase 2 (after buying the Mac mini): live backend
