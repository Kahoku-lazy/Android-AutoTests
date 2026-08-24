"""Toolbox / Knowledge / Uploads / Agent 工具管理组接口测试（live-server）。

覆盖端点：toolbox 6 + knowledge 3 + uploads 2 + agent tools 7。
断言当前实现契约；Batch 3 迁移 DRF 时同步改为 {status, data} 信封
（已信封的端点：knowledge、upload-file、agent tools list 保持 data 形状不变）。

运行：pytest tests/ai_assistant/test_toolbox_knowledge_api.py -v
"""

import base64
import json

import allure
import pytest
import requests

from tests.ai_assistant.conftest import (
    AGENT_TOOLS_URL,
    IMPORT_FROM_TOOLBOX_URL,
    KB_ADD_DOC_URL,
    KB_DOCUMENTS_URL,
    KB_STATUS_URL,
    TIMEOUT,
    TOOL_DELETE_URL,
    TOOL_TOGGLE_URL,
    TOOLBOX_CREATE_URL,
    TOOLBOX_DELETE_URL,
    TOOLBOX_UPDATE_URL,
    TOOLBOX_UPLOAD_SKILL_URL,
    TOOLBOX_URL,
    UPLOAD_AVATAR_URL,
    UPLOAD_FILE_URL,
    create_agent,
    create_shared_tool,
    import_tool,
)

pytestmark = [pytest.mark.api, pytest.mark.ai_assistant]


# ═══════════════════════════════════════════════════════════════════
# Toolbox（共享工具箱）
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("AI 工具箱")
def test_toolbox_list_success(base_url, api_session, auth_headers):
    """列表 → 200 {status, items:[{id,name,item_type,description,config_json,created_at}]}。"""
    created = create_shared_tool(api_session, base_url, auth_headers)
    resp = api_session.get(f"{base_url}{TOOLBOX_URL}", headers=auth_headers, timeout=TIMEOUT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    item = next((i for i in body["data"]["items"] if i["id"] == created["id"]), None)
    assert item is not None
    assert item["item_type"] == "mcp"


@allure.feature("AI 助手")
@allure.story("AI 工具箱")
def test_toolbox_create_success(base_url, api_session, auth_headers):
    """创建 MCP 项 → 200 {status, data:{id}}。"""
    created = create_shared_tool(api_session, base_url, auth_headers)
    assert isinstance(created["id"], int)


@allure.feature("AI 助手")
@allure.story("AI 工具箱")
def test_toolbox_create_missing_name_400(base_url, api_session, auth_headers):
    """缺 name → 400。"""
    resp = api_session.post(
        f"{base_url}{TOOLBOX_CREATE_URL}",
        json={"item_type": "mcp"},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 400


@allure.feature("AI 助手")
@allure.story("AI 工具箱")
def test_toolbox_create_bad_item_type_400(base_url, api_session, auth_headers):
    """item_type 非法 → 400。"""
    resp = api_session.post(
        f"{base_url}{TOOLBOX_CREATE_URL}",
        json={"name": "x", "item_type": "skill"},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 400


@allure.feature("AI 助手")
@allure.story("AI 工具箱")
def test_toolbox_update_success(base_url, api_session, auth_headers):
    """更新 → 200 {status}；列表可见新名称。"""
    created = create_shared_tool(api_session, base_url, auth_headers)
    resp = api_session.post(
        f"{base_url}{TOOLBOX_UPDATE_URL.format(item_id=created['id'])}",
        json={"name": "改名共享"},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] is True
    listing = api_session.get(
        f"{base_url}{TOOLBOX_URL}", headers=auth_headers, timeout=TIMEOUT
    ).json()
    item = next(i for i in listing["data"]["items"] if i["id"] == created["id"])
    assert item["name"] == "改名共享"


@allure.feature("AI 助手")
@allure.story("AI 工具箱")
def test_toolbox_update_404(base_url, api_session, auth_headers):
    """不存在的项 → 404。"""
    resp = api_session.post(
        f"{base_url}{TOOLBOX_UPDATE_URL.format(item_id=999999999)}",
        json={"name": "x"},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 404


@allure.feature("AI 助手")
@allure.story("AI 工具箱")
def test_toolbox_delete_success(base_url, api_session, auth_headers):
    """删除 → 200 {status}；列表不再可见。"""
    created = create_shared_tool(api_session, base_url, auth_headers)
    resp = api_session.post(
        f"{base_url}{TOOLBOX_DELETE_URL.format(item_id=created['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] is True
    listing = api_session.get(
        f"{base_url}{TOOLBOX_URL}", headers=auth_headers, timeout=TIMEOUT
    ).json()
    assert all(i["id"] != created["id"] for i in listing["data"]["items"])


@allure.feature("AI 助手")
@allure.story("AI 工具箱")
def test_toolbox_upload_skill_no_files_400(base_url, api_session, auth_headers):
    """上传共享 skill 缺文件 → 400。"""
    resp = api_session.post(
        f"{base_url}{TOOLBOX_UPLOAD_SKILL_URL}", headers=auth_headers, timeout=TIMEOUT
    )
    assert resp.status_code == 400


@allure.feature("AI 助手")
@allure.story("AI 工具箱")
def test_import_from_toolbox_success(base_url, api_session, auth_headers):
    """导入共享项到 Agent → 200 {status, id}；Agent 工具列表可见。"""
    agent = create_agent(api_session, base_url, auth_headers)
    shared = create_shared_tool(api_session, base_url, auth_headers)
    resp = api_session.post(
        f"{base_url}{IMPORT_FROM_TOOLBOX_URL.format(agent_id=agent['id'])}",
        json={"toolbox_item_id": shared["id"]},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    tools = api_session.get(
        f"{base_url}{AGENT_TOOLS_URL.format(agent_id=agent['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    ).json()
    assert any(t["id"] == body["data"]["id"] for t in tools["data"]["mcp"])


@allure.feature("AI 助手")
@allure.story("AI 工具箱")
def test_import_from_toolbox_duplicate_409(base_url, api_session, auth_headers):
    """重复导入同名 → 409。"""
    agent = create_agent(api_session, base_url, auth_headers)
    shared = create_shared_tool(api_session, base_url, auth_headers)
    url = f"{base_url}{IMPORT_FROM_TOOLBOX_URL.format(agent_id=agent['id'])}"
    payload = json.dumps({"toolbox_item_id": shared["id"]})
    first = api_session.post(url, data=payload, headers=auth_headers, timeout=TIMEOUT)
    assert first.status_code == 200
    second = api_session.post(url, data=payload, headers=auth_headers, timeout=TIMEOUT)
    assert second.status_code == 409


@allure.feature("AI 助手")
@allure.story("AI 工具箱")
def test_import_from_toolbox_404(base_url, api_session, auth_headers):
    """共享项不存在 → 404。"""
    agent = create_agent(api_session, base_url, auth_headers)
    resp = api_session.post(
        f"{base_url}{IMPORT_FROM_TOOLBOX_URL.format(agent_id=agent['id'])}",
        json={"toolbox_item_id": 999999999},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# Knowledge（知识库；已信封 {status, data}）
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("知识库")
def test_kb_status_success(base_url, api_session, auth_headers):
    """状态 → 200 {status, data:{doc_count, db_size_mb, reindex:{...}}}。"""
    resp = api_session.get(f"{base_url}{KB_STATUS_URL}", headers=auth_headers, timeout=TIMEOUT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert "doc_count" in body["data"]
    assert "reindex" in body["data"]


@allure.feature("AI 助手")
@allure.story("知识库")
def test_kb_documents_success(base_url, api_session, auth_headers):
    """文档列表 → 200 {status, data:{documents, total}}。"""
    resp = api_session.get(f"{base_url}{KB_DOCUMENTS_URL}", headers=auth_headers, timeout=TIMEOUT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    data = body["data"]
    assert isinstance(data["documents"], list)
    assert data["total"] == len(data["documents"])


@allure.feature("AI 助手")
@allure.story("知识库")
def test_kb_add_document_empty_400(base_url, api_session, auth_headers):
    """内容为空 → 400（不触发索引写入）。"""
    resp = api_session.post(
        f"{base_url}{KB_ADD_DOC_URL}",
        json={},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 400
    assert resp.json()["status"] is False


# ═══════════════════════════════════════════════════════════════════
# Uploads（上传）
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("文件上传")
def test_upload_avatar_success(base_url, api_session, auth_headers):
    """上传 base64 头像 → 200 {status, url}（data URI）。"""
    img_b64 = base64.b64encode(b"fake-png-bytes").decode()
    resp = api_session.post(
        f"{base_url}{UPLOAD_AVATAR_URL}",
        json={"image": img_b64},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert body["data"]["url"].startswith("data:image/png;base64,")


@allure.feature("AI 助手")
@allure.story("文件上传")
def test_upload_file_missing_file_400(base_url, api_session, auth_headers):
    """缺文件 → 400。"""
    resp = api_session.post(f"{base_url}{UPLOAD_FILE_URL}", headers=auth_headers, timeout=TIMEOUT)
    assert resp.status_code == 400
    assert resp.json()["status"] is False


@allure.feature("AI 助手")
@allure.story("文件上传")
def test_upload_file_txt_success(base_url, auth_headers):
    """上传 txt → 200 {status, data:{filename,type,content,preview,...}}（已信封）。"""
    resp = requests.post(
        f"{base_url}{UPLOAD_FILE_URL}",
        files={"file": ("note.txt", b"hello world", "text/plain")},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    data = body["data"]
    assert data["type"] == "txt"
    assert data["content"] == "hello world"
    assert data["preview"] == "hello world"


# ═══════════════════════════════════════════════════════════════════
# Agent 工具管理（MCP / Skill）
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("Agent 工具")
def test_agent_tools_list_success(base_url, api_session, auth_headers):
    """工具列表 → 200 {status, data:{mcp, skills}}（已信封）。"""
    agent = create_agent(api_session, base_url, auth_headers)
    saved = import_tool(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.get(
        f"{base_url}{AGENT_TOOLS_URL.format(agent_id=agent['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert any(t["id"] == saved["id"] for t in body["data"]["mcp"])
    assert isinstance(body["data"]["skills"], list)


@allure.feature("AI 助手")
@allure.story("Agent 工具")
def test_agent_tools_list_403_other_user(base_url, api_session, auth_headers, other_auth_headers):
    """非所有者 → 403。"""
    agent = create_agent(api_session, base_url, auth_headers)
    resp = api_session.get(
        f"{base_url}{AGENT_TOOLS_URL.format(agent_id=agent['id'])}",
        headers=other_auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 403


@allure.feature("AI 助手")
@allure.story("Agent 工具")
def test_toggle_tool_success(base_url, api_session, auth_headers):
    """禁用工具 → 200 {status, enabled:false}；列表可见 enabled=false。"""
    agent = create_agent(api_session, base_url, auth_headers)
    saved = import_tool(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.post(
        f"{base_url}{TOOL_TOGGLE_URL.format(agent_id=agent['id'], tool_id=saved['id'])}",
        json={"enabled": False},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert body["data"]["enabled"] is False
    tools = api_session.get(
        f"{base_url}{AGENT_TOOLS_URL.format(agent_id=agent['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    ).json()
    item = next(t for t in tools["data"]["mcp"] if t["id"] == saved["id"])
    assert item["enabled"] is False


@allure.feature("AI 助手")
@allure.story("Agent 工具")
def test_toggle_tool_404(base_url, api_session, auth_headers):
    """工具不存在 → 404。"""
    agent = create_agent(api_session, base_url, auth_headers)
    resp = api_session.post(
        f"{base_url}{TOOL_TOGGLE_URL.format(agent_id=agent['id'], tool_id=999999999)}",
        json={"enabled": False},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 404


@allure.feature("AI 助手")
@allure.story("Agent 工具")
def test_delete_tool_success(base_url, api_session, auth_headers):
    """删除工具 → 200 {status}；列表不再可见。"""
    agent = create_agent(api_session, base_url, auth_headers)
    saved = import_tool(api_session, base_url, auth_headers, agent["id"])
    resp = api_session.post(
        f"{base_url}{TOOL_DELETE_URL.format(agent_id=agent['id'], tool_id=saved['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] is True
    tools = api_session.get(
        f"{base_url}{AGENT_TOOLS_URL.format(agent_id=agent['id'])}",
        headers=auth_headers,
        timeout=TIMEOUT,
    ).json()
    assert all(t["id"] != saved["id"] for t in tools["data"]["mcp"])


@allure.feature("AI 助手")
@allure.story("Agent 工具")
def test_delete_tool_404(base_url, api_session, auth_headers):
    """工具不存在 → 404。"""
    agent = create_agent(api_session, base_url, auth_headers)
    resp = api_session.post(
        f"{base_url}{TOOL_DELETE_URL.format(agent_id=agent['id'], tool_id=999999999)}",
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 404
