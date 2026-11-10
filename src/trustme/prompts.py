"""Prompts and output parsing. Kept in one place so every variant sees the same wording."""

from __future__ import annotations

import json
import re

CRITERIA = ("correctness", "edge_cases", "spec_compliance")
PASS_SCORE = 8

MAKER_SYSTEM = """You are an expert Python programmer solving a small coding task.
Reply in exactly this format:
PLAN: <one sentence: the single next step you are taking>
```python
<the complete contents of solution.py>
```
Use only the Python standard library. Do not include tests or example usage."""

MAKER_REVISE = """{task}

Your previous solution:
```python
{code}
```

A reviewer checked it and said:
{feedback}

Fix the weakest point first, then return the complete revised solution.py."""

SCORE_SYSTEM = """You are a strict code reviewer. You will see a coding task and a proposed solution.
Score the solution from 1 to 10 on each criterion:
- correctness: does it return the right answer for normal inputs?
- edge_cases: does it handle tricky and boundary inputs?
- spec_compliance: does it follow every sentence of the task exactly?
Reply with only a JSON object, no other text, where "weakest" names the most serious problem (or "none"):
{"scores": {"correctness": n, "edge_cases": n, "spec_compliance": n}, "weakest": "..."}"""

SCORE_USER = """TASK:
{task}

PROPOSED solution.py:
```python
{code}
```"""

TESTWRITER_SYSTEM = """You are a bug hunter. You will see a coding task and a proposed solution.
Write Python test functions designed to BREAK the solution: target tricky inputs, boundaries,
and every requirement in the task. Each test must be a plain function named test_<something>
that uses `assert`. Import the function under test with `from solution import <name>`.
Base expected values on the task statement, never on what the solution happens to return.
Reply with only one ```python code block containing the tests. Standard library only."""

TESTWRITER_USER = SCORE_USER

_CODE_BLOCK = re.compile(r"```(?:python|py)?[ \t]*\r?\n(.*?)```", re.DOTALL | re.IGNORECASE)
_PLAN = re.compile(r"^\s*PLAN:\s*(.+)$", re.MULTILINE)
_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


def extract_code(text: str) -> str:
    """Return the longest fenced Python block, or the whole text if there is no fence."""
    blocks = _CODE_BLOCK.findall(text)
    if blocks:
        return max(blocks, key=len).strip() + "\n"
    return text.strip() + "\n"


def extract_plan(text: str) -> str:
    match = _PLAN.search(text)
    return match.group(1).strip() if match else ""


def parse_scores(text: str) -> tuple[dict[str, int], str]:
    """Parse the score checker's JSON. Raises ValueError if it is unusable."""
    match = _JSON_OBJECT.search(text)
    if not match:
        raise ValueError("no JSON object found")
    data = json.loads(match.group(0))
    raw = data["scores"]
    scores = {c: int(raw[c]) for c in CRITERIA}
    if not all(1 <= s <= 10 for s in scores.values()):
        raise ValueError(f"scores out of range: {scores}")
    return scores, str(data.get("weakest", "")).strip()
