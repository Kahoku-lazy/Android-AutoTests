from __future__ import annotations

import pathlib
import re

import pytest

from backend.apps.accounts.serializers import LoginSerializer, RegisterSerializer

pytestmark = pytest.mark.unit

NL = chr(10)
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
FRONTEND_FORM = REPO_ROOT / "frontend/src/shared/composables/useLoginForm.ts"
AUTH_FLOW = REPO_ROOT / "frontend/src/views/composables/useAuthFlow.ts"
BACKEND_SERIALIZERS = REPO_ROOT / "backend/apps/accounts/serializers.py"

_QUOTES = "\"'"
FE_MESSAGE_RX = re.compile(
    r"errs\.(\w+)\s*=\s*[" + _QUOTES + r"]([^" + _QUOTES + r"]+)[" + _QUOTES + r"]"
)
BE_MESSAGE_RX = re.compile(r'ValidationError\(\s*"([^"]+)"')

FE_THRESHOLD_RX = re.compile(r"\.length\s*([<>]=?)\s*(\d+)")
BE_THRESHOLD_RX = re.compile(r"len\(.*?\)\s*([<>]=?)\s*(\d+)")

ACCEPTED_DIFFERENCES = {
    "frontend_only": {
        "请再次输入密码": "前端区分「密码2 为空」与「两次不一致」；后端只有后者（空值也报不一致）",
    },
    "backend_only": {
        "请输入用户名和密码": "后端把「用户名与密码都为空」合并成一条；前端按字段分别提示",
        "用户名或密码错误": "凭证校验只能在服务端，前端无法预知",
    },
}

MIN_MESSAGES_PER_SIDE = 10
MIN_THRESHOLDS_PER_SIDE = 4


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _frontend_messages() -> set[str]:
    return {m.group(2) for m in FE_MESSAGE_RX.finditer(_read(FRONTEND_FORM))}


def _backend_messages() -> set[str]:
    return {m.group(1) for m in BE_MESSAGE_RX.finditer(_read(BACKEND_SERIALIZERS))}


def _frontend_thresholds() -> set[tuple[str, str]]:
    return {(m.group(1), m.group(2)) for m in FE_THRESHOLD_RX.finditer(_read(FRONTEND_FORM))}


def _backend_thresholds() -> set[tuple[str, str]]:
    return {(m.group(1), m.group(2)) for m in BE_THRESHOLD_RX.finditer(_read(BACKEND_SERIALIZERS))}


def test_extraction_finds_the_expected_volume():
    actual = {
        "前端文案": (len(_frontend_messages()), MIN_MESSAGES_PER_SIDE),
        "后端文案": (len(_backend_messages()), MIN_MESSAGES_PER_SIDE),
        "前端阈值": (len(_frontend_thresholds()), MIN_THRESHOLDS_PER_SIDE),
        "后端阈值": (len(_backend_thresholds()), MIN_THRESHOLDS_PER_SIDE),
    }
    shortfalls = [
        f"{label}: 只提取到 {got} 条，低于期望 {minimum}"
        for label, (got, minimum) in actual.items()
        if got < minimum
    ]
    assert shortfalls == [], (
        "提取规则可能失效，请检查 FE_MESSAGE_RX / BE_MESSAGE_RX / "
        "阈值正则，而不是直接调低下限：" + NL + NL.join(f"  - {item}" for item in shortfalls)
    )


def test_accepted_differences_all_carry_a_reason():
    missing = [
        f"{side}: {message}"
        for side, entries in ACCEPTED_DIFFERENCES.items()
        for message, reason in entries.items()
        if not reason.strip()
    ]
    assert missing == [], "以下例外缺理由：" + NL + NL.join(f"  - {m}" for m in missing)


def test_message_differences_equal_the_accepted_exceptions():
    frontend = _frontend_messages()
    backend = _backend_messages()
    actual = {"frontend_only": frontend - backend, "backend_only": backend - frontend}
    accepted = {side: set(entries) for side, entries in ACCEPTED_DIFFERENCES.items()}

    problems = []
    for side in ("frontend_only", "backend_only"):
        added = sorted(actual[side] - accepted[side])
        gone = sorted(accepted[side] - actual[side])
        if added:
            problems.append(f"{side} 新增/改动（需同步另一侧，或补理由登记为例外）：{added}")
        if gone:
            problems.append(f"{side} 例外已消失（已同步，或例外过期）：{gone}")

    assert problems == [], (
        "两侧校验文案的差异不再等于已声明的例外："
        + NL
        + NL.join(f"  - {p}" for p in problems)
        + NL
        + f"  前端 {len(frontend)} 条 / 后端 {len(backend)} 条 / 共有 {len(frontend & backend)} 条"
    )


def test_threshold_sets_are_identical():
    frontend = _frontend_thresholds()
    backend = _backend_thresholds()
    assert frontend == backend, (
        "两侧的数值阈值不一致（格式：(比较符, 数值)）："
        + NL
        + f"  仅前端：{sorted(frontend - backend)}"
        + NL
        + f"  仅后端：{sorted(backend - frontend)}"
    )


MIN_CALLS_PER_SIDE = 1


def _trim_flag(serializer, field_name: str) -> bool:
    return bool(getattr(serializer.fields[field_name], "trim_whitespace", False))


def _auth_call_rx(fn_name: str) -> re.Pattern[str]:
    return re.compile(r"await\s+" + fn_name + r"\(([^()\n]*(?:\([^()\n]*\)[^()\n]*)*)\)")


def _auth_call_args(fn_name: str) -> list[list[str]]:
    matches = _auth_call_rx(fn_name).findall(_read(AUTH_FLOW))
    return [[part.strip() for part in m.split(",") if part.strip()] for m in matches]


def test_backend_trim_stance_is_declared_per_field():
    serializer = LoginSerializer()
    password_flag = _trim_flag(serializer, "password")
    username_flag = _trim_flag(serializer, "username")
    assert password_flag is True and username_flag is False, (
        "空白归一化口径漂移：期望 密码=True / 账号=False，"
        f"实际 密码={password_flag} / 账号={username_flag}"
    )


def test_backend_login_password_strips_surrounding_whitespace():
    assert LoginSerializer().fields["password"].run_validation("  abc123  ") == "abc123"


def test_backend_password_inner_whitespace_is_kept():
    field = LoginSerializer().fields["password"]
    assert field.run_validation("a b\tc\nd") == "a b\tc\nd"


def test_backend_login_username_is_kept_as_typed():
    assert LoginSerializer().fields["username"].run_validation("  admin  ") == "  admin  "


def test_backend_register_strips_password_surrounding_whitespace():
    attrs = RegisterSerializer().validate(
        {
            "username": "  abc  ",
            "password": "  abc123  ",
            "password2": "  abc123  ",
            "email": "  a@b.com  ",
        }
    )
    assert attrs["password"] == "abc123"
    assert attrs["username"] == "abc"
    assert attrs["email"] == "a@b.com"


def test_frontend_login_export_does_not_trim_password():
    calls = _auth_call_args("login")
    assert len(calls) >= MIN_CALLS_PER_SIDE, "提取规则可能失效：没读到 await login(...)"
    assert [args[1] for args in calls] == ["password"] * len(calls)


def test_frontend_register_export_trims_password():
    calls = _auth_call_args("register")
    assert len(calls) >= MIN_CALLS_PER_SIDE, "提取规则可能失效：没读到 await register(...)"
    for args in calls:
        assert args[1] == "password.trim()"
        assert args[2] == "password2!.trim()"
        assert args[3] == "email!.trim()"
