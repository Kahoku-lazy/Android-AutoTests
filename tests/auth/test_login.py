"""登录接口 API 测试 — POST /api/auth/login（数据驱动 + JSON Schema）。

20 条用例按断言 Shape 分为 3 个参数化组 + 5 个独立函数：
  - test_login_validation[8]   — 400 + 精确/子串错误消息
  - test_login_auth_fail[7]    — 401 + "用户名或密码错误"
  - test_login_success          — 200 + Token + 用户对象
  - test_login_whitespace       — 用户名含首尾空格（200/401 条件）
  - test_login_invalid_json     — 非 JSON 请求体
  - test_login_oversized        — 1MB 密码不崩溃
  - test_login_brute_force      — 连续 5 次错误密码

运行方式：
    pytest tests/auth/test_login.py -v --alluredir=allure-results
"""

from dataclasses import dataclass

import allure
import jsonschema
import pytest

from tests.auth.conftest import LOGIN_URL, set_allure_metadata
from tests.auth.schemas import AUTH_SUCCESS_SCHEMA, ERROR_RESPONSE_SCHEMA

# ═══════════════════════════════════════════════════════════════════
# 数据类型
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ValidationCase:
    """400 校验拒绝用例 — 请求被拒绝，返回 {status:false, message}。"""

    id: str
    title: str
    description: str
    severity: str
    priority: str
    payload: dict
    expected_message: str
    exact_message: bool = True  # True = assert ==, False = assert "in"


@dataclass(frozen=True)
class AuthFailCase:
    """401 认证失败用例 — 统一返回 "用户名或密码错误"。"""

    id: str
    title: str
    description: str
    severity: str
    priority: str
    payload: dict
    extra_tags: tuple[str, ...] = ()


# ═══════════════════════════════════════════════════════════════════
# Group 1: 校验拒绝 — 400 + 精确/子串 message（8 条）
# ═══════════════════════════════════════════════════════════════════

LOGIN_VALIDATION_CASES: list[ValidationCase] = [
    ValidationCase(
        id="TC-LOGIN-003",
        title="用户名和密码均为空",
        description='请求体：username=""，password=""\n期望：400，message="请输入用户名和密码"\n测试点：not username and not password',
        severity="critical",
        priority="P0",
        payload={"username": "", "password": ""},
        expected_message="请输入用户名和密码",
    ),
    ValidationCase(
        id="TC-LOGIN-004",
        title="用户名为空",
        description='请求体：username=""，password="admin123"\n期望：400，message="请输入用户名"\n测试点：not username 分支',
        severity="critical",
        priority="P0",
        payload={"username": "", "password": "admin123"},
        expected_message="请输入用户名",
    ),
    ValidationCase(
        id="TC-LOGIN-005",
        title="密码为空",
        description='请求体：username="admin"，password=""\n期望：400，message="请输入密码"\n测试点：not password 分支',
        severity="critical",
        priority="P0",
        payload={"username": "admin", "password": ""},
        expected_message="请输入密码",
    ),
    ValidationCase(
        id="TC-LOGIN-006",
        title="用户名为纯空白",
        description='请求体：username="   "，password="admin123"\n期望：400，message="用户名不能为空白"\n测试点：not username.strip() 分支',
        severity="critical",
        priority="P0",
        payload={"username": "   ", "password": "admin123"},
        expected_message="用户名不能为空白",
    ),
    ValidationCase(
        id="TC-LOGIN-007",
        title="用户名超过 150 字符",
        description='请求体：username=151×\'a\'，password="admin123"\n期望：400，message 含 "过长"\n测试点：len(username) > 150',
        severity="normal",
        priority="P1",
        payload={"username": "a" * 151, "password": "admin123"},
        expected_message="过长",
        exact_message=False,
    ),
    ValidationCase(
        id="TC-LOGIN-009",
        title="缺少 username 字段",
        description='请求体：{"password":"admin123"}\n期望：400，message="请输入用户名"\n测试点：data.get("username","") → ""',
        severity="normal",
        priority="P1",
        payload={"password": "admin123"},
        expected_message="请输入用户名",
    ),
    ValidationCase(
        id="TC-LOGIN-010",
        title="缺少 password 字段",
        description='请求体：{"username":"admin"}\n期望：400，message="请输入密码"\n测试点：data.get("password","") → ""',
        severity="normal",
        priority="P1",
        payload={"username": "admin"},
        expected_message="请输入密码",
    ),
    ValidationCase(
        id="TC-LOGIN-011",
        title="空请求体",
        description='请求体：{}\n期望：400，message="请输入用户名和密码"\n测试点：空 JSON 对象',
        severity="normal",
        priority="P1",
        payload={},
        expected_message="请输入用户名和密码",
    ),
]


@pytest.mark.parametrize("case", LOGIN_VALIDATION_CASES, ids=lambda c: c.id)
@pytest.mark.api
@pytest.mark.auth
def test_login_validation(base_url, api_session, case):
    """参数化：登录校验拒绝（8 条）。"""
    set_allure_metadata(
        feature="认证模块",
        story="登录接口",
        title=f"{case.id}: {case.title}",
        description=case.description,
        severity=case.severity,
        tags=("auth", "api", case.priority),
    )
    resp = api_session.post(f"{base_url}{LOGIN_URL}", json=case.payload)
    body = resp.json()
    jsonschema.validate(instance=body, schema=ERROR_RESPONSE_SCHEMA)
    assert resp.status_code == 400, f"期望 400，实际 {resp.status_code}: {body}"
    if case.exact_message:
        assert body["message"] == case.expected_message
    else:
        assert case.expected_message in body["message"]


# ═══════════════════════════════════════════════════════════════════
# Group 2: 认证失败 — 401 + "用户名或密码错误"（7 条）
# ═══════════════════════════════════════════════════════════════════

LOGIN_AUTH_FAIL_CASES: list[AuthFailCase] = [
    AuthFailCase(
        id="TC-LOGIN-008",
        title="用户名 150 字符（边界内）",
        description='请求体：username=150×\'a\'，password="admin123"\n期望：401，message="用户名或密码错误"\n测试点：边界值 150 通过长度校验 → 进入 authenticate',
        severity="normal",
        priority="P1",
        payload={"username": "a" * 150, "password": "admin123"},
    ),
    AuthFailCase(
        id="TC-LOGIN-013",
        title="密码错误",
        description='请求体：username="admin"，password="wrong"\n期望：401，message="用户名或密码错误"\n测试点：不区分"用户不存在"和"密码错误"',
        severity="critical",
        priority="P0",
        payload={"username": "admin", "password": "wrong"},
    ),
    AuthFailCase(
        id="TC-LOGIN-014",
        title="用户名不存在",
        description='请求体：username="no_such_user"，password="admin123"\n期望：401，message="用户名或密码错误"\n测试点：统一错误消息，防止用户名枚举',
        severity="critical",
        priority="P0",
        payload={"username": "no_such_user", "password": "admin123"},
    ),
    AuthFailCase(
        id="TC-LOGIN-015",
        title="用户名和密码均错误",
        description='请求体：username="no"，password="wrong"\n期望：401，message="用户名或密码错误"\n测试点：两种错误统一返回 401',
        severity="critical",
        priority="P0",
        payload={"username": "no", "password": "wrong"},
    ),
    AuthFailCase(
        id="TC-LOGIN-016",
        title="SQL 注入 — username 字段",
        description="请求体：username=\"admin' OR '1'='1\"\n期望：401，不绕过认证\n测试点：Django ORM 参数化查询防注入",
        severity="normal",
        priority="P1",
        extra_tags=("security",),
        payload={"username": "admin' OR '1'='1", "password": "admin123"},
    ),
    AuthFailCase(
        id="TC-LOGIN-017",
        title="SQL 注入 — password 字段",
        description="请求体：password=\"' OR '1'='1\"\n期望：401，不绕过认证\n测试点：密码字段同样受参数化查询保护",
        severity="normal",
        priority="P1",
        extra_tags=("security",),
        payload={"username": "admin", "password": "' OR '1'='1"},
    ),
    AuthFailCase(
        id="TC-LOGIN-018",
        title="XSS — username 字段",
        description='请求体：username="<script>alert(1)</script>"\n期望：401（用户不存在）\n测试点：XSS 注入不产生安全风险',
        severity="normal",
        priority="P1",
        extra_tags=("security",),
        payload={"username": "<script>alert(1)</script>", "password": "admin123"},
    ),
]


@pytest.mark.parametrize("case", LOGIN_AUTH_FAIL_CASES, ids=lambda c: c.id)
@pytest.mark.api
@pytest.mark.auth
def test_login_auth_fail(base_url, api_session, case):
    """参数化：登录认证失败（7 条）。"""
    tags = ("auth", "api", case.priority) + case.extra_tags
    set_allure_metadata(
        feature="认证模块",
        story="登录接口",
        title=f"{case.id}: {case.title}",
        description=case.description,
        severity=case.severity,
        tags=tags,
    )
    resp = api_session.post(f"{base_url}{LOGIN_URL}", json=case.payload)
    body = resp.json()
    jsonschema.validate(instance=body, schema=ERROR_RESPONSE_SCHEMA)
    assert resp.status_code == 401, f"期望 401，实际 {resp.status_code}: {body}"
    assert body["message"] == "用户名或密码错误"


# ═══════════════════════════════════════════════════════════════════
# 独立函数：成功 / 空白用户名 / 非法 JSON / 超大密码 / 暴力破解
# ═══════════════════════════════════════════════════════════════════


@allure.feature("认证模块")
@allure.story("登录接口")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("TC-LOGIN-001: 正常登录")
@allure.description(
    '请求体：{"username":"admin","password":"admin123"}\n'
    "期望：200，返回 Token 对 + 用户对象\n"
    "测试点：正常登录流程，确认 Token 对和用户信息正确返回"
)
@allure.tag("auth", "api", "P0")
@pytest.mark.api
@pytest.mark.auth
def test_login_success(base_url, api_session):
    """正常登录 → 200 + Token + 用户对象。"""
    resp = api_session.post(
        f"{base_url}{LOGIN_URL}",
        json={"username": "admin", "password": "admin123"},
    )
    body = resp.json()
    assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {body}"
    jsonschema.validate(instance=body, schema=AUTH_SUCCESS_SCHEMA)
    assert body["data"]["user"]["username"] == "admin"


@allure.feature("认证模块")
@allure.story("登录接口")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("TC-LOGIN-002: 用户名含首尾空格")
@allure.description(
    '请求体：username=" admin "\n'
    "期望：200 或 401（取决于 authenticate 是否 trim）\n"
    "测试点：后端不 trim 用户名，直接传给认证函数"
)
@allure.tag("auth", "api", "P1")
@pytest.mark.api
@pytest.mark.auth
def test_login_username_with_spaces(base_url, api_session):
    """用户名首尾空格 — 条件 200/401。"""
    resp = api_session.post(
        f"{base_url}{LOGIN_URL}",
        json={"username": " admin ", "password": "admin123"},
    )
    body = resp.json()
    assert resp.status_code in (200, 401), f"意外状态码 {resp.status_code}: {body}"
    if resp.status_code == 200:
        assert body["status"] is True
    else:
        assert body["status"] is False


@allure.feature("认证模块")
@allure.story("登录接口")
@allure.severity(allure.severity_level.MINOR)
@allure.title("TC-LOGIN-012: JSON 格式非法")
@allure.description(
    '请求体：纯文本 "not a json"\n期望：400，message="请求格式错误"\n测试点：json.JSONDecodeError 捕获'
)
@allure.tag("auth", "api", "P2")
@pytest.mark.api
@pytest.mark.auth
def test_login_invalid_json(base_url, api_session):
    """非 JSON 请求体 → 400。使用 data= 而非 json=。"""
    resp = api_session.post(f"{base_url}{LOGIN_URL}", data="not a json")
    body = resp.json()
    assert resp.status_code == 400
    assert body["status"] is False
    assert body["message"] == "请求格式错误"


@allure.feature("认证模块")
@allure.story("登录接口")
@allure.severity(allure.severity_level.MINOR)
@allure.title("TC-LOGIN-019: 超长密码")
@allure.description(
    "请求体：password 为 1MB 字符串\n期望：401/400/413，服务不崩溃\n测试点：Django authenticate() 能正常处理超大输入"
)
@allure.tag("auth", "api", "security", "P2")
@pytest.mark.api
@pytest.mark.auth
def test_login_oversized_password(base_url, api_session):
    """1MB 密码 — 验证服务不崩溃。"""
    resp = api_session.post(
        f"{base_url}{LOGIN_URL}",
        json={"username": "admin", "password": "a" * 1024 * 1024},
    )
    body = resp.json()
    assert resp.status_code in (401, 400, 413), f"意外状态码 {resp.status_code}: {body}"
    assert body["status"] is False


@allure.feature("认证模块")
@allure.story("登录接口")
@allure.severity(allure.severity_level.MINOR)
@allure.title("TC-LOGIN-020: 暴力破解 — 5 次连续错误密码")
@allure.description(
    '连续 5 次对同一用户使用错误密码\n期望：每次均返回 401，message="用户名或密码错误"\n测试点：当前无频率限制，确认不会被锁或异常'
)
@allure.tag("auth", "api", "security", "P2")
@pytest.mark.api
@pytest.mark.auth
def test_login_brute_force(base_url, api_session):
    """连续 5 次错误密码 → 每次都返回 401。"""
    for i in range(5):
        resp = api_session.post(
            f"{base_url}{LOGIN_URL}",
            json={"username": "admin", "password": f"wrong_{i}"},
        )
        body = resp.json()
        assert resp.status_code == 401, f"第 {i + 1} 次: {resp.status_code}"
        assert body["status"] is False
        assert body["message"] == "用户名或密码错误"
