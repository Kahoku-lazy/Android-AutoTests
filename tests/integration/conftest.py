"""tests/integration/ 共享 fixtures 和 mock 工厂。

为三层测试提供可复用的测试辅助：
- Django ORM fixtures（带 @pytest.mark.django_db）
- Mock DeviceConnection / DeviceAdapter（Layer 3 用）
- Mock ApiAdapter / WebAdapter（Layer 3 用）
- RecordingCallback（所有 Runner 测试用）
"""

from unittest.mock import MagicMock, AsyncMock
import pytest


# ═══════════════════════════════════════
# Django 环境 fixtures（Layer 2 用）
# ═══════════════════════════════════════

@pytest.fixture
def task_card(db):
    """创建一个 idle 状态的 TaskCard。"""
    from apps.test_runner.models import TaskCard
    return TaskCard.objects.create(
        task_id="TC-TEST-001",
        name="测试任务",
        creator="tester",
        task_type="ui_automation",
        mode="immediate",
        device_serial="TEST-DEVICE",
        case_ids=["CASE-1", "CASE-2"],
        loop_count=2,
        interval_seconds=5,
        status="idle",
    )


@pytest.fixture
def queued_task_card(db):
    """创建一个 queued 状态的 TaskCard。"""
    from apps.test_runner.models import TaskCard
    return TaskCard.objects.create(
        task_id="TC-QUEUED-001",
        name="排队任务",
        creator="tester",
        task_type="ui_automation",
        mode="immediate",
        device_serial="TEST-DEVICE",
        case_ids=["CASE-1"],
        loop_count=1,
        status="queued",
    )


@pytest.fixture
def task_card_api(db):
    """创建一个 api_testing 类型的 TaskCard。"""
    from apps.test_runner.models import TaskCard
    return TaskCard.objects.create(
        task_id="TC-API-001",
        name="API测试任务",
        task_type="api_testing",
        case_ids=["API-1"],
        loop_count=1,
        status="idle",
    )


# ═══════════════════════════════════════
# Mock DeviceConnection（Layer 3 UI 用）
# ═══════════════════════════════════════

@pytest.fixture
def mock_device_connection():
    """创建一个完全 Mock 的 DeviceConnection。

    uiautomator2 默认行为：元素存在、点击成功、返回 mock 文本。
    Airtest 默认行为：分辨率 1080x2400、操作成功。
    测试中可通过 .return_value 覆盖特定行为。
    """
    from apps.test_runner.executors.ui.connect import DeviceConnection

    conn = MagicMock(spec=DeviceConnection)
    conn.serial = "MOCK-DEVICE"

    # ── Mock uiautomator2 ──
    u2 = MagicMock()
    # xpath 链式调用默认返回
    xpath_elem = MagicMock()
    xpath_elem.exists = True
    xpath_elem.click.return_value = None
    xpath_elem.long_click.return_value = None
    xpath_elem.get.return_value.attrib = {"text": "mock_text"}
    xpath_elem.all.return_value = [MagicMock()]
    u2.xpath.return_value = xpath_elem
    # toast
    u2.toast.get_message.return_value = None
    # settings
    u2.settings = {}
    # info
    u2.info = {"productName": "MockPhone", "brand": "MockBrand", "sdkInt": 33}
    conn.u2 = u2

    # ── Mock Airtest ──
    airtest = MagicMock()
    airtest.get_current_resolution.return_value = (1080, 2400)
    airtest.swipe.return_value = None
    airtest.stop_app.return_value = None
    airtest.shell.return_value = None
    airtest.display_info = {"displayWidth": 1080, "displayHeight": 2400}
    conn.airtest = airtest

    conn.info = {
        "serial": "MOCK-DEVICE",
        "displayWidth": 1080,
        "displayHeight": 2400,
        "productName": "MockPhone",
        "brand": "MockBrand",
        "sdkInt": 33,
    }
    return conn


@pytest.fixture
def mock_device_adapter(mock_device_connection):
    """基于 mock_device_connection 创建 DeviceAdapter。"""
    from apps.test_runner.executors.ui.adapter import DeviceAdapter
    return DeviceAdapter(
        device_conn=mock_device_connection,
        package_name="com.test.app",
        logger=MagicMock(),
        should_stop=lambda: False,
    )


# ═══════════════════════════════════════
# Mock ApiAdapter（Layer 3 API 用）
# ═══════════════════════════════════════

@pytest.fixture
def mock_api_adapter():
    """创建一个 Mock ApiAdapter。

    默认 execute_step 返回成功响应。
    测试中可设置 execute_step.return_value 模拟不同场景。
    """
    adapter = MagicMock()
    adapter.execute_step.return_value = {
        "status_code": 200,
        "response_body": {"status": "ok"},
        "response_headers": {"Content-Type": "application/json"},
        "duration_ms": 50.0,
        "result": "pass",
        "curl_command": "curl -X GET http://test.local/api/status",
    }
    adapter.stopped.return_value = False
    adapter.log = MagicMock()
    adapter.get_log_buffer.return_value = []
    adapter.clear_log_buffer = MagicMock()
    adapter.base_url = "http://test.local"
    return adapter


# ═══════════════════════════════════════
# Mock WebAdapter（Layer 3 Web 用）
# ═══════════════════════════════════════

@pytest.fixture
def mock_web_adapter():
    """创建一个 Mock WebAdapter（AsyncMock）。

    所有 Playwright 交互均被 mock，不需要真实浏览器。
    """
    adapter = MagicMock()
    adapter._navigate = AsyncMock(return_value={"result": "pass", "message": "ok"})
    adapter._click = AsyncMock(return_value={"result": "pass", "message": "clicked"})
    adapter._fill = AsyncMock(return_value={"result": "pass", "message": "filled"})
    adapter._wait_for = AsyncMock(return_value={"result": "pass", "message": "waited"})
    adapter._verify_text = MagicMock(return_value=True)
    adapter._screenshot = AsyncMock(return_value=b"fake_png_bytes")
    adapter._screenshot_to_path = AsyncMock(return_value="/fake/path/screenshot.png")
    adapter._element_bounds = AsyncMock(return_value={"x": 100, "y": 200, "width": 300, "height": 50})
    adapter._ensure_browser = AsyncMock()
    adapter._page = MagicMock()
    adapter._page.content = AsyncMock(return_value="<html>ok</html>")
    adapter.stopped.return_value = False
    adapter.log = MagicMock()
    adapter.get_log_buffer.return_value = []
    adapter.clear_log_buffer = MagicMock()
    adapter.run_watchers = AsyncMock(return_value=None)
    adapter.reset_state = AsyncMock(return_value=None)
    adapter.close = AsyncMock(return_value=None)
    return adapter


# ═══════════════════════════════════════
# RecordingCallback（所有 Runner 测试用）
# ═══════════════════════════════════════

class RecordingCallback:
    """记录所有回调调用，供测试断言。

    实现 TestRunnerCallback 的全部 10 个 async 方法。
    每次调用追加到 self.calls 列表。
    """

    def __init__(self):
        self.calls: list[tuple] = []

    async def _record(self, *args):
        self.calls.append(args)

    async def on_log(self, run_id, message):
        await self._record("log", run_id, message)

    async def on_run_started(self, run_id):
        await self._record("run_started", run_id)

    async def on_case_started(self, run_id, case_id, case_title, loop_count):
        await self._record("case_started", run_id, case_id, case_title, loop_count)

    async def on_step_started(self, run_id, case_id, iteration, step_index,
                              total_steps, step_type, description):
        await self._record("step_started", run_id, case_id, iteration, step_index,
                           total_steps, step_type, description)

    async def on_step_result(self, run_id, case_id, iteration, step_index,
                             total_steps, step_type, description, result):
        await self._record("step_result", run_id, case_id, iteration, step_index,
                           total_steps, step_type, description, result)

    async def on_iteration_result(self, run_id, case_id, iteration, result, duration_ms):
        await self._record("iteration_result", run_id, case_id, iteration, result, duration_ms)

    async def on_case_finished(self, run_id, case_id, pass_count, fail_count, rate):
        await self._record("case_finished", run_id, case_id, pass_count, fail_count, rate)

    async def on_run_finished(self, run_id, summary, log_path):
        await self._record("run_finished", run_id, summary, log_path)

    async def on_device_error(self, run_id, error):
        await self._record("device_error", run_id, error)

    async def on_heartbeat(self, run_id):
        await self._record("heartbeat", run_id)
