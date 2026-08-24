"""ai_assistant 接口测试共享基础设施 — 端点常量 / 认证 / 数据工厂。

风格对齐 tests/auth 与 tests/case_manager：live-server 黑盒测试
（TEST_BASE_URL 默认 http://localhost:8766），admin 登录取 token，
数据经 HTTP API 创建，名称带 uuid 后缀避免碰撞。

不用 django_db 的原因：仓库迁移链含 MySQL 专属 RunSQL
（test_runner/0017、ai_assistant/0021），SQLite 测试库无法建库
（tests/auth/test_me.py 中已有 xfail 记录）。
"""

import uuid

import pytest
import requests

# ── 端点常量（避免 URL 字符串散落各测试函数） ──

LOGIN_URL = "/api/auth/login"
REGISTER_URL = "/api/auth/register"

AGENTS_URL = "/api/ai/agents"
AGENT_DETAIL_URL = "/api/ai/agents/{agent_id}"
AGENT_CREATE_URL = "/api/ai/agents/create"
AGENT_UPDATE_URL = "/api/ai/agents/{agent_id}/update"
AGENT_DELETE_URL = "/api/ai/agents/{agent_id}/delete"
AGENT_REVEAL_KEY_URL = "/api/ai/agents/{agent_id}/reveal-key"
AGENT_HEALTH_URL = "/api/ai/agents/health"
AGENT_TEST_URL = "/api/ai/agents/{agent_id}/test"
AGENT_MODELS_URL = "/api/ai/agents/{agent_id}/models"
MODELS_DETECT_URL = "/api/ai/models/detect"
AVAILABLE_TOOLS_URL = "/api/ai/available-tools"
AVAILABLE_SKILLS_URL = "/api/ai/available-skills"

CONVERSATIONS_URL = "/api/ai/agents/{agent_id}/conversations"
CONVERSATION_CREATE_URL = "/api/ai/agents/{agent_id}/conversations/create"
MESSAGES_URL = "/api/ai/conversations/{conv_id}/messages"
SAVE_MESSAGE_URL = "/api/ai/conversations/{conv_id}/save-message"
CONFIRM_RESULT_URL = "/api/ai/conversations/{conv_id}/confirm-result"
RENAME_URL = "/api/ai/conversations/{conv_id}/rename"
DELETE_CONVERSATION_URL = "/api/ai/conversations/{conv_id}/delete"
CONV_TASKS_URL = "/api/ai/conversations/{conv_id}/tasks"
CONV_TASK_DETAIL_URL = "/api/ai/conversations/{conv_id}/tasks/{run_id}"
AI_TASKS_URL = "/api/ai/tasks"

TOOLBOX_URL = "/api/ai/toolbox"
TOOLBOX_CREATE_URL = "/api/ai/toolbox/create"
TOOLBOX_UPDATE_URL = "/api/ai/toolbox/{item_id}/update"
TOOLBOX_DELETE_URL = "/api/ai/toolbox/{item_id}/delete"
TOOLBOX_UPLOAD_SKILL_URL = "/api/ai/toolbox/upload-skill"
IMPORT_FROM_TOOLBOX_URL = "/api/ai/agents/{agent_id}/tools/import-from-toolbox"

KB_STATUS_URL = "/api/ai/knowledge/status"
KB_DOCUMENTS_URL = "/api/ai/knowledge/documents"
KB_ADD_DOC_URL = "/api/ai/knowledge/documents/add"

UPLOAD_AVATAR_URL = "/api/ai/upload-avatar"
UPLOAD_FILE_URL = "/api/ai/upload-file"

AGENT_TOOLS_URL = "/api/ai/agents/{agent_id}/tools"
TOOL_TOGGLE_URL = "/api/ai/agents/{agent_id}/tools/{tool_id}/toggle"
TOOL_DELETE_URL = "/api/ai/agents/{agent_id}/tools/{tool_id}/delete"

TIMEOUT = 30


# ── 工具函数 ──


def _unique(slug: str) -> str:
    """名称加 uuid 后缀，避免多次运行/并发时的数据碰撞。"""
    return f"{slug}_{uuid.uuid4().hex[:8]}"


# ── 认证 fixture ──


@pytest.fixture(scope="session")
def auth_token(base_url: str) -> str:
    """admin 登录返回 access_token（与 tests/auth、tests/case_manager 同源）。"""
    resp = requests.post(
        f"{base_url}{LOGIN_URL}",
        json={"username": "admin", "password": "admin123"},
        timeout=10,
    )
    body = resp.json()
    assert body.get("status") is True, f"Login failed: {body}"
    return body["data"]["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """admin（用户 1）的 Bearer 头。"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="session")
def other_auth_headers(base_url: str) -> dict:
    """注册一个临时用户并返回其 Bearer 头（用于 403 所有权用例）。

    注册契约：username 3-20 字符、password ≥6 位、password2/email 必填（tests/auth 契约）。
    """
    username = _unique("aiu")
    reg = requests.post(
        f"{base_url}{REGISTER_URL}",
        json={
            "username": username,
            "password": "Test123456",
            "password2": "Test123456",
            "email": f"{username}@test.local",
        },
        timeout=10,
    )
    assert reg.status_code == 200, f"Register failed: {reg.text}"
    login = requests.post(
        f"{base_url}{LOGIN_URL}",
        json={"username": username, "password": "Test123456"},
        timeout=10,
    )
    body = login.json()
    assert body.get("status") is True, f"Login failed: {body}"
    return {"Authorization": f"Bearer {body['data']['access_token']}"}


# ── 数据工厂（经 HTTP API 创建，返回响应 JSON 的 body） ──


def create_agent(
    api_session: requests.Session,
    base_url: str,
    headers: dict,
    *,
    name: str | None = None,
    api_key: str = "",
) -> dict:
    """POST /api/ai/agents/create（Batch 1 已迁 DRF 信封），归一化返回 {"id": int}。"""
    resp = api_session.post(
        f"{base_url}{AGENT_CREATE_URL}",
        json={"name": name or _unique("测试智能体"), "api_key": api_key},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, f"create agent failed: {resp.status_code} {resp.text}"
    body = resp.json()
    assert body.get("status") is True
    return {"id": body["data"]["id"]}


def create_conversation(
    api_session: requests.Session,
    base_url: str,
    headers: dict,
    agent_id: int,
    *,
    title: str | None = None,
) -> dict:
    """POST /api/ai/agents/{id}/conversations/create（Batch 2 已迁 DRF 信封），
    归一化返回 {"id": int, "agent_scope_session_id": str}。"""
    resp = api_session.post(
        f"{base_url}{CONVERSATION_CREATE_URL.format(agent_id=agent_id)}",
        json={"title": title or _unique("测试对话")},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, f"create conversation failed: {resp.status_code} {resp.text}"
    body = resp.json()
    assert body.get("status") is True
    return {
        "id": body["data"]["id"],
        "agent_scope_session_id": body["data"].get("agent_scope_session_id", ""),
    }


def create_shared_tool(
    api_session: requests.Session,
    base_url: str,
    headers: dict,
    *,
    name: str | None = None,
) -> dict:
    """POST /api/ai/toolbox/create（Batch 3 已迁 DRF 信封），归一化返回 {"id": int}。"""
    resp = api_session.post(
        f"{base_url}{TOOLBOX_CREATE_URL}",
        json={"name": name or _unique("shared_mcp"), "item_type": "mcp", "config_json": "{}"},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, f"create shared tool failed: {resp.status_code} {resp.text}"
    body = resp.json()
    assert body.get("status") is True
    return {"id": body["data"]["id"]}


def import_tool(
    api_session: requests.Session,
    base_url: str,
    headers: dict,
    agent_id: int,
    *,
    name: str | None = None,
) -> dict:
    """经工具箱创建共享 MCP 并导入智能体，归一化返回 {"id": int}（per-agent AITool）。"""
    shared = create_shared_tool(api_session, base_url, headers, name=name)
    resp = api_session.post(
        f"{base_url}{IMPORT_FROM_TOOLBOX_URL.format(agent_id=agent_id)}",
        json={"toolbox_item_id": shared["id"]},
        headers=headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, f"import tool failed: {resp.status_code} {resp.text}"
    body = resp.json()
    assert body.get("status") is True
    return {"id": body["data"]["id"]}
