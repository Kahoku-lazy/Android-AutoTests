"""注册接口 API 测试 — POST /api/ai/auth/register（数据驱动 + JSON Schema）。

24 条用例按断言 Shape 分为 3 个参数化组 + 2 个独立函数：
  - test_register_validation[15]  — 400/409 + 精确错误消息
  - test_register_success[2]      — 200 + Token + 用户对象
  - test_register_conditional[5]  — 200/409 条件分支
  - test_register_invalid_json    — 400 非 JSON 请求体
  - test_register_oversized       — 1MB 密码不崩溃

运行方式：
    pytest tests/auth/test_register.py -v --alluredir=allure-results
"""

import uuid

from dataclasses import dataclass

import allure
import jsonschema
import pytest

from tests.auth.conftest import REGISTER_URL, set_allure_metadata
from tests.auth.schemas import ERROR_RESPONSE_SCHEMA, REGISTER_SUCCESS_SCHEMA

# ═══════════════════════════════════════════════════════════════════
# 数据类型
# ═══════════════════════════════════════════════════════════════════

UNIQUE_SENTINEL = "__UNIQUE__"
"""payload 中的占位符 — 执行时替换为 uuid 生成的唯一用户名。"""


@dataclass(frozen=True)
class ValidationCase:
    """400/409 校验拒绝用例 — 请求被拒绝，返回 {status:false, message}。"""

    id: str
    title: str
    description: str
    severity: str
    priority: str
    payload: dict
    expected_status: int
    expected_message: str


@dataclass(frozen=True)
class SuccessCase:
    """200 注册成功用例 — 返回 Token 对 + 用户对象。"""

    id: str
    title: str
    description: str
    severity: str
    priority: str
    payload: dict


@dataclass(frozen=True)
class ConditionalCase:
    """200/409 条件用例 — 用户名唯一则成功，已存在则 409。"""

    id: str
    title: str
    description: str
    severity: str
    priority: str
    payload: dict
    extra_tags: tuple[str, ...] = ()


# ── 辅助 ──


def _resolve_payload(payload: dict, unique_username: str = "") -> dict:
    """将 payload 中的 UNIQUE_SENTINEL 替换为实际唯一用户名。"""
    if not unique_username:
        return payload
    return {k: (unique_username if v == UNIQUE_SENTINEL else v) for k, v in payload.items()}


# ═══════════════════════════════════════════════════════════════════
# Group 1: 校验拒绝 — 400/409 + 精确 message（15 条）
# ═══════════════════════════════════════════════════════════════════

REGISTER_VALIDATION_CASES: list[ValidationCase] = [
    ValidationCase(
        id="TC-REG-004",
        title="用户名和密码均为空",
        description='请求体：全空\n期望：400，message="请输入用户名和密码"\n测试点：not username and not password',
        severity="critical",
        priority="P0",
        payload={"username": "", "password": "", "password2": "", "email": ""},
        expected_status=400,
        expected_message="请输入用户名和密码",
    ),
    ValidationCase(
        id="TC-REG-005",
        title="用户名为空",
        description='请求体：username=""，password="pass123"\n期望：400，message="请输入用户名"\n测试点：not username 分支',
        severity="critical",
        priority="P0",
        payload={"username": "", "password": "pass123", "password2": "pass123", "email": "a@b.com"},
        expected_status=400,
        expected_message="请输入用户名",
    ),
    ValidationCase(
        id="TC-REG-006",
        title="密码为空",
        description='请求体：password=""，password2=""\n期望：400，message="请输入密码"\n测试点：not password 分支',
        severity="critical",
        priority="P0",
        payload={"username": "newuser", "password": "", "password2": "", "email": "a@b.com"},
        expected_status=400,
        expected_message="请输入密码",
    ),
    ValidationCase(
        id="TC-REG-007",
        title="用户名少于 3 字符",
        description='请求体：username="ab"（2 字符）\n期望：400，message="用户名至少 3 个字符"\n测试点：len(username) < 3',
        severity="normal",
        priority="P1",
        payload={
            "username": "ab",
            "password": "pass123",
            "password2": "pass123",
            "email": "a@b.com",
        },
        expected_status=400,
        expected_message="用户名至少 3 个字符",
    ),
    ValidationCase(
        id="TC-REG-008",
        title="用户名 2 字符（刚好低于最小值）",
        description='请求体：username="ab"（2 字符）\n期望：400，message="用户名至少 3 个字符"\n测试点：边界值 2，len(username) < 3',
        severity="normal",
        priority="P1",
        payload={
            "username": "ab",
            "password": "pass123",
            "password2": "pass123",
            "email": "a@b.com",
        },
        expected_status=400,
        expected_message="用户名至少 3 个字符",
    ),
    ValidationCase(
        id="TC-REG-009",
        title="用户名超过 20 字符",
        description="请求体：username=21×'a'\n期望：400，message=\"用户名最多 20 个字符\"\n测试点：len(username) > 20",
        severity="normal",
        priority="P1",
        payload={
            "username": "a" * 21,
            "password": "pass123",
            "password2": "pass123",
            "email": "a@b.com",
        },
        expected_status=400,
        expected_message="用户名最多 20 个字符",
    ),
    ValidationCase(
        id="TC-REG-010",
        title="用户名 21 字符（刚好超限）",
        description="请求体：username=21×'a'\n期望：400，message=\"用户名最多 20 个字符\"\n测试点：边界值 21，len(username) > 20",
        severity="normal",
        priority="P1",
        payload={
            "username": "a" * 21,
            "password": "pass123",
            "password2": "pass123",
            "email": "a@b.com",
        },
        expected_status=400,
        expected_message="用户名最多 20 个字符",
    ),
    ValidationCase(
        id="TC-REG-011",
        title="两次密码不一致",
        description='请求体：password="pass123", password2="pass456"\n期望：400，message="两次密码不一致"\n测试点：password != password2',
        severity="critical",
        priority="P0",
        payload={
            "username": UNIQUE_SENTINEL,
            "password": "pass123",
            "password2": "pass456",
            "email": "a@b.com",
        },
        expected_status=400,
        expected_message="两次密码不一致",
    ),
    ValidationCase(
        id="TC-REG-012",
        title="邮箱为空",
        description='请求体：email=""\n期望：400，message="请输入邮箱"\n测试点：not email',
        severity="normal",
        priority="P1",
        payload={
            "username": UNIQUE_SENTINEL,
            "password": "pass123",
            "password2": "pass123",
            "email": "",
        },
        expected_status=400,
        expected_message="请输入邮箱",
    ),
    ValidationCase(
        id="TC-REG-013",
        title="邮箱格式不正确 — 缺 @",
        description='请求体：email="notanemail"\n期望：400，message="邮箱格式不正确"\n测试点："@" not in email',
        severity="normal",
        priority="P1",
        payload={
            "username": UNIQUE_SENTINEL,
            "password": "pass123",
            "password2": "pass123",
            "email": "notanemail",
        },
        expected_status=400,
        expected_message="邮箱格式不正确",
    ),
    ValidationCase(
        id="TC-REG-015",
        title="缺少 username 字段",
        description='请求体：无 username 键\n期望：400，message="请输入用户名"\n测试点：data.get("username","").strip() → ""',
        severity="normal",
        priority="P1",
        payload={"password": "pass123", "password2": "pass123", "email": "a@b.com"},
        expected_status=400,
        expected_message="请输入用户名",
    ),
    ValidationCase(
        id="TC-REG-016",
        title="缺少 password 字段",
        description='请求体：无 password 键\n期望：400，message="请输入密码"\n测试点：data.get("password","").strip() → ""',
        severity="normal",
        priority="P1",
        payload={"username": "newuser", "password2": "pass123", "email": "a@b.com"},
        expected_status=400,
        expected_message="请输入密码",
    ),
    ValidationCase(
        id="TC-REG-017",
        title="缺少 email 字段",
        description='请求体：无 email 键\n期望：400，message="请输入邮箱"\n测试点：data.get("email","").strip() → ""',
        severity="normal",
        priority="P1",
        payload={"username": UNIQUE_SENTINEL, "password": "pass123", "password2": "pass123"},
        expected_status=400,
        expected_message="请输入邮箱",
    ),
    ValidationCase(
        id="TC-REG-018",
        title="空请求体",
        description='请求体：{}\n期望：400，message="请输入用户名和密码"\n测试点：所有字段默认空串 → not username and not password',
        severity="normal",
        priority="P1",
        payload={},
        expected_status=400,
        expected_message="请输入用户名和密码",
    ),
    ValidationCase(
        id="TC-REG-020",
        title="用户名已存在",
        description='请求体：username="admin"（已存在）\n期望：409，message="用户名已存在"\n测试点：User.objects.filter(username=username).exists()',
        severity="critical",
        priority="P0",
        payload={
            "username": "admin",
            "password": "pass123",
            "password2": "pass123",
            "email": "a@b.com",
        },
        expected_status=409,
        expected_message="用户名已存在",
    ),
]


@pytest.mark.parametrize("case", REGISTER_VALIDATION_CASES, ids=lambda c: c.id)
@pytest.mark.api
@pytest.mark.auth
def test_register_validation(base_url, api_session, unique_username, case):
    """参数化：注册校验拒绝（15 条）。"""
    set_allure_metadata(
        feature="认证模块",
        story="注册接口",
        title=f"{case.id}: {case.title}",
        description=case.description,
        severity=case.severity,
        tags=("auth", "api", case.priority),
    )
    payload = _resolve_payload(case.payload, unique_username)
    resp = api_session.post(f"{base_url}{REGISTER_URL}", json=payload)
    body = resp.json()
    jsonschema.validate(instance=body, schema=ERROR_RESPONSE_SCHEMA)
    assert resp.status_code == case.expected_status, (
        f"期望 {case.expected_status}，实际 {resp.status_code}: {body}"
    )
    assert body["message"] == case.expected_message


# ═══════════════════════════════════════════════════════════════════
# Group 2: 成功注册 — 200 + Token + 用户对象（2 条）
# ═══════════════════════════════════════════════════════════════════

REGISTER_SUCCESS_CASES: list[SuccessCase] = [
    SuccessCase(
        id="TC-REG-001",
        title="正常注册",
        description="请求体：username 唯一，password/password2/email 正常\n期望：200，返回 Token 对 + 用户对象\n测试点：正常注册流程，注册即登录",
        severity="blocker",
        priority="P0",
        payload={
            "username": UNIQUE_SENTINEL,
            "password": "pass123",
            "password2": "pass123",
            "email": "a@b.com",
        },
    ),
    SuccessCase(
        id="TC-REG-002",
        title="用户名 3 字符（边界最小值）",
        description="请求体：username=3 字符\n期望：200，返回 Token 对\n测试点：len(username) >= 3 边界通过",
        severity="critical",
        priority="P0",
        payload={
            "username": UNIQUE_SENTINEL,
            "password": "pass123",
            "password2": "pass123",
            "email": "a@b.com",
        },
    ),
]


@pytest.mark.parametrize("case", REGISTER_SUCCESS_CASES, ids=lambda c: c.id)
@pytest.mark.api
@pytest.mark.auth
def test_register_success(base_url, api_session, unique_username, case):
    """参数化：注册成功（2 条）。"""
    set_allure_metadata(
        feature="认证模块",
        story="注册接口",
        title=f"{case.id}: {case.title}",
        description=case.description,
        severity=case.severity,
        tags=("auth", "api", case.priority),
    )
    uname = unique_username
    if case.id == "TC-REG-002":
        # 确保用户名恰好 3 字符，3 hex 字符 = 4096 种组合
        uname = uuid.uuid4().hex[:3]
    payload = _resolve_payload(case.payload, unique_username=uname)
    resp = api_session.post(f"{base_url}{REGISTER_URL}", json=payload)
    body = resp.json()
    assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {body}"
    jsonschema.validate(instance=body, schema=REGISTER_SUCCESS_SCHEMA)
    assert body["user"]["username"] == uname
    assert body["user"]["email"] == "a@b.com"


# ═══════════════════════════════════════════════════════════════════
# Group 3: 条件分支 — 200/409，取决于 DB 状态（5 条）
# ═══════════════════════════════════════════════════════════════════

REGISTER_CONDITIONAL_CASES: list[ConditionalCase] = [
    ConditionalCase(
        id="TC-REG-003",
        title="用户名 20 字符（边界最大值）",
        description="请求体：username=20×'a'\n期望：200 或 409（取决于用户名是否已存在）\n测试点：len(username) <= 20 边界通过",
        severity="critical",
        priority="P0",
        payload={
            "username": "a" * 20,
            "password": "pass123",
            "password2": "pass123",
            "email": "a@b.com",
        },
    ),
    ConditionalCase(
        id="TC-REG-014",
        title="邮箱格式 — 仅含 @ 符号",
        description='请求体：email="@"\n期望："@" in "@" → True → 通过校验 → 200 或 409\n测试点：仅校验 @ 存在，不校验格式完整性',
        severity="normal",
        priority="P1",
        payload={
            "username": UNIQUE_SENTINEL,
            "password": "pass123",
            "password2": "pass123",
            "email": "@",
        },
    ),
    ConditionalCase(
        id="TC-REG-021",
        title="SQL 注入 — username",
        description='请求体：username="admin\'--"\n期望：200 或 409，不绕过认证\n测试点：Django ORM 参数化查询防注入',
        severity="normal",
        priority="P1",
        extra_tags=("security",),
        payload={
            "username": "admin'--",
            "password": "pass123",
            "password2": "pass123",
            "email": "a@b.com",
        },
    ),
    ConditionalCase(
        id="TC-REG-022",
        title="XSS — username",
        description='请求体：username="<img src=x>"（11 字符）\n期望：200 或 409\n测试点：XSS 注入不影响注册逻辑',
        severity="normal",
        priority="P1",
        extra_tags=("security",),
        payload={
            "username": "<img src=x>",
            "password": "pass123",
            "password2": "pass123",
            "email": "a@b.com",
        },
    ),
    ConditionalCase(
        id="TC-REG-023",
        title="XSS — email",
        description='请求体：email="<script>@x.com"\n期望："@" in email → True → 200 或 409\n测试点：邮箱仅校验 @ 存在，不校验完整格式',
        severity="normal",
        priority="P1",
        extra_tags=("security",),
        payload={
            "username": UNIQUE_SENTINEL,
            "password": "pass123",
            "password2": "pass123",
            "email": "<script>@x.com",
        },
    ),
]


@pytest.mark.parametrize("case", REGISTER_CONDITIONAL_CASES, ids=lambda c: c.id)
@pytest.mark.api
@pytest.mark.auth
def test_register_conditional(base_url, api_session, unique_username, case):
    """参数化：注册条件分支 — 200/409（5 条）。"""
    tags = ("auth", "api", case.priority) + case.extra_tags
    set_allure_metadata(
        feature="认证模块",
        story="注册接口",
        title=f"{case.id}: {case.title}",
        description=case.description,
        severity=case.severity,
        tags=tags,
    )
    payload = _resolve_payload(case.payload, unique_username)
    resp = api_session.post(f"{base_url}{REGISTER_URL}", json=payload)
    body = resp.json()
    assert resp.status_code in (200, 409), f"意外状态码 {resp.status_code}: {body}"
    if resp.status_code == 200:
        jsonschema.validate(instance=body, schema=REGISTER_SUCCESS_SCHEMA)
        assert body["status"] is True
    else:
        assert body["status"] is False
        assert body["message"] == "用户名已存在"


# ═══════════════════════════════════════════════════════════════════
# 独立函数：JSON 非法 / 超长密码（Shape 特殊，不适合参数化）
# ═══════════════════════════════════════════════════════════════════


@allure.feature("认证模块")
@allure.story("注册接口")
@allure.severity(allure.severity_level.MINOR)
@allure.title("TC-REG-019: JSON 格式非法")
@allure.description(
    '请求体：纯文本 "not a json"\n期望：400，message="请求格式错误"\n测试点：json.JSONDecodeError 捕获'
)
@allure.tag("auth", "api", "P2")
@pytest.mark.api
@pytest.mark.auth
def test_register_invalid_json(base_url, api_session):
    """非 JSON 请求体 → 400。使用 data= 而非 json=。"""
    resp = api_session.post(f"{base_url}{REGISTER_URL}", data="not a json")
    body = resp.json()
    assert resp.status_code == 400
    assert body["status"] is False
    assert body["message"] == "请求格式错误"


@allure.feature("认证模块")
@allure.story("注册接口")
@allure.severity(allure.severity_level.MINOR)
@allure.title("TC-REG-024: 超长密码")
@allure.description(
    "请求体：password 为 1MB 字符串\n期望：200/400/409/413，服务不崩溃\n测试点：Django create_user 无密码长度上限"
)
@allure.tag("auth", "api", "security", "P2")
@pytest.mark.api
@pytest.mark.auth
def test_register_oversized_password(base_url, api_session, unique_username):
    """1MB 密码 — 验证服务不崩溃、不超时。"""
    big = "a" * 1024 * 1024
    resp = api_session.post(
        f"{base_url}{REGISTER_URL}",
        json={"username": unique_username, "password": big, "password2": big, "email": "a@b.com"},
    )
    body = resp.json()
    assert resp.status_code in (200, 400, 409, 413), f"意外状态码 {resp.status_code}: {body}"
    if resp.status_code == 200:
        jsonschema.validate(instance=body, schema=REGISTER_SUCCESS_SCHEMA)
        assert body["status"] is True
    else:
        assert body["status"] is False
