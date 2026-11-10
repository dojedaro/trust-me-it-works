"""Model clients: a scripted fake for tests, and any OpenAI-compatible chat API (Groq, Gemini, ...)."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Protocol

USER_AGENT = "trust-me-it-works/0.1"


@dataclass
class Completion:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class Model(Protocol):
    @property
    def name(self) -> str: ...

    def complete(self, system: str, user: str) -> Completion: ...


class BudgetExceeded(RuntimeError):
    """Raised when a run would exceed its hard cap on model calls."""


@dataclass
class CallBudget:
    """Hard cap on the number of model calls, shared by every model in a run."""

    max_calls: int
    used: int = 0

    def spend(self) -> None:
        if self.used >= self.max_calls:
            raise BudgetExceeded(f"call budget of {self.max_calls} exhausted")
        self.used += 1


@dataclass
class FakeModel:
    """Returns scripted responses, so the whole harness can be tested without an API.

    `script` is either a list of responses (consumed in order) or a function of (system, user).
    """

    script: Sequence[str] | Callable[[str, str], str]
    name: str = "fake"
    calls: list[tuple[str, str]] = field(default_factory=list)

    def complete(self, system: str, user: str) -> Completion:
        self.calls.append((system, user))
        if callable(self.script):
            text = self.script(system, user)
        else:
            if len(self.calls) > len(self.script):
                raise RuntimeError(f"FakeModel {self.name!r} ran out of scripted responses")
            text = self.script[len(self.calls) - 1]
        return Completion(text=text, input_tokens=len(system + user) // 4, output_tokens=len(text) // 4)


@dataclass
class OpenAICompatModel:
    """Chat-completions client for any OpenAI-compatible endpoint (stdlib only, no SDK)."""

    model: str
    base_url: str
    api_key_env: str
    temperature: float = 0.0
    max_tokens: int = 2048
    min_interval_s: float = 2.0  # stay under free-tier requests-per-minute limits
    max_retries: int = 6
    budget: CallBudget | None = None
    _last_call: float = 0.0

    @property
    def name(self) -> str:
        return self.model

    def complete(self, system: str, user: str) -> Completion:
        if self.budget is not None:
            self.budget.spend()
        key = os.environ.get(self.api_key_env)
        if not key:
            raise RuntimeError(f"environment variable {self.api_key_env} is not set (see .env.example)")
        body = json.dumps(
            {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            }
        ).encode()
        for attempt in range(self.max_retries):
            wait = self.min_interval_s - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()
            req = urllib.request.Request(
                self.base_url.rstrip("/") + "/chat/completions",
                data=body,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "User-Agent": USER_AGENT,
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.load(resp)
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    retry_after = e.headers.get("retry-after")
                    time.sleep(float(retry_after) if retry_after else 2.0 * 2**attempt)
                    continue
                raise RuntimeError(f"{self.model}: HTTP {e.code}: {e.read()[:500]!r}") from e
            usage = data.get("usage") or {}
            return Completion(
                text=data["choices"][0]["message"]["content"] or "",
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
            )
        raise RuntimeError(f"{self.model}: gave up after {self.max_retries} retries")


def list_models(base_url: str, api_key_env: str) -> list[str]:
    """Ask the provider which model IDs exist, instead of guessing them."""
    key = os.environ.get(api_key_env)
    if not key:
        raise RuntimeError(f"environment variable {api_key_env} is not set")
    req = urllib.request.Request(
        base_url.rstrip("/") + "/models",
        headers={"Authorization": f"Bearer {key}", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return sorted(m["id"] for m in json.load(resp)["data"])
