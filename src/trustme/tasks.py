"""Load Trap Room tasks from tasks/<room>/<task_id>/."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

REQUIRED_FILES = ("task.toml", "hidden_test.py", "reference.py", "naive.py")


@dataclass(frozen=True)
class Example:
    call: str
    result: str


@dataclass(frozen=True)
class Task:
    id: str
    room: str
    title: str
    prompt: str
    signature: str
    examples: tuple[Example, ...]
    trap: str
    hidden_test: str
    reference: str
    naive: str

    def render_prompt(self) -> str:
        """What the maker sees. Never includes the trap note or the hidden tests."""
        examples = "\n".join(f"    {e.call}  ->  {e.result}" for e in self.examples)
        return f"{self.prompt.strip()}\n\nSignature:\n    {self.signature}\n\nExamples:\n{examples}"


def load_task(path: Path) -> Task:
    missing = [f for f in REQUIRED_FILES if not (path / f).exists()]
    if missing:
        raise FileNotFoundError(f"{path}: missing {missing}")
    meta = tomllib.loads((path / "task.toml").read_text(encoding="utf-8"))
    return Task(
        id=meta["id"],
        room=meta["room"],
        title=meta["title"],
        prompt=meta["prompt"],
        signature=meta["signature"],
        examples=tuple(Example(**e) for e in meta["examples"]),
        trap=meta["trap"],
        hidden_test=(path / "hidden_test.py").read_text(encoding="utf-8"),
        reference=(path / "reference.py").read_text(encoding="utf-8"),
        naive=(path / "naive.py").read_text(encoding="utf-8"),
    )


def load_tasks(root: Path, only: list[str] | None = None) -> list[Task]:
    """Load every task under root, optionally filtered by task id or room name."""
    tasks = [load_task(p.parent) for p in sorted(root.glob("*/*/task.toml"))]
    if only:
        tasks = [t for t in tasks if t.id in only or t.room in only]
    return tasks
