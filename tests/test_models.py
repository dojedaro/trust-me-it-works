"""The HTTP client's retry rules, with urlopen stubbed out (no network)."""

import io
import json
import urllib.error

import pytest

from trustme import models
from trustme.models import OpenAICompatModel

OK = {"choices": [{"message": {"content": "<think>hmm</think>hello"}, "finish_reason": "stop"}], "usage": {}}


def http_error(code: int, body: bytes) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x", code, "err", {}, io.BytesIO(body))


def stub(monkeypatch, outcomes):
    outcomes = list(outcomes)

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def urlopen(req, timeout):
        o = outcomes.pop(0)
        if isinstance(o, Exception):
            raise o
        return Resp(json.dumps(o).encode())

    monkeypatch.setattr(models.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(models.time, "sleep", lambda s: None)
    monkeypatch.setenv("KEY", "x")


def model() -> OpenAICompatModel:
    return OpenAICompatModel(model="m", base_url="http://x", api_key_env="KEY", min_interval_s=0)


def test_malformed_generation_is_retried(monkeypatch):
    stub(monkeypatch, [http_error(400, b'{"error":{"code":"tool_use_failed"}}'), OK])
    m = model()
    assert m.complete("s", "u").text == "hello"  # reasoning tags stripped
    assert m.glitches == 1


def test_other_bad_requests_fail_fast(monkeypatch):
    stub(monkeypatch, [http_error(400, b'{"error":{"code":"invalid_model"}}'), OK])
    with pytest.raises(RuntimeError, match="invalid_model"):
        model().complete("s", "u")


def test_server_errors_are_retried(monkeypatch):
    stub(monkeypatch, [http_error(503, b""), http_error(429, b""), OK])
    assert model().complete("s", "u").text == "hello"


def test_anthropic_errors_map_to_the_runner_contract():
    """The runner skips a run on RuntimeError and stops on RateLimited; SDK errors must become one of them."""
    anthropic = pytest.importorskip("anthropic")
    httpx = pytest.importorskip("httpx2")  # the HTTP library this SDK version uses

    from trustme.models import AnthropicModel, RateLimited

    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")

    def failing(exc):
        class Messages:
            def create(self, **kw):
                raise exc

        m = AnthropicModel(model="claude-haiku-4-5")
        m._client = type("Client", (), {"messages": Messages()})()
        return m

    limited = anthropic.RateLimitError("slow down", response=httpx.Response(429, request=request), body=None)
    with pytest.raises(RateLimited):
        failing(limited).complete("s", "u")
    overloaded = anthropic.InternalServerError("overloaded", response=httpx.Response(529, request=request), body=None)
    with pytest.raises(RuntimeError, match="InternalServerError"):
        failing(overloaded).complete("s", "u")
