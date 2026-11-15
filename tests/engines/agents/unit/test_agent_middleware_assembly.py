"""中间件装配：默认只剩事件流与模型重试。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from engines.agents.middleware import build_agent_middlewares


pytestmark = [pytest.mark.unit]

_ENV_NAMES = (
    "AGENT_MODEL_RETRY_ATTEMPTS",
    "AGENT_FALLBACK_MODEL",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """每个用例从干净的环境变量出发，避免互相污染。"""
    for name in _ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    return None


def _names(middlewares: list) -> list[str]:
    return [type(item).__name__ for item in middlewares]


class _FakeState:
    def __init__(self, text: str) -> None:
        message = SimpleNamespace(role="user", get_text_content=lambda: text)
        self.context = [message]


def _fake_agent(text: str) -> SimpleNamespace:
    return SimpleNamespace(state=_FakeState(text))


class _FakeRag:
    """记录检索次数、按预设返回或抛错的假检索服务。"""

    def __init__(self, hits: list | None = None, boom: bool = False) -> None:
        self.hits = hits or []
        self.boom = boom
        self.queries: list[str] = []

    async def search(self, query: str, top_k=None) -> list:
        self.queries.append(query)
        if self.boom:
            raise RuntimeError("向量库不可用")
        return self.hits


# ── 默认集合与顺序 ────────────────────────────────────────


def test_defaults_are_events_then_retry() -> None:
    names = _names(build_agent_middlewares())

    assert names[0] == "ReplyEventsMiddleware"
    assert names[-1] == "ModelRetryMiddleware"
    assert "TracingMiddleware" not in names
    assert "TTSMiddleware" not in names


def test_sop_can_skip_events() -> None:
    names = _names(build_agent_middlewares(with_events=False))

    assert "ReplyEventsMiddleware" not in names


# ── 各能力开关 ────────────────────────────────────────────


def test_rag_off_by_default() -> None:
    assert "RagContextMiddleware" not in _names(build_agent_middlewares())


def test_rag_skipped_when_index_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_RAG_ENABLED", "1")

    assert "RagContextMiddleware" not in _names(build_agent_middlewares())


def _enable_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    """把 RAG 的两个前置条件都打开：中间件开关 + 索引可用（需密钥）。"""
    monkeypatch.setenv("AGENT_RAG_ENABLED", "1")
    monkeypatch.setenv("KNOWLEDGE_ASSISTANT_RAG_ENABLED", "true")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")


def test_sop_roles_never_get_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_rag(monkeypatch)

    assert "RagContextMiddleware" not in _names(build_agent_middlewares())


def test_rag_prompt_injection_is_not_assembled(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_rag(monkeypatch)

    assert "RagContextMiddleware" not in _names(build_agent_middlewares())






