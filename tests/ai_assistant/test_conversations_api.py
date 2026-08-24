"""对话/消息/任务组接口测试（live-server）— conversations / messages / HITL / tasks。

覆盖端点：conversations 6 + messages 2 + confirm-result 1 + tasks 3。
断言当前实现契约（平铺信封）；Batch 2 迁移 DRF 时同步改为 {status, data} 信封。

运行：pytest tests/ai_assistant/test_conversations_api.py -v
"""

import allure
import pytest

from tests.ai_assistant.conftest import (
    AI_TASKS_URL,
    CONFIRM_RESULT_URL,
    CONV_TASK_DETAIL_URL,
    CONV_TASKS_URL,
    CONVERSATION_CREATE_URL,
    CONVERSATIONS_URL,
    DELETE_CONVERSATION_URL,
    MESSAGES_URL,
    RENAME_URL,
    SAVE_MESSAGE_URL,
    TIMEOUT,
    create_agent,
    create_conversation,
)

pytestmark = [pytest.mark.api, pytest.mark.ai_assistant]


# ═══════════════════════════════════════════════════════════════════
# 对话列表 / 创建
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("对话列表")
def test_list_conversations_success(base_url, api_session, auth_headers):
    """列表 → 200 {status, conversations:[{id,title,status,agent_scope_session_id,created_at}]}。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.get(
        f"{base_url}{CONVERSATIONS_URL.format(agent_id=agent['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    item = next((c for c in body["data"]["conversations"] if c["id"] == conv["id"]), None)
    assert item is not None
    assert item["status"] == "active"
    assert "title" in item and "agent_scope_session_id" in item and "created_at" in item


@allure.feature("AI 助手")
@allure.story("对话列表")
def test_list_conversations_403_other_agent(
    base_url, api_session, auth_headers, other_auth_headers
):
    """他人的 Agent → 403。"""
    theirs = create_agent(api_session, base_url, other_auth_headers)
    resp = api_session.get(
        f"{base_url}{CONVERSATIONS_URL.format(agent_id=theirs['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


@allure.feature("AI 助手")
@allure.story("对话创建")
def test_create_conversation_success(base_url, api_session, auth_headers):
    """创建 → 200 {status, data:{id, agent_scope_session_id}}。"""
    agent = create_agent(api_session, base_url, auth_headers)
    body = create_conversation(api_session, base_url, auth_headers, agent["id"], title="新对话")
    assert isinstance(body["id"], int)
    assert "agent_scope_session_id" in body


@allure.feature("AI 助手")
@allure.story("对话创建")
def test_create_conversation_403_other_agent(
    base_url, api_session, auth_headers, other_auth_headers
):
    """在他人 Agent 下创建 → 403。"""
    theirs = create_agent(api_session, base_url, other_auth_headers)
    resp = api_session.post(
        f"{base_url}{CONVERSATION_CREATE_URL.format(agent_id=theirs['id'])}",
        json={"title": "x"},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════
# 消息
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("消息")
def test_save_and_list_messages(base_url, api_session, auth_headers):
    """保存 user 消息 → 200 {status, id}；列表可见且字段齐全。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    saved = api_session.post(
        f"{base_url}{SAVE_MESSAGE_URL.format(conv_id=conv['id'])}",
        json={"role": "user", "content": "hello"},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert saved.status_code == 200
    saved_body = saved.json()
    assert saved_body["status"] is True

    resp = api_session.get(
        f"{base_url}{MESSAGES_URL.format(conv_id=conv['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    item = next((m for m in body["data"]["messages"] if m["id"] == saved_body["data"]["id"]), None)
    assert item is not None
    assert item["role"] == "user"
    assert item["content"] == "hello"
    assert item["blocks"] == []


@allure.feature("AI 助手")
@allure.story("消息")
def test_list_messages_403_other_user(base_url, api_session, auth_headers, other_auth_headers):
    """非所有者 → 403。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.get(
        f"{base_url}{MESSAGES_URL.format(conv_id=conv['id'])}",
        headers=other_auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


@allure.feature("AI 助手")
@allure.story("消息")
def test_save_message_empty_content_400(base_url, api_session, auth_headers):
    """user 消息 content 与 blocks 均为空 → 400。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.post(
        f"{base_url}{SAVE_MESSAGE_URL.format(conv_id=conv['id'])}",
        json={"role": "user", "content": ""},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 400
    assert resp.json()["status"] is False


@allure.feature("AI 助手")
@allure.story("消息")
def test_save_message_403_other_user(base_url, api_session, auth_headers, other_auth_headers):
    """非所有者保存 → 403。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.post(
        f"{base_url}{SAVE_MESSAGE_URL.format(conv_id=conv['id'])}",
        json={"role": "user", "content": "x"},
        headers=other_auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════
# 重命名 / 删除
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("对话重命名")
def test_rename_conversation_success(base_url, api_session, auth_headers):
    """重命名 → 200 {status, data:{title}}。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.post(
        f"{base_url}{RENAME_URL.format(conv_id=conv['id'])}",
        json={"title": "新标题"},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert body["data"]["title"] == "新标题"


@allure.feature("AI 助手")
@allure.story("对话重命名")
def test_rename_conversation_empty_title_400(base_url, api_session, auth_headers):
    """空标题 → 400。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.post(
        f"{base_url}{RENAME_URL.format(conv_id=conv['id'])}",
        json={"title": "  "},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 400


@allure.feature("AI 助手")
@allure.story("对话重命名")
def test_rename_conversation_403_nonexistent(base_url, api_session, auth_headers):
    """不存在的对话 → 403（权限检查先于存在性检查）。"""
    resp = api_session.post(
        f"{base_url}{RENAME_URL.format(conv_id=999999999)}",
        json={"title": "x"},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


@allure.feature("AI 助手")
@allure.story("对话删除")
def test_delete_conversation_success(base_url, api_session, auth_headers):
    """删除 → 200 {status}；随后消息列表 403（对话已不存在）。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.post(
        f"{base_url}{DELETE_CONVERSATION_URL.format(conv_id=conv['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] is True
    after = api_session.get(
        f"{base_url}{MESSAGES_URL.format(conv_id=conv['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert after.status_code == 403  # check_conversation_access 对已删对话返回 False


@allure.feature("AI 助手")
@allure.story("对话删除")
def test_delete_conversation_403_other_user(
    base_url, api_session, auth_headers, other_auth_headers
):
    """非所有者删除 → 403。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.post(
        f"{base_url}{DELETE_CONVERSATION_URL.format(conv_id=conv['id'])}",
        headers=other_auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════
# HITL 确认
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("HITL 确认")
def test_confirm_result_403_other_user(base_url, api_session, auth_headers, other_auth_headers):
    """非所有者确认 → 403。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.post(
        f"{base_url}{CONFIRM_RESULT_URL.format(conv_id=conv['id'])}",
        json={"reply_id": "r1", "confirm_results": []},
        headers=other_auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


@allure.feature("AI 助手")
@allure.story("HITL 确认")
def test_confirm_result_no_active_session_400(base_url, api_session, auth_headers):
    """无活跃 Agent 会话 → 400。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.post(
        f"{base_url}{CONFIRM_RESULT_URL.format(conv_id=conv['id'])}",
        json={"reply_id": "r1", "confirm_results": []},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 400
    assert resp.json()["status"] is False


@allure.feature("AI 助手")
@allure.story("HITL 确认")
def test_confirm_result_403_nonexistent(base_url, api_session, auth_headers):
    """对话不存在 → 403（权限检查先于存在性检查）。"""
    resp = api_session.post(
        f"{base_url}{CONFIRM_RESULT_URL.format(conv_id=999999999)}",
        json={"reply_id": "r1", "confirm_results": []},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════
# 任务历史
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("任务看板")
def test_list_ai_tasks_shape(base_url, api_session, auth_headers):
    """任务看板 → 200 {status, tasks:[...]}。"""
    resp = api_session.get(f"{base_url}{AI_TASKS_URL}", headers=auth_headers, timeout=TIMEOUT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert isinstance(body["data"]["tasks"], list)


@allure.feature("AI 助手")
@allure.story("对话任务")
def test_list_conv_tasks_shape(base_url, api_session, auth_headers):
    """对话任务 → 200 {status, data:{tasks:[...]}}。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.get(
        f"{base_url}{CONV_TASKS_URL.format(conv_id=conv['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert isinstance(body["data"]["tasks"], list)


@allure.feature("AI 助手")
@allure.story("对话任务")
def test_list_conv_tasks_404(base_url, api_session, auth_headers):
    """对话不存在 → 404。"""
    resp = api_session.get(
        f"{base_url}{CONV_TASKS_URL.format(conv_id=999999999)}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 404


@allure.feature("AI 助手")
@allure.story("对话任务")
def test_get_conv_task_404(base_url, api_session, auth_headers):
    """run_id 不存在 → 404。"""
    agent = create_agent(api_session, base_url, auth_headers)
    conv = create_conversation(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.get(
        f"{base_url}{CONV_TASK_DETAIL_URL.format(conv_id=conv['id'], run_id='no-such-run-xyz')}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 404
