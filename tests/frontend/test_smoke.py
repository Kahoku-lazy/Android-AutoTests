"""
冒烟测试 — 平台启动后最先运行，验证基本健康状态。

运行方式:
    pytest test_smoke.py -v -m smoke          # 只跑冒烟测试
    pytest test_smoke.py -v -k "not ws"        # 跳过 WebSocket 测试

测试范围:
    1. Django 后端是否响应
    2. Vue 前端是否能加载 (无浏览器报错)
    3. 全部 5 个 API 模块是否可访问
    4. WebSocket 截图端点是否可连接
"""
import pytest


@pytest.mark.smoke
class TestSmoke:
    """平台基本健康检查 — 后端、前端、API、WebSocket 四项最基础验证。"""

    def test_backend_alive(self, api):
        """
        验证 Django 后端根路径返回健康状态。

        预期: GET / → 200, {"ok": true}
        失败场景: Daphne 未启动、端口冲突、Django 加载异常
        """
        r = api.get("http://localhost:8765/")
        assert r.status_code == 200, f"后端返回 {r.status_code}，可能未启动"
        assert r.json()["ok"] is True, "后端健康检查失败"

    def test_frontend_alive(self, driver, wait):
        """
        验证 Vue 前端页面能完整加载且浏览器控制台无严重报错。

        加载 /elements 页面 (默认重定向目标)，等待 DOM ready，
        然后检查浏览器 console 日志中是否存在 SEVERE 级别错误。

        失败场景: Vite 未启动、JS 模块加载失败、Vue 组件渲染异常
        """
        driver.get("http://localhost:5173")
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        logs = driver.get_log("browser")
        severe = [l for l in logs if l["level"] == "SEVERE"]
        assert len(severe) == 0, f"浏览器控制台有严重错误: {severe}"

    def test_all_api_modules_respond(self, api):
        """
        验证全部 5 个 API 模块的 GET 端点均返回 200。

        覆盖模块:
            /api/devices          — 设备管理
            /api/devices/current  — 当前设备信息
            /api/elements/pages   — 元素定位 (页面列表)
            /api/elements/flows   — 元素定位 (跳转关系)
            /api/cases/definitions— 用例工程 (用例列表)
            /api/runner/runs      — 执行引擎 (执行历史)
            /api/reports          — 报告分析 (报告列表)

        失败场景: 某个模块路由未注册、数据库表不存在 (500)
        """
        endpoints = [
            "/api/devices",
            "/api/devices/current",
            "/api/elements/pages",
            "/api/elements/flows",
            "/api/cases/definitions",
            "/api/runner/runs",
            "/api/reports",
        ]
        for ep in endpoints:
            r = api.get(f"http://localhost:8765{ep}")
            assert r.status_code == 200, f"端点 {ep} 返回 {r.status_code}，预期 200"

    def test_ws_screenshot_endpoint_accessible(self):
        """
        验证 WebSocket 实时截图端点可以建立连接。

        连接 ws://localhost:8765/ws/screenshot，
        能成功握手即表示 Channels + ScreenshotConsumer 正常工作。

        失败场景: Daphne 未启动、Channels 路由未配置、端口不可达
        """
        import asyncio
        import websockets

        async def check():
            try:
                async with websockets.connect("ws://localhost:8765/ws/screenshot") as ws:
                    return True  # 握手成功即通过
            except Exception:
                return False

        result = asyncio.run(check())
        assert result, "WebSocket 截图端点无法连接"
