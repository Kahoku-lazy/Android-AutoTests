import os
import re
import uuid

import allure
import pytest
import requests

from django.db.backends.signals import connection_created

from tests.e2e import selectors as S
from tests.e2e import step_report
from tests.e2e.step_report import CaseRecord, StepRecorder


def _register_mysql_collation(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        connection.connection.create_collation("utf8mb4_bin", lambda a, b: (a > b) - (a < b))


connection_created.connect(_register_mysql_collation)

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8766")
FRONTEND_URL = os.environ.get("TEST_FRONTEND_URL", "http://localhost:5173")

LOGIN_PATH = "/api/auth/login/"
REGISTER_PATH = "/api/auth/register/"

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
    match = re.search(r"e2e_(\d{3})", nodeid)
    return f"E2E-{match.group(1)}" if match else nodeid


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="function")
def api_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def unique_username() -> str:
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def admin_login(base_url) -> tuple[requests.Session, dict]:
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    resp = session.post(
        f"{base_url}/api/auth/login/", json={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    data = resp.json()["data"]
    session.headers.update({"Authorization": f"Bearer {data['access_token']}"})
    return session, {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


@pytest.fixture(scope="function")
def auth_session(admin_login) -> requests.Session:
    return admin_login[0]


@pytest.fixture(scope="session")
def frontend_url() -> str:
    return FRONTEND_URL.rstrip("/")


@pytest.fixture(scope="session")
def e2e_services(frontend_url: str, base_url: str) -> dict:
    if not _reachable(frontend_url):
        pytest.skip(f"前端不可达: {frontend_url}")
    if not _reachable(base_url):
        pytest.skip(f"后端不可达: {base_url}")
    return {"frontend": frontend_url, "backend": base_url}


@pytest.fixture(scope="session")
def e2e_account(e2e_services: dict) -> dict:
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
    report = step_report.get_report()
    report.reset()
    return report


@pytest.fixture
def login_page(page, e2e_services: dict):
    page.goto(f"{e2e_services['frontend']}/login", wait_until="domcontentloaded")
    page.get_by_test_id(S.LOGIN_PAGE).wait_for(timeout=15000)
    return page


@pytest.fixture
def steps(page, request, e2e_step_report) -> StepRecorder:
    nodeid = re.sub(r"\[[^\]]*\]$", "", request.node.name)
    doc = (getattr(request.node.function, "__doc__", "") or "").strip()
    title = doc.splitlines()[0].strip() if doc else nodeid
    case = CaseRecord(code=_case_code(nodeid), title=title, nodeid=nodeid)
    e2e_step_report.register(case)
    return StepRecorder(page, case, e2e_step_report)


@pytest.fixture
def login_requests(page) -> list:
    hits: list = []

    def _on_request(request):
        if request.method == "POST" and request.url.split("?")[0].endswith(LOGIN_PATH):
            hits.append(request.url)

    page.on("request", _on_request)
    return hits


@pytest.fixture
def held_login_requests(page) -> list:
    held: list = []

    def _on_route(route):
        held.append(route)

    page.route(f"**{LOGIN_PATH}", _on_route)
    return held


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
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
    report = step_report.get_report()
    if not report.cases:
        return
    path = report.render()
    terminal = session.config.pluginmanager.get_plugin("terminalreporter")
    if terminal is not None:
        terminal.write_sep("=", "端到端步骤报告")
        terminal.write_line(f"{len(report.cases)} 个用例 · HTML：{path.resolve()}")
