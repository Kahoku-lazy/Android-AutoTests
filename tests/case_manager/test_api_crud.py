"""API test case CRUD tests — POST/GET/PUT/DELETE /api/cases/api-testing/definitions.

≥10 cases: create, validate, list, detail, update, delete, error paths.
"""

import copy

import allure
import jsonschema
import pytest

from tests.case_manager.conftest import API_DEFS_URL, set_allure_metadata
from tests.case_manager.schemas import (
    API_CREATE_RESPONSE_SCHEMA,
    API_DETAIL_RESPONSE_SCHEMA,
    API_LIST_RESPONSE_SCHEMA,
    ERROR_RESPONSE_SCHEMA,
)

pytestmark = [pytest.mark.api, pytest.mark.case_manager]


# ═══════════════════════════════════════════════════════════════════
# Create tests
# ═══════════════════════════════════════════════════════════════════


@allure.feature("API 用例管理")
@allure.story("创建用例")
def test_create_with_minimal_config(base_url, api_session, auth_headers, sample_config_json):
    """TC-API-001: 创建最小 config_json 用例 → 200, 返回 id"""
    set_allure_metadata(
        "API 用例管理",
        "创建用例",
        "TC-API-001: 创建最小 config_json",
        "完整的 case_info + steps + 空 test_data + validation",
        "critical",
        ("api", "crud", "P0"),
    )
    body = {"case_type": "api_testing", "config_json": sample_config_json}
    resp = api_session.post(f"{base_url}{API_DEFS_URL}", json=body, headers=auth_headers)
    assert resp.status_code == 200, f"Unexpected status: {resp.status_code}"
    data = resp.json()
    jsonschema.validate(data, API_CREATE_RESPONSE_SCHEMA)
    assert len(data["id"]) > 0


@allure.feature("API 用例管理")
@allure.story("创建用例")
def test_create_with_full_config(base_url, api_session, auth_headers, full_config_json):
    """TC-API-002: 创建完整 config_json（schemas + extract + test_data + validation）→ 200"""
    set_allure_metadata(
        "API 用例管理",
        "创建用例",
        "TC-API-002: 完整字段用例创建",
        "4 模块全部填充，含 request_schema/response_schema/extract/test_data/validation",
        "critical",
        ("api", "crud", "P0"),
    )
    body = {"case_type": "api_testing", "config_json": full_config_json}
    resp = api_session.post(f"{base_url}{API_DEFS_URL}", json=body, headers=auth_headers)
    assert resp.status_code == 200, f"Unexpected status: {resp.status_code}"
    data = resp.json()
    jsonschema.validate(data, API_CREATE_RESPONSE_SCHEMA)


@allure.feature("API 用例管理")
@allure.story("创建用例")
def test_create_without_title_returns_400(base_url, api_session, auth_headers, sample_config_json):
    """TC-API-003: case_info.title 为空 → 400"""
    set_allure_metadata(
        "API 用例管理",
        "创建用例",
        "TC-API-003: 标题为空返回 400",
        "config_json.case_info.title = ''",
        "critical",
        ("api", "crud", "P0"),
    )
    cfg = copy.deepcopy(sample_config_json)
    cfg["case_info"]["title"] = ""
    resp = api_session.post(
        f"{base_url}{API_DEFS_URL}",
        json={"case_type": "api_testing", "config_json": cfg},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    jsonschema.validate(resp.json(), ERROR_RESPONSE_SCHEMA)


@allure.feature("API 用例管理")
@allure.story("创建用例")
def test_create_without_steps_returns_400(base_url, api_session, auth_headers, sample_config_json):
    """TC-API-004: config_json.steps 为空 → 400"""
    set_allure_metadata(
        "API 用例管理",
        "创建用例",
        "TC-API-004: 无步骤返回 400",
        "config_json.steps = []",
        "critical",
        ("api", "crud", "P0"),
    )
    cfg = copy.deepcopy(sample_config_json)
    cfg["steps"] = []
    resp = api_session.post(
        f"{base_url}{API_DEFS_URL}",
        json={"case_type": "api_testing", "config_json": cfg},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    jsonschema.validate(resp.json(), ERROR_RESPONSE_SCHEMA)


@allure.feature("API 用例管理")
@allure.story("创建用例")
def test_create_missing_case_info_module(base_url, api_session, auth_headers):
    """TC-API-005: config_json 缺 case_info 模块 → 400"""
    set_allure_metadata(
        "API 用例管理",
        "创建用例",
        "TC-API-005: 缺少 case_info 模块",
        "config_json 只有 steps/test_data/validation，缺 case_info",
        "critical",
        ("api", "crud", "P0"),
    )
    cfg = {
        "steps": [{"url": "/get", "method": "GET", "assert": False}],
        "test_data": [],
        "validation": [],
    }
    resp = api_session.post(
        f"{base_url}{API_DEFS_URL}",
        json={"case_type": "api_testing", "config_json": cfg},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    jsonschema.validate(resp.json(), ERROR_RESPONSE_SCHEMA)


@allure.feature("API 用例管理")
@allure.story("创建用例")
def test_create_invalid_json_body(base_url, api_session, auth_headers):
    """TC-API-006: 非 JSON 请求体 → 400"""
    set_allure_metadata(
        "API 用例管理",
        "创建用例",
        "TC-API-006: 非法 JSON 返回 400",
        "发送纯文本非 JSON",
        "normal",
        ("api", "crud", "P1"),
    )
    resp = api_session.post(
        f"{base_url}{API_DEFS_URL}",
        data="not json at all",
        headers={**auth_headers, "Content-Type": "text/plain"},
    )
    assert resp.status_code == 400
    jsonschema.validate(resp.json(), ERROR_RESPONSE_SCHEMA)


# ═══════════════════════════════════════════════════════════════════
# List / Detail tests
# ═══════════════════════════════════════════════════════════════════


@allure.feature("API 用例管理")
@allure.story("列表查询")
def test_list_definitions(base_url, api_session, auth_headers):
    """TC-API-007: 获取用例列表 → 200, definitions 为数组"""
    set_allure_metadata(
        "API 用例管理",
        "列表查询",
        "TC-API-007: 用例列表",
        "GET /definitions 返回数组，含 config_json",
        "critical",
        ("api", "crud", "P0"),
    )
    resp = api_session.get(f"{base_url}{API_DEFS_URL}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    jsonschema.validate(data, API_LIST_RESPONSE_SCHEMA)


@allure.feature("API 用例管理")
@allure.story("详情查询")
def test_get_single_definition(base_url, api_session, auth_headers, sample_config_json):
    """TC-API-008: 获取单个用例详情 → 200, config_json 完整"""
    set_allure_metadata(
        "API 用例管理",
        "详情查询",
        "TC-API-008: 获取单个用例",
        "创建后 GET /definitions/{id}，config_json 结构完整",
        "critical",
        ("api", "crud", "P0"),
    )
    # Create first
    body = {"case_type": "api_testing", "config_json": sample_config_json}
    created = api_session.post(f"{base_url}{API_DEFS_URL}", json=body, headers=auth_headers).json()
    case_id = created["id"]

    # Read back
    resp = api_session.get(f"{base_url}{API_DEFS_URL}/{case_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    jsonschema.validate(data, API_DETAIL_RESPONSE_SCHEMA)
    # Verify data round-trip
    assert (
        data["definition"]["config_json"]["case_info"]["title"]
        == sample_config_json["case_info"]["title"]
    )


@allure.feature("API 用例管理")
@allure.story("详情查询")
def test_get_nonexistent_returns_404(base_url, api_session, auth_headers):
    """TC-API-009: 查询不存在的用例 → 404"""
    set_allure_metadata(
        "API 用例管理",
        "详情查询",
        "TC-API-009: 不存在的用例返回 404",
        "GET /definitions/NONEXISTENT",
        "normal",
        ("api", "crud", "P1"),
    )
    resp = api_session.get(f"{base_url}{API_DEFS_URL}/NONEXISTENT-ID", headers=auth_headers)
    assert resp.status_code == 404
    jsonschema.validate(resp.json(), ERROR_RESPONSE_SCHEMA)


# ═══════════════════════════════════════════════════════════════════
# Update tests
# ═══════════════════════════════════════════════════════════════════


@allure.feature("API 用例管理")
@allure.story("更新用例")
def test_update_definition(base_url, api_session, auth_headers, sample_config_json):
    """TC-API-010: 更新用例 → 200, 数据变更生效"""
    set_allure_metadata(
        "API 用例管理",
        "更新用例",
        "TC-API-010: 更新用例数据",
        "POST 同 id 更新 config_json，验证新数据生效",
        "critical",
        ("api", "crud", "P0"),
    )
    # Create
    body = {"case_type": "api_testing", "config_json": sample_config_json}
    created = api_session.post(f"{base_url}{API_DEFS_URL}", json=body, headers=auth_headers).json()
    case_id = created["id"]

    # Update — change title + description
    import uuid as _uuid

    new_title = f"Updated {_uuid.uuid4().hex[:6]}"
    updated_cfg = copy.deepcopy(sample_config_json)
    updated_cfg["case_info"]["title"] = new_title
    updated_cfg["case_info"]["description"] = "Updated description"
    resp = api_session.post(
        f"{base_url}{API_DEFS_URL}",
        json={"id": case_id, "case_type": "api_testing", "config_json": updated_cfg},
        headers=auth_headers,
    )
    assert resp.status_code == 200, f"Update failed with {resp.status_code}: {resp.json()}"

    # Verify
    detail = api_session.get(f"{base_url}{API_DEFS_URL}/{case_id}", headers=auth_headers).json()
    assert detail["definition"]["title"] == new_title
    assert detail["definition"]["config_json"]["case_info"]["title"] == new_title


# ═══════════════════════════════════════════════════════════════════
# Delete test
# ═══════════════════════════════════════════════════════════════════


@allure.feature("API 用例管理")
@allure.story("删除用例")
def test_delete_definition(base_url, api_session, auth_headers, sample_config_json):
    """TC-API-011: 删除用例 → 200, 再查返回 404"""
    set_allure_metadata(
        "API 用例管理",
        "删除用例",
        "TC-API-011: 删除用例",
        "DELETE /definitions/{id} 后 GET 返回 404",
        "critical",
        ("api", "crud", "P0"),
    )
    # Create
    body = {"case_type": "api_testing", "config_json": sample_config_json}
    created = api_session.post(f"{base_url}{API_DEFS_URL}", json=body, headers=auth_headers).json()
    case_id = created["id"]

    # Delete
    resp = api_session.delete(f"{base_url}{API_DEFS_URL}/{case_id}", headers=auth_headers)
    assert resp.status_code == 200

    # Verify gone
    resp2 = api_session.get(f"{base_url}{API_DEFS_URL}/{case_id}", headers=auth_headers)
    assert resp2.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# Auth test
# ═══════════════════════════════════════════════════════════════════


@allure.feature("API 用例管理")
@allure.story("鉴权")
def test_create_without_token_returns_401(base_url, api_session, sample_config_json):
    """TC-API-012: 无 Token 创建 → 401"""
    set_allure_metadata(
        "API 用例管理",
        "鉴权",
        "TC-API-012: 无 Token 返回 401",
        "POST 不带 Authorization header",
        "critical",
        ("api", "auth", "P0"),
    )
    body = {"case_type": "api_testing", "config_json": sample_config_json}
    resp = api_session.post(f"{base_url}{API_DEFS_URL}", json=body)
    assert resp.status_code == 401
