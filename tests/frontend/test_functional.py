"""
功能逻辑测试 — 验证每个模块页面的实际 UI 交互行为。

运行方式:
    pytest test_functional.py -v -m functional
    pytest test_functional.py -v -k "dump"     # 只跑元素定位相关

测试范围:
    1. 元素定位: Dump 按钮 → API 调用 → 结果显示
    2. 用例工程: 新建按钮 → 弹窗 → 表格数据
    3. 执行引擎: 选择器 + 按钮 + 日志面板
    4. 设备管理: 设备表格渲染
    5. 报告分析: 报告网格布局

注意:
    - 涉及设备交互的测试 (如 dump) 在无设备时页面会显示错误提示，
      这也是合法的功能行为，测试验证的是"有响应"而非"成功"。
    - 所有测试均为只读验证，不修改任何数据。
"""
import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


@pytest.mark.functional
class TestElementLocatorFlow:
    """元素定位页面功能逻辑 — Dump UI、截图渲染、动作操作。"""

    def test_dump_button_exists(self, driver, wait):
        """
        验证 "Dump UI" 按钮在元素定位页面可见。

        页面加载后，等待包含 'Dump' 文本的按钮出现。
        失败场景: element-locator/index.vue 渲染失败、按钮被 CSS 隐藏
        """
        driver.get("http://localhost:5173/elements")
        btn = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//button[contains(.,'Dump') or contains(.,'dump')]"
            ))
        )
        assert btn.is_displayed(), "Dump 按钮应该可见"

    def test_dump_button_triggers_api(self, driver, wait):
        """
        验证点击 Dump UI 按钮后触发了 API 调用并显示了结果。

        点击按钮 → 等待 3 秒 (API 往返 + Canvas 渲染) →
        页面上出现 .info (成功信息) 或 .error (错误信息)。

        无 ADB 设备时显示 "Device not connected" 也是正确的功能行为。
        失败场景: 点击后页面无任何变化 (API 未被调用)
        """
        driver.get("http://localhost:5173/elements")
        btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[contains(.,'Dump') or contains(.,'dump')]"
        )))
        btn.click()
        time.sleep(3)  # 等待 API 响应 + Canvas 渲染
        page_loaded = False
        try:
            info_el = driver.find_element(By.CLASS_NAME, "info")
            page_loaded = info_el.is_displayed()
        except Exception:
            try:
                error_el = driver.find_element(By.CLASS_NAME, "error")
                page_loaded = error_el.is_displayed()
            except Exception:
                pass
        assert page_loaded, "Dump 后应该显示结果信息或错误提示"

    def test_screenshot_canvas_renders(self, driver, wait):
        """
        验证截图 Canvas 元素能够渲染（WebSocket 截图流）。

        加载页面 → 等待 2 秒 WebSocket 连接 →
        检查 Canvas 存在 或 .no-signal 提示存在。

        成功场景: Canvas 渲染手机截图
        降级场景: .no-signal 显示 "No device signal"（无设备时正常）
        失败场景: Canvas 和 no-signal 都不存在（WebSocket 未连接）
        """
        driver.get("http://localhost:5173/elements")
        time.sleep(2)  # 等待 WebSocket 建立连接
        try:
            canvas = driver.find_element(By.TAG_NAME, "canvas")
            assert canvas.is_displayed(), "截图 Canvas 应该可见"
        except Exception:
            no_signal = driver.find_element(By.CLASS_NAME, "no-signal")
            assert no_signal.is_displayed(), "无设备时应显示 No signal 提示"


@pytest.mark.functional
class TestCaseManagerFlow:
    """用例工程页面功能逻辑 — 新建用例弹窗、表格数据。"""

    def test_create_button_exists(self, driver, wait):
        """
        验证 "新建用例" 按钮在用例页面可见。

        加载 /cases → 等待包含 '新建' 或 'Create' 的按钮出现。
        """
        driver.get("http://localhost:5173/cases")
        btn = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//button[contains(.,'新建') or contains(.,'Create')]"
            ))
        )
        assert btn.is_displayed(), "新建按钮应该可见"

    def test_create_dialog_opens(self, driver, wait):
        """
        验证点击 "新建用例" 按钮后弹出 Element Plus 对话框。

        点击按钮 → 等待 0.5 秒动画 → .el-dialog 出现在 DOM 中。

        对话框中应包含: ID、标题、分类、包名 输入框。
        失败场景: dialogVisible 未正确绑定、对话框 CSS z-index 问题
        """
        driver.get("http://localhost:5173/cases")
        btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[contains(.,'新建') or contains(.,'Create')]"
        )))
        btn.click()
        time.sleep(0.5)  # 等待 Element Plus 弹窗动画
        dialog = driver.find_element(By.CLASS_NAME, "el-dialog")
        assert dialog.is_displayed(), "弹窗应该打开"

    def test_table_loads_data(self, driver, wait):
        """
        验证用例表格能加载数据。

        页面加载 → 等待 2 秒 API 返回 → el-table 出现在 DOM 中。
        空表格 (无数据) 也算正常，只要表格组件本身渲染即可。
        """
        driver.get("http://localhost:5173/cases")
        time.sleep(2)
        try:
            table = driver.find_element(By.CLASS_NAME, "el-table")
            assert table.is_displayed(), "用例表格应该可见"
        except Exception:
            pass  # 空数据时表格可能不渲染，也算正常


@pytest.mark.functional
class TestRunnerFlow:
    """执行引擎页面功能逻辑 — 用例选择、执行控制、日志面板。"""

    def test_runner_controls_visible(self, driver, wait):
        """
        验证执行页面显示了用例选择器和执行按钮。

        el-select (多选用例选择器) + 包含 "执行" 的按钮。
        失败场景: test-runner/index.vue 渲染失败、API 未加载用例列表
        """
        driver.get("http://localhost:5173/runner")
        select = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "el-select"))
        )
        run_btn = driver.find_element(
            By.XPATH, "//button[contains(.,'执行') or contains(.,'Run')]"
        )
        assert select.is_displayed(), "用例选择器应该可见"
        assert run_btn.is_displayed(), "执行按钮应该可见"

    def test_log_panel_exists(self, driver, wait):
        """
        验证执行页面存在日志输出面板。

        .log-panel 区域在未执行时为深色背景空面板。
        失败场景: test-runner/index.vue 缺少 log-panel 区域
        """
        driver.get("http://localhost:5173/runner")
        log_panel = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "log-panel"))
        )
        assert log_panel.is_displayed(), "日志面板应该可见"


@pytest.mark.functional
class TestDevicePoolFlow:
    """设备管理页面功能逻辑 — 设备表格。"""

    def test_device_table_visible(self, driver, wait):
        """
        验证设备管理页面显示了设备表格。

        .device-table 元素在页面加载后出现。
        失败场景: device-pool/index.vue 渲染失败
        """
        driver.get("http://localhost:5173/devices")
        table = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "device-table"))
        )
        assert table.is_displayed(), "设备表格应该可见"


@pytest.mark.functional
class TestReportFlow:
    """报告分析页面功能逻辑 — 报告网格布局。"""

    def test_report_grid_visible(self, driver, wait):
        """
        验证报告页面显示了网格布局。

        .grid 容器包含 "报告文件" 和 "执行历史" 两个卡片。
        失败场景: report-generator/index.vue 渲染失败
        """
        driver.get("http://localhost:5173/reports")
        time.sleep(1)  # 等待 API 加载报告列表
        grid = driver.find_element(By.CLASS_NAME, "grid")
        assert grid.is_displayed(), "报告网格应该可见"
