"""
页面切换测试 — 验证 Vue Router 路由和侧边栏导航是否正常工作。

运行方式:
    pytest test_page_navigation.py -v -m navigation

测试场景:
    1. 应用加载后侧边栏是否可见
    2. 5 个页面各自能否通过 URL 直接访问
    3. 5 个页面各自能否通过侧边栏点击访问
    4. 侧边栏恰好有 5 个导航项
    5. 根路径 / 是否自动跳转到 /elements
    6. 页面切换时侧边栏是否保持可见

注意: 这些测试需要 Vite 前端服务器在 :5173 运行
"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


# 5 个页面的路径、中文标签、模块名
NAV_PAGES = [
    ("/devices", "设备管理", "device-pool"),
    ("/elements", "元素定位", "element-locator"),
    ("/cases",    "用例工程", "case-manager"),
    ("/runner",   "执行引擎", "test-runner"),
    ("/reports",  "测试报告", "report-generator"),
]


@pytest.mark.navigation
class TestPageNavigation:
    """页面路由导航测试 — URL 直接访问 + 侧边栏点击两种方式。"""

    def test_app_loads(self, driver, wait):
        """
        验证应用首次加载后侧边栏就可见。

        访问根路径 → 自动跳转到 /elements → 侧边栏渲染
        失败场景: Vue 未启动、App.vue 渲染失败、CSS 隐藏了侧边栏
        """
        driver.get("http://localhost:5173")
        sidebar = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "sidebar"))
        )
        assert sidebar.is_displayed(), "侧边栏应该可见"

    @pytest.mark.parametrize("path,label,module", NAV_PAGES)
    def test_page_loads_via_url(self, driver, wait, path, label, module):
        """
        验证 5 个页面各自能通过浏览器 URL 直接访问。

        访问 http://localhost:5173/{path} → 页面加载 → 侧边栏对应项高亮
        失败场景: router.js 未注册路由、Vue 组件 import 失败
        """
        driver.get(f"http://localhost:5173{path}")
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        active_link = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".nav-item.active"))
        )
        assert label in active_link.text or module in driver.current_url, \
            f"页面 {path} 应该处于激活状态"

    @pytest.mark.parametrize("path,label,module", NAV_PAGES)
    def test_page_loads_via_sidebar(self, driver, wait, path, label, module):
        """
        验证 5 个页面各自能通过点击侧边栏导航项访问。

        从根路径出发 → 点击侧边栏对应项 → URL 变为目标 path
        失败场景: 导航项未渲染、路由 push 失败、Vue Router 未配置
        """
        driver.get("http://localhost:5173")
        nav_link = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                f"//a[contains(@class,'nav-item')]//span[contains(text(),'{label}')]/.."
            ))
        )
        nav_link.click()
        wait.until(lambda d: path in d.current_url or
                             f"/{module}" in d.current_url.lower().replace('-', ''))
        assert path in driver.current_url or path.split('/')[-1] in driver.current_url, \
            f"点击侧边栏 {label} 后 URL 应该包含 {path}"

    def test_sidebar_has_5_items(self, driver, wait):
        """
        验证侧边栏恰好有 5 个导航项。

        5 个模块对应 5 个 .nav-item 元素。
        失败场景: 某个模块的菜单项未在 AppSidebar.vue 中注册
        """
        driver.get("http://localhost:5173")
        items = wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "nav-item"))
        )
        assert len(items) == 5, f"预期 5 个导航项，实际 {len(items)} 个"

    def test_default_redirect_to_elements(self, driver, wait):
        """
        验证访问根路径 / 自动重定向到 /elements。

        router.js 配置: { path: '/:pathMatch(.*)*', redirect: '/elements' }
        失败场景: router.js 未配置通配重定向
        """
        driver.get("http://localhost:5173/")
        wait.until(lambda d: "/elements" in d.current_url)
        assert "/elements" in driver.current_url, "根路径应该重定向到 /elements"

    def test_page_switch_preserves_sidebar(self, driver, wait):
        """
        验证在不同页面之间切换时侧边栏始终保持可见。

        先加载 /elements → 切换到 /devices → 切换到 /cases，
        每一步都确认侧边栏仍在 DOM 中。

        失败场景: sidebar 只在某些页面渲染 (可能是 App.vue 布局问题)
        """
        driver.get("http://localhost:5173/elements")
        sidebar = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "sidebar"))
        )
        for path, label, _ in NAV_PAGES[1:3]:  # 测试 2 次切换
            nav = driver.find_element(
                By.XPATH,
                f"//a[contains(@class,'nav-item')]//span[contains(text(),'{label}')]/.."
            )
            nav.click()
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "sidebar")))
        assert sidebar.is_displayed(), "切换页面后侧边栏应该仍然可见"
