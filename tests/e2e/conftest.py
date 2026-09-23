"""黑盒·端到端测试层 fixtures — Playwright 真实浏览器 + 带标注的步骤报告。

依赖：pytest-playwright、前后端已启动（「python run.py start」，前端 5173 / 后端 8766）。
环境变量（都可不设）：
  TEST_FRONTEND_URL        默认 http://localhost:5173
  TEST_BASE_URL            默认 http://localhost:8766（见 tests/conftest.py）
  E2E_REPORT_DIR           步骤报告输出目录，默认 tests/reports/e2e

本层**不需要任何密钥**：用公开注册端点自建一个固定账号，之后每轮运行复用。
因此不会出现「没设密钥 → 静默跳过」的假守护。

每一步的截图与标注见 tests/e2e/step_report.py；报告在会话结束时落到
tests/reports/e2e/index.html。
"""

import os
import re

import allure
import pytest
import requests

from tests.e2e import selectors as S
from tests.e2e import step_report
from tests.e2e.step_report import CaseRecord, StepRecorder

FRONTEND_URL = os.environ.get("TEST_FRONTEND_URL", "http://localhost:5173")

LOGIN_PATH = "/api/auth/login/"
REGISTER_PATH = "/api/auth/register/"

#: E2E 自建账号：固定用户名 + 固定密码 → 首次运行创建、之后复用，开发库最多留 1 行。
E2E_ACCOUNT = {
    "username": "e2e_probe",
    "password": "e2e-probe-password",
    "email": "e2e_probe@example.com",
}


def _reachable(url: str, timeout: float = 2.0) -> bool:
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False


def _case_code(nodeid: str) -> str:
    """从 test_e2e_001_xxx 里取出用例编号 E2E-001。"""
    match = re.search(r"e2e_(\d{3})", nodeid)
    return f"E2E-{match.group(1)}" if match else nodeid


@pytest.fixture(scope="session")
def frontend_url() -> str:
    return FRONTEND_URL.rstrip("/")


@pytest.fixture(scope="session")
def e2e_services(frontend_url: str, base_url: str) -> dict:
    """前后端不可达时跳过整组 E2E，避免硬 fail。"""
    if not _reachable(frontend_url):
        pytest.skip(f"前端不可达: {frontend_url}")
    if not _reachable(base_url):
        pytest.skip(f"后端不可达: {base_url}")
    return {"frontend": frontend_url, "backend": base_url}


@pytest.fixture(scope="session")
def e2e_account(e2e_services: dict) -> dict:
    """自建 / 复用 E2E 账号 —— 不需要任何密钥，因此不会静默跳过。

    先走公开注册端点；返回 409 说明上一轮已经建过（固定用户名），直接登录复用。
    两条路都走不通时 fail 而不是 skip：账号被占用却登不进去是真实红灯。
    """
    api = e2e_services["backend"]
    created = requests.post(
        api + REGISTER_PATH,
        json={
            "username": E2E_ACCOUNT["username"],
            "password": E2E_ACCOUNT["password"],
            "password2": E2E_ACCOUNT["password"],
            "email": E2E_ACCOUNT["email"],
        },
        timeout=15,
    )
    if created.status_code == 200:
        return dict(E2E_ACCOUNT)
    if created.status_code != 409:
        pytest.fail(
            f"E2E 账号创建失败：POST {REGISTER_PATH} → {created.status_code} {created.text[:200]}"
        )

    reused = requests.post(
        api + LOGIN_PATH,
        json={"username": E2E_ACCOUNT["username"], "password": E2E_ACCOUNT["password"]},
        timeout=15,
    )
    if reused.status_code != 200:
        pytest.fail(
            f"E2E 账号 {E2E_ACCOUNT['username']} 已存在但登录失败"
            f"（{reused.status_code} {reused.text[:200]}）—— 可能被改过密码，请改名或删号后重跑"
        )
    return dict(E2E_ACCOUNT)


@pytest.fixture(scope="session")
def e2e_step_report() -> step_report.StepReport:
    """会话级步骤报告：开场先清掉上一轮产物，结束时由 pytest_sessionfinish 落盘。"""
    report = step_report.get_report()
    report.reset()
    return report


@pytest.fixture
def login_page(page, e2e_services: dict):
    """打开 /login 并等到登录页渲染就绪。"""
    page.goto(f"{e2e_services['frontend']}/login", wait_until="domcontentloaded")
    page.get_by_test_id(S.LOGIN_PAGE).wait_for(timeout=15000)
    return page


@pytest.fixture
def steps(page, request, e2e_step_report) -> StepRecorder:
    """用例级步骤记录器：动作照旧走 Playwright 原生 API，夹具负责标注截图与汇总。

    用例标题取 docstring 首行（那里写着它覆盖的业务用例编号），报告里就能业务对业务地读。
    """
    nodeid = re.sub(r"\[[^\]]*\]$", "", request.node.name)
    doc = (getattr(request.node.function, "__doc__", "") or "").strip()
    title = doc.splitlines()[0].strip() if doc else nodeid
    case = CaseRecord(code=_case_code(nodeid), title=title, nodeid=nodeid)
    e2e_step_report.register(case)
    return StepRecorder(page, case, e2e_step_report)


@pytest.fixture
def login_requests(page) -> list:
    """记录发往登录端点的请求 —— 「只发 1 次」类断言的主证据。

    只看界面会漏掉重复提交（功能测试文档第四节明确要求同时看请求条数），所以计数
    是断言的第一证据，覆盖层层数作第二条独立证据。
    """
    hits: list = []

    def _on_request(request):
        if request.method == "POST" and request.url.split("?")[0].endswith(LOGIN_PATH):
            hits.append(request.url)

    page.on("request", _on_request)
    return hits


@pytest.fixture
def held_login_requests(page) -> list:
    """拦住登录请求不让它出网，返回 route 列表；用例用 held[0].continue_() 放行。

    本地后端只需几十毫秒，靠「响应够慢」观测 loading 是 flaky 的；拦住请求可以把
    loading 窗口（以及连点窗口）变成确定性事件。
    """
    held: list = []

    def _on_route(route):
        held.append(route)

    page.route(f"**{LOGIN_PATH}", _on_route)
    return held


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """记录用例结果与耗时，失败时补一张失败现场截图（同时挂 Allure）。"""
    outcome = yield
    report = outcome.get_result()

    recorder = item.funcargs.get("steps")
    if recorder is not None and report.when == "call":
        recorder.case.duration = report.duration
        recorder.case.status = "passed" if report.passed else "failed"
        if report.failed:
            recorder.case.error = str(report.longrepr)
            try:
                recorder.fail("用例失败现场", str(report.longrepr))
            except Exception:  # noqa: BLE001 — 失败现场截图不能再抛，掩盖原始失败
                pass

    if report.when != "call" or not report.failed:
        return
    page = item.funcargs.get("page")
    if page is None:
        return
    try:
        png = page.screenshot(full_page=True)
        allure.attach(
            png, name=f"失败截图 · {item.name}", attachment_type=allure.attachment_type.PNG
        )
        allure.attach(
            getattr(page, "url", ""), name="失败时 URL", attachment_type=allure.attachment_type.TEXT
        )
    except Exception:  # noqa: BLE001 — 截图失败不掩盖原失败
        pass


def pytest_sessionfinish(session, exitstatus):
    """会话结束落盘步骤报告 —— 无论成败都要有报告，否则等于没有留痕。"""
    report = step_report.get_report()
    if not report.cases:
        return
    path = report.render()
    terminal = session.config.pluginmanager.get_plugin("terminalreporter")
    if terminal is not None:
        terminal.write_sep("=", "端到端步骤报告")
        terminal.write_line(f"{len(report.cases)} 个用例 · HTML：{path.resolve()}")
