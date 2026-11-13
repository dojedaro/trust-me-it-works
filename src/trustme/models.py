"""Model clients: a scripted fake for tests, and any OpenAI-compatible chat API (Groq, Gemini, ...)."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Protocol

USER_AGENT = "trust-me-it-works/0.1"
MAX_RETRY_WAIT_S = 120.0  # a longer wait means a daily quota is used up: stop and resume later
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


class RateLimited(RuntimeError):
    """The provider's quota is exhausted for longer than we are willing to wait. Re-run later to resume."""


@dataclass
class Completion:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    truncated: bool = False  # the reply hit the max_tokens cap (often: all spent on hidden reasoning)


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
    max_tokens: int = 4096
    min_interval_s: float = 2.0  # stay under free-tier rate limits
    max_retries: int = 6
    reasoning_effort: str | None = None  # "low" / "medium" / "high" for reasoning models that support it
    budget: CallBudget | None = None
    glitches: int = 0  # provider-side malformed generations that were retried
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
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort
        body = json.dumps(payload).encode()
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
                    wait_s = float(retry_after) if retry_after else 2.0 * 2**attempt
                    if wait_s > MAX_RETRY_WAIT_S:
                        raise RateLimited(f"{self.model}: rate limited for {wait_s:.0f}s; re-run later") from e
                    time.sleep(wait_s)
                    continue
                body = e.read()
                if e.code == 400 and b"tool_use_failed" in body:
                    # gpt-oss sometimes emits a malformed internal channel that the provider rejects as a
                    # tool call. It's a sampling glitch, not a bad request: the same request usually works.
                    self.glitches += 1
                    continue
                raise RuntimeError(f"{self.model}: HTTP {e.code}: {body[:500]!r}") from e
            usage = data.get("usage") or {}
            choice = data["choices"][0]
            return Completion(
                text=_THINK.sub("", choice["message"]["content"] or "").strip(),
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                truncated=choice.get("finish_reason") == "length",
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


# Models that accept the server-side refusal fallback routed by category.
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-sonnet-5-5"}


@dataclass
class AnthropicModel:
    """Claude through the official Anthropic SDK (optional dependency: pip install -e ".[claude]").

    Current Claude models reject a temperature setting, so samples differ by default; adaptive thinking
    counts toward max_tokens, so the cap is set generously and truncation is recorded.
    """

    model: str
    api_key_env: str = "ANTHROPIC_API_KEY"
    max_tokens: int = 8000
    effort: str | None = None  # "low" / "medium" / "high"
    budget: CallBudget | None = None
    refusals: int = 0
    _client: object = None

    @property
    def name(self) -> str:
        return self.model

    def complete(self, system: str, user: str) -> Completion:
        if self.budget is not None:
            self.budget.spend()
        if self._client is None:
            import anthropic  # optional dependency

            self._client = anthropic.Anthropic(api_key=os.environ.get(self.api_key_env), max_retries=6)
        params: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        if self.effort:
            params["output_config"] = {"effort": self.effort}
        import anthropic

        try:
            if self.model in _FALLBACK_MODELS:
                # On a safety-classifier decline, the API re-runs the request on a fallback model in the same call.
                resp = self._client.beta.messages.create(
                    betas=["server-side-fallback-2026-07-01"], fallbacks="default", **params
                )
            else:
                resp = self._client.messages.create(**params)
        except anthropic.RateLimitError as e:
            # The SDK already retried with backoff; stop the run so it can resume later.
            raise RateLimited(f"{self.model}: rate limited after retries; re-run later") from e
        except anthropic.APIError as e:
            # The runner skips a (variant, task, sample) on RuntimeError and retries it on the next run.
            raise RuntimeError(f"{self.model}: {type(e).__name__}: {e}") from e
        if resp.stop_reason == "refusal":
            self.refusals += 1
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        return Completion(
            text=text.strip(),
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            truncated=resp.stop_reason == "max_tokens",
        )
