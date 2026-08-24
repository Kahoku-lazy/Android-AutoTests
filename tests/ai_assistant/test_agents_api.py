"""Agent 组接口测试（live-server）— 鉴权 / 列表 / CRUD / reveal-key / health / 模型检测。

覆盖端点：/api/ai/agents*（Batch 1 已迁移 DRF）+ /api/ai/models/detect + available-tools/skills。
断言 DRF 信封：成功 {status:true, data:{...}}，失败 {status:false, message}。
行为契约（Batch 0 实测锁定）：权限检查先于存在性检查 → 不存在资源返回 403。

运行：pytest tests/ai_assistant/test_agents_api.py -v
"""

import allure
import pytest

from tests.ai_assistant.conftest import (
    AGENT_CREATE_URL,
    AGENT_DELETE_URL,
    AGENT_DETAIL_URL,
    AGENT_HEALTH_URL,
    AGENT_MODELS_URL,
    AGENT_REVEAL_KEY_URL,
    AGENT_TEST_URL,
    AGENT_UPDATE_URL,
    AGENTS_URL,
    AVAILABLE_SKILLS_URL,
    AVAILABLE_TOOLS_URL,
    MODELS_DETECT_URL,
    TIMEOUT,
    create_agent,
)

pytestmark = [pytest.mark.api, pytest.mark.ai_assistant]


# ═══════════════════════════════════════════════════════════════════
# 鉴权
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("Agent 列表")
def test_list_agents_unauthenticated_401(base_url, api_session):
    """未携带 token → JWT 中间件 401。"""
    resp = api_session.get(f"{base_url}{AGENTS_URL}", timeout=TIMEOUT)
    assert resp.status_code == 401
    assert resp.json()["status"] is False


# ═══════════════════════════════════════════════════════════════════
# 列表
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("Agent 列表")
def test_list_agents_scoped_to_owner(base_url, api_session, auth_headers, other_auth_headers):
    """列表只含当前用户的 Agent（{status, data:{agents}}）。"""
    mine = create_agent(api_session, base_url, auth_headers)
    theirs = create_agent(api_session, base_url, other_auth_headers)

    resp = api_session.get(f"{base_url}{AGENTS_URL}", headers=auth_headers, timeout=TIMEOUT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    ids = [a["id"] for a in body["data"]["agents"]]
    assert mine["id"] in ids
    assert theirs["id"] not in ids


# ═══════════════════════════════════════════════════════════════════
# 创建
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("Agent 创建")
def test_create_agent_success(base_url, api_session, auth_headers):
    """创建 Agent → 200 {status, data:{id}}。"""
    created = create_agent(api_session, base_url, auth_headers, name="新智能体")
    assert isinstance(created["id"], int)


@allure.feature("AI 助手")
@allure.story("Agent 创建")
def test_create_agent_missing_name_400(base_url, api_session, auth_headers):
    """name 为空 → 400 {status:false, message}。"""
    resp = api_session.post(
        f"{base_url}{AGENT_CREATE_URL}",
        json={"name": "  "},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 400
    assert resp.json()["status"] is False
    assert "message" in resp.json()


@allure.feature("AI 助手")
@allure.story("Agent 创建")
def test_create_agent_invalid_provider_400(base_url, api_session, auth_headers):
    """不支持的 model_provider → 400。"""
    resp = api_session.post(
        f"{base_url}{AGENT_CREATE_URL}",
        json={"name": "x", "model_provider": "notexist"},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 400
    assert resp.json()["status"] is False


@allure.feature("AI 助手")
@allure.story("Agent 创建")
def test_create_agent_bad_json_400(base_url, api_session, auth_headers):
    """非法 JSON → 400（DRF 解析器兜底，旧实现为 400"无效的 JSON"）。"""
    resp = api_session.post(
        f"{base_url}{AGENT_CREATE_URL}",
        data="{bad",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 400
    assert resp.json()["status"] is False


# ═══════════════════════════════════════════════════════════════════
# 详情
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("Agent 详情")
def test_agent_detail_success(base_url, api_session, auth_headers):
    """详情 → 200 {status, data:{agent}}，api_key 脱敏。"""
    created = create_agent(api_session, base_url, auth_headers, api_key="sk-test-key-12345678")
    resp = api_session.get(
        f"{base_url}{AGENT_DETAIL_URL.format(agent_id=created['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    agent = body["data"]["agent"]
    assert agent["id"] == created["id"]
    assert "***" in agent["api_key"]  # 脱敏
    assert "sk-test-key-12345678" not in agent["api_key"]
    for key in ("model_provider", "model_name", "status", "tools"):
        assert key in agent


@allure.feature("AI 助手")
@allure.story("Agent 详情")
def test_agent_detail_403_nonexistent(base_url, api_session, auth_headers):
    """不存在的 id → 403（权限检查先于存在性检查，不泄露资源存在性）。"""
    resp = api_session.get(
        f"{base_url}{AGENT_DETAIL_URL.format(agent_id=999999999)}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403
    assert resp.json()["status"] is False


@allure.feature("AI 助手")
@allure.story("Agent 详情")
def test_agent_detail_403_other_user(base_url, api_session, auth_headers, other_auth_headers):
    """非所有者 → 403。"""
    created = create_agent(api_session, base_url, auth_headers)
    resp = api_session.get(
        f"{base_url}{AGENT_DETAIL_URL.format(agent_id=created['id'])}",
        headers=other_auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403
    assert resp.json()["status"] is False


# ═══════════════════════════════════════════════════════════════════
# 更新
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("Agent 更新")
def test_update_agent_success(base_url, api_session, auth_headers):
    """更新名称 → 200 {status, data:{id}}。"""
    created = create_agent(api_session, base_url, auth_headers)
    resp = api_session.post(
        f"{base_url}{AGENT_UPDATE_URL.format(agent_id=created['id'])}",
        json={"name": "改名智能体"},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] is True
    detail = api_session.get(
        f"{base_url}{AGENT_DETAIL_URL.format(agent_id=created['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    ).json()
    assert detail["data"]["agent"]["name"] == "改名智能体"


@allure.feature("AI 助手")
@allure.story("Agent 更新")
def test_update_agent_masked_key_skipped(base_url, api_session, auth_headers):
    """前端传脱敏 Key（含 ***）→ 跳过更新，真实 Key 不变（用 reveal-key 验证）。"""
    created = create_agent(api_session, base_url, auth_headers, api_key="sk-test-key-12345678")
    resp = api_session.post(
        f"{base_url}{AGENT_UPDATE_URL.format(agent_id=created['id'])}",
        json={"name": "不改名", "api_key": "sk-***abcd"},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    reveal = api_session.post(
        f"{base_url}{AGENT_REVEAL_KEY_URL.format(agent_id=created['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    ).json()
    assert reveal["data"]["api_key"] == "sk-test-key-12345678"


@allure.feature("AI 助手")
@allure.story("Agent 更新")
def test_update_agent_403_other_user(base_url, api_session, auth_headers, other_auth_headers):
    """非所有者更新 → 403。"""
    created = create_agent(api_session, base_url, auth_headers)
    resp = api_session.post(
        f"{base_url}{AGENT_UPDATE_URL.format(agent_id=created['id'])}",
        json={"name": "hack"},
        headers=other_auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════
# 删除
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("Agent 删除")
def test_delete_agent_success(base_url, api_session, auth_headers):
    """删除 → 200 {status, data:{}}；随后详情 403（权限检查先于存在性检查）。"""
    created = create_agent(api_session, base_url, auth_headers)
    resp = api_session.post(
        f"{base_url}{AGENT_DELETE_URL.format(agent_id=created['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] is True
    detail = api_session.get(
        f"{base_url}{AGENT_DETAIL_URL.format(agent_id=created['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert detail.status_code == 403


@allure.feature("AI 助手")
@allure.story("Agent 删除")
def test_delete_agent_403_nonexistent(base_url, api_session, auth_headers):
    """不存在的 id → 403（权限检查先于存在性检查）。"""
    resp = api_session.post(
        f"{base_url}{AGENT_DELETE_URL.format(agent_id=999999999)}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


@allure.feature("AI 助手")
@allure.story("Agent 删除")
def test_delete_agent_403_other_user(base_url, api_session, auth_headers, other_auth_headers):
    """非所有者删除 → 403。"""
    created = create_agent(api_session, base_url, auth_headers)
    resp = api_session.post(
        f"{base_url}{AGENT_DELETE_URL.format(agent_id=created['id'])}",
        headers=other_auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════
# reveal-key（一次性查看）
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("API Key 一次性查看")
def test_reveal_key_first_time(base_url, api_session, auth_headers):
    """首次查看 → 200 返回明文 Key + revealed=True。"""
    created = create_agent(api_session, base_url, auth_headers, api_key="sk-test-key-12345678")
    resp = api_session.post(
        f"{base_url}{AGENT_REVEAL_KEY_URL.format(agent_id=created['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["revealed"] is True
    assert data["api_key"] == "sk-test-key-12345678"


@allure.feature("AI 助手")
@allure.story("API Key 一次性查看")
def test_reveal_key_second_time_masked(base_url, api_session, auth_headers):
    """二次查看 → 200 返回脱敏 Key + revealed=False。"""
    created = create_agent(api_session, base_url, auth_headers, api_key="sk-test-key-12345678")
    url = f"{base_url}{AGENT_REVEAL_KEY_URL.format(agent_id=created['id'])}"
    first = api_session.post(url, headers=auth_headers, timeout=TIMEOUT)
    assert first.status_code == 200
    second = api_session.post(url, headers=auth_headers, timeout=TIMEOUT)
    assert second.status_code == 200
    data = second.json()["data"]
    assert data["revealed"] is False
    assert "***" in data["api_key"]


@allure.feature("AI 助手")
@allure.story("API Key 一次性查看")
def test_reveal_key_no_key_400(base_url, api_session, auth_headers):
    """未配置 Key → 400。"""
    created = create_agent(api_session, base_url, auth_headers, api_key="")
    resp = api_session.post(
        f"{base_url}{AGENT_REVEAL_KEY_URL.format(agent_id=created['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════
# health / models / available-*
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("健康检查")
def test_health_check_shape_no_network(base_url, api_session, auth_headers):
    """无 Key 的 Agent 跳过外部探测 → 200 {status, data:{agents:[...]}}。"""
    created = create_agent(api_session, base_url, auth_headers, api_key="")
    resp = api_session.get(f"{base_url}{AGENT_HEALTH_URL}", headers=auth_headers, timeout=TIMEOUT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    item = next((a for a in body["data"]["agents"] if a["id"] == created["id"]), None)
    assert item is not None
    assert item["is_connected"] is False
    assert "name" in item and "last_checked" in item


@allure.feature("AI 助手")
@allure.story("模型列表")
def test_agent_models_get_success(base_url, api_session, auth_headers):
    """GET /agents/{id}/models 读缓存 → 200 {status, data:{models, is_connected, last_checked}}。"""
    created = create_agent(api_session, base_url, auth_headers)
    resp = api_session.get(
        f"{base_url}{AGENT_MODELS_URL.format(agent_id=created['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["models"] == []
    assert "is_connected" in data and "last_checked" in data


@allure.feature("AI 助手")
@allure.story("模型列表")
def test_agent_models_get_404(base_url, api_session, auth_headers):
    """不存在的 agent → 404。"""
    resp = api_session.get(
        f"{base_url}{AGENT_MODELS_URL.format(agent_id=999999999)}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 404


@allure.feature("AI 助手")
@allure.story("连接测试")
def test_agent_test_403_nonexistent(base_url, api_session, auth_headers):
    """连接测试对不存在 agent → 403（不发起外部网络调用）。"""
    resp = api_session.post(
        f"{base_url}{AGENT_TEST_URL.format(agent_id=999999999)}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


@allure.feature("AI 助手")
@allure.story("连接测试")
def test_agent_test_403_other_user(base_url, api_session, auth_headers, other_auth_headers):
    """连接测试非所有者 → 403。"""
    created = create_agent(api_session, base_url, auth_headers)
    resp = api_session.post(
        f"{base_url}{AGENT_TEST_URL.format(agent_id=created['id'])}",
        headers=other_auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


@allure.feature("AI 助手")
@allure.story("模型检测")
def test_models_detect_missing_api_key_400(base_url, api_session, auth_headers):
    """模型检测缺 api_key → 400（不发起外部网络调用）。"""
    resp = api_session.post(
        f"{base_url}{MODELS_DETECT_URL}",
        json={"model_provider": "dashscope"},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 400
    assert resp.json()["status"] is False


@allure.feature("AI 助手")
@allure.story("平台工具")
def test_available_tools_shape(base_url, api_session, auth_headers):
    """平台工具列表 → 200 {status, data:{categories:[...]}}。"""
    resp = api_session.get(
        f"{base_url}{AVAILABLE_TOOLS_URL}", headers=auth_headers, timeout=TIMEOUT
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert isinstance(body["data"]["categories"], list)


@allure.feature("AI 助手")
@allure.story("平台技能")
def test_available_skills_shape(base_url, api_session, auth_headers):
    """workspace 技能列表 → 200 {status, data:{skills:[...]}}。"""
    resp = api_session.get(
        f"{base_url}{AVAILABLE_SKILLS_URL}", headers=auth_headers, timeout=TIMEOUT
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert isinstance(body["data"]["skills"], list)


# ═══════════════════════════════════════════════════════════════════
# 中间件身份注入（DRF 视图依赖 request.user_id 等价物）
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("Agent 创建")
def test_create_agent_records_other_user_owner(base_url, api_session, other_auth_headers):
    """其他用户 token 创建 Agent 后，创建者本人可读（owner 隔离生效）。"""
    created = create_agent(api_session, base_url, other_auth_headers)
    detail = api_session.get(
        f"{base_url}{AGENT_DETAIL_URL.format(agent_id=created['id'])}",
        headers=other_auth_headers,
        timeout=TIMEOUT,
    )
    assert detail.status_code == 200
    assert detail.json()["data"]["agent"]["id"] == created["id"]
