"""中间件装配：默认集合、顺序、各能力开关与单项失败隔离。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from engines.agents.middleware import (
    build_agent_middlewares,
    build_budget_middleware,
    build_memory_middleware,
    build_rag_middleware,
    build_tracing_middleware,
    build_tts_middleware,
)
from engines.agents.middleware import tracing as tracing_module
from engines.agents.middleware.rag_context import RagContextMiddleware

pytestmark = [pytest.mark.unit]

_ENV_NAMES = (
    "AGENT_MODEL_RETRY_ATTEMPTS",
    "AGENT_FALLBACK_MODEL",
    "AGENT_REPLY_TOKEN_BUDGET",
    "AGENT_REPLY_INPUT_WEIGHT",
    "AGENT_REPLY_OUTPUT_WEIGHT",
    "AGENT_TRACING_OTLP_ENDPOINT",
    "AGENT_TRACING_SERVICE_NAME",
    "AGENT_RAG_ENABLED",
    "AGENT_RAG_TOP_K",
    "AGENT_TTS_MIDDLEWARE",
    "AGENT_TTS_MODEL",
    "AGENT_TTS_VOICE",
    "AGENT_MEMORY_BACKEND",
    "KNOWLEDGE_ASSISTANT_RAG_ENABLED",
    "DASHSCOPE_API_KEY",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """每个用例从干净的环境变量出发，避免互相污染。"""
    for name in _ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(tracing_module, "_configured", False)


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


def test_defaults_are_budget_plus_retry() -> None:
    assert _names(build_agent_middlewares()) == [
        "ReplyBudgetControlMiddleware",
        "ModelRetryMiddleware",
    ]


def test_budget_on_by_default() -> None:
    middleware = build_budget_middleware()

    assert middleware is not None
    assert middleware.token_budget == 600_000
    assert middleware.output_token_weight == 2.0


def test_budget_zero_disables_it(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_REPLY_TOKEN_BUDGET", "0")

    assert build_budget_middleware() is None


def test_budget_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_REPLY_TOKEN_BUDGET", "1234")
    monkeypatch.setenv("AGENT_REPLY_INPUT_WEIGHT", "1")
    monkeypatch.setenv("AGENT_REPLY_OUTPUT_WEIGHT", "3")

    middleware = build_budget_middleware()

    assert middleware is not None
    assert middleware.token_budget == 1234
    assert middleware.input_token_weight == 1.0
    assert middleware.output_token_weight == 3.0


def test_order_is_fixed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_TRACING_OTLP_ENDPOINT", "http://127.0.0.1:4318/v1/traces")
    monkeypatch.setenv("AGENT_TTS_MIDDLEWARE", "1")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setenv("AGENT_REPLY_TOKEN_BUDGET", "1000")

    names = _names(build_agent_middlewares())

    assert names[0] == "TracingMiddleware"
    assert names.index("ReplyBudgetControlMiddleware") < names.index("TTSMiddleware")
    assert names[-1] == "ModelRetryMiddleware"


# ── 各能力开关 ────────────────────────────────────────────


def test_tracing_off_without_endpoint() -> None:
    assert build_tracing_middleware() is None


def test_tracing_on_with_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_TRACING_OTLP_ENDPOINT", "http://127.0.0.1:4318/v1/traces")

    assert type(build_tracing_middleware()).__name__ == "TracingMiddleware"


def test_rag_off_by_default() -> None:
    assert build_rag_middleware() is None


def test_rag_skipped_when_index_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_RAG_ENABLED", "1")

    assert build_rag_middleware() is None


def _enable_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    """把 RAG 的两个前置条件都打开：中间件开关 + 索引可用（需密钥）。"""
    monkeypatch.setenv("AGENT_RAG_ENABLED", "1")
    monkeypatch.setenv("KNOWLEDGE_ASSISTANT_RAG_ENABLED", "true")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")


def test_sop_roles_never_get_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_rag(monkeypatch)

    assert "RagContextMiddleware" not in _names(build_agent_middlewares())


def test_knowledge_roles_get_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_rag(monkeypatch)

    assert "RagContextMiddleware" in _names(build_agent_middlewares(with_rag=True))


def test_memory_entry_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MEMORY_BACKEND", "mem0")

    assert build_memory_middleware() is None


def test_tts_off_by_default() -> None:
    assert build_tts_middleware() is None


def test_tts_skipped_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_TTS_MIDDLEWARE", "1")

    assert build_tts_middleware() is None


def test_tts_builds_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_TTS_MIDDLEWARE", "1")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setenv("AGENT_TTS_VOICE", "Cherry")

    assert type(build_tts_middleware()).__name__ == "TTSMiddleware"


# ── RAG 上下文注入 ────────────────────────────────────────


async def test_rag_context_appends_hits() -> None:
    from engines.agents.rag.service import RagHit

    service = _FakeRag(
        [RagHit(source="手册.md", text="开关在设置页", score=0.9, chunk_index=0, document_id="d1")]
    )
    middleware = RagContextMiddleware(service, top_k=3)

    prompt = await middleware.on_system_prompt(_fake_agent("开关在哪"), "你是助手")

    assert prompt.startswith("你是助手")
    assert "参考资料" in prompt
    assert "开关在设置页" in prompt


async def test_rag_context_reuses_result_for_same_query() -> None:
    from engines.agents.rag.service import RagHit

    service = _FakeRag(
        [RagHit(source="手册.md", text="片段", score=0.5, chunk_index=0, document_id="d1")]
    )
    middleware = RagContextMiddleware(service)
    agent = _fake_agent("同一个问题")

    await middleware.on_system_prompt(agent, "提示词")
    await middleware.on_system_prompt(agent, "提示词")

    assert service.queries == ["同一个问题"]


async def test_rag_context_without_hits_keeps_prompt() -> None:
    middleware = RagContextMiddleware(_FakeRag([]))

    assert await middleware.on_system_prompt(_fake_agent("问题"), "提示词") == "提示词"


async def test_rag_context_degrades_on_error() -> None:
    middleware = RagContextMiddleware(_FakeRag(boom=True))

    assert await middleware.on_system_prompt(_fake_agent("问题"), "提示词") == "提示词"


async def test_rag_context_without_user_message_keeps_prompt() -> None:
    middleware = RagContextMiddleware(_FakeRag([]))
    agent = SimpleNamespace(state=SimpleNamespace(context=[]))

    assert await middleware.on_system_prompt(agent, "提示词") == "提示词"
