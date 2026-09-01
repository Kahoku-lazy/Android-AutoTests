"""Toolbox / Knowledge / Uploads / 平台配置 组接口测试（live-server）。

覆盖端点：toolbox（含 toggle）+ knowledge 3 + uploads 2 + platform-config 2。
断言当前实现契约；DRF 统一 {status, data} 信封。

运行：pytest tests/ai_assistant/test_toolbox_knowledge_api.py -v
"""

import base64

import allure
import pytest
import requests

from tests.ai_assistant.conftest import (
    KB_ADD_DOC_URL,
    KB_DOCUMENTS_URL,
    KB_STATUS_URL,
    PLATFORM_CONFIG_UPDATE_URL,
    PLATFORM_CONFIG_URL,
    TIMEOUT,
    TOOLBOX_CREATE_URL,
    TOOLBOX_DELETE_URL,
    TOOLBOX_TOGGLE_URL,
    TOOLBOX_UPDATE_URL,
    TOOLBOX_UPLOAD_SKILL_URL,
    TOOLBOX_URL,
    UPLOAD_AVATAR_URL,
    UPLOAD_FILE_URL,
    create_shared_tool,
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
def test_toolbox_toggle_success(base_url, api_session, auth_headers):
    """启停共享项 → 200 {status, enabled}；列表含 enabled 状态。"""
    shared = create_shared_tool(api_session, base_url, auth_headers)
    resp = api_session.post(
        f"{base_url}{TOOLBOX_TOGGLE_URL.format(item_id=shared['id'])}",
        json={"enabled": False},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert body["data"]["enabled"] is False
    listing = api_session.get(
        f"{base_url}{TOOLBOX_URL}", headers=auth_headers, timeout=TIMEOUT
    ).json()
    item = next(i for i in listing["data"]["items"] if i["id"] == shared["id"])
    assert item["enabled"] is False


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
# 平台配置（平台唯一智能体的工具/知识库配置）
# ═══════════════════════════════════════════════════════════════════


@allure.feature("AI 助手")
@allure.story("平台配置")
def test_platform_config_read(base_url, api_session, auth_headers):
    """读取平台唯一智能体配置 → 200 {status, data:{...}}。"""
    resp = api_session.get(
        f"{base_url}{PLATFORM_CONFIG_URL}", headers=auth_headers, timeout=TIMEOUT
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    data = body["data"]
    assert "enable_business_tools" in data
    assert isinstance(data["knowledge_sources"], dict)
    assert isinstance(data["skills_config"], dict)


@allure.feature("AI 助手")
@allure.story("平台配置")
def test_platform_config_update(base_url, api_session, auth_headers):
    """更新平台智能体配置 → 200；读回值一致并还原。"""
    before = api_session.get(
        f"{base_url}{PLATFORM_CONFIG_URL}", headers=auth_headers, timeout=TIMEOUT
    ).json()["data"]
    original = bool(before.get("enable_workspace_tools", False))
    target = not original
    resp = api_session.post(
        f"{base_url}{PLATFORM_CONFIG_UPDATE_URL}",
        json={"enable_workspace_tools": target},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["enable_workspace_tools"] is target
    # 还原
    api_session.post(
        f"{base_url}{PLATFORM_CONFIG_UPDATE_URL}",
        json={"enable_workspace_tools": original},
        headers=auth_headers,
        timeout=TIMEOUT,
    )
