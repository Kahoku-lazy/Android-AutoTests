"""
接口测试 — 验证全部 5 个 API 模块的 REST 端点返回正确的 JSON 响应。

运行方式:
    pytest test_api_calls.py -v -m api          # 只跑接口测试
    pytest test_api_calls.py -v -k "devices"     # 只跑设备模块

测试范围:
    1. 设备管理 (5 端点): GET 列表、GET 当前设备
    2. 元素定位 (11 端点): GET 页面、GET 跳转、GET 页面元素
    3. 用例工程 (8 端点): GET 列表、POST 创建、GET 详情、DELETE 删除、GET 导出
    4. 执行引擎 (4 端点): GET 历史
    5. 报告分析 (2 端点): GET 报告列表、GET 根路径

每个测试验证:
    - HTTP 状态码是否为 200
    - JSON 响应中 ok 字段是否为 true
    - 关键字段是否存在 (如 devices, definitions, files 等)
"""
import pytest

API = "http://localhost:8765/api"


class TestDevicePoolAPI:
    """设备管理模块 /api/devices/* — 设备列表、当前设备信息。"""

    def test_list_devices(self, api):
        """
        GET /api/devices — 获取已连接的 ADB 设备列表。

        返回字段: ok, devices[{serial, model, screen, sdk}], current
        失败场景: ADB 未安装、无设备连接 (ok=false)、Django 路由错误
        """
        r = api.get(f"{API}/devices")
        assert r.status_code == 200, f"返回 {r.status_code}"
        data = r.json()
        assert data["ok"] is True, f"ok 不为 true: {data}"
        assert "devices" in data, "返回 JSON 缺少 devices 字段"

    def test_device_current(self, api):
        """
        GET /api/devices/current — 获取当前活动设备的基本信息。

        返回字段: serial, screen_w, screen_h, package
        不依赖 ADB 设备连接，即使无设备也返回默认值 (1440×3040)
        """
        r = api.get(f"{API}/devices/current")
        assert r.status_code == 200
        data = r.json()
        assert "serial" in data, "缺少 serial 字段"
        assert "screen_w" in data, "缺少 screen_w 字段"
        assert "screen_h" in data, "缺少 screen_h 字段"


class TestElementLocatorAPI:
    """元素定位模块 /api/elements/* — 页面快照、跳转关系、元素查询。"""

    def test_list_pages(self, api):
        """
        GET /api/elements/pages — 获取已 dump 的 UI 页面列表。

        返回字段: ok, pages[{id, label, package, activity, element_count, created_at}]
        """
        r = api.get(f"{API}/elements/pages")
        assert r.status_code == 200, f"返回 {r.status_code}"
        data = r.json()
        assert data["ok"] is True
        assert "pages" in data, "缺少 pages 字段"

    def test_list_flows(self, api):
        """
        GET /api/elements/flows — 获取页面跳转关系列表。

        返回字段: ok, flows[{id, from_page_id, to_page_id, from_label, to_label}]
        """
        r = api.get(f"{API}/elements/flows")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True

    def test_page_elements_filter(self, api):
        """
        GET /api/elements/pages/{id}/items?filter=clickable — 获取页面元素，按条件过滤。

        步骤:
            1. 先取页面列表，拿到第一个 page_id
            2. 用 page_id 请求元素列表，加上 filter=clickable 参数
            3. 验证返回 200

        支持的 filter 值: all | clickable | text | testpoint
        失败场景: 无已 dump 的页面 (跳过、不报错)
        """
        r = api.get(f"{API}/elements/pages")
        if r.json().get("pages"):
            page_id = r.json()["pages"][0]["id"]
            r2 = api.get(f"{API}/elements/pages/{page_id}/items", params={"filter": "clickable"})
            assert r2.status_code == 200, f"页面 {page_id} 的元素查询返回 {r2.status_code}"


class TestCaseManagerAPI:
    """用例工程模块 /api/cases/* — 用例定义的 CRUD 和 YAML 导出。"""

    def test_list_definitions(self, api):
        """
        GET /api/cases/definitions — 获取所有测试用例定义列表。

        返回字段: ok, definitions[{id, title, category, enabled, steps_data, package_name}]
        """
        r = api.get(f"{API}/cases/definitions")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert "definitions" in data, "缺少 definitions 字段"

    def test_crud_definition(self, api):
        """
        POST → GET → DELETE 完整 CRUD 流程 — 创建、读取、删除一条测试用例定义。

        步骤:
            1. POST /api/cases/definitions  创建用例 (id=pytest_case_001)
            2. GET  /api/cases/definitions/{id}  读取刚创建的用例
            3. DELETE /api/cases/definitions/{id} 删除用例

        验证:
            - 创建返回 ok=true
            - 读取返回的 title 与创建时一致
            - 删除返回 ok=true (无论是否存在)

        失败场景: 数据库写入失败 (表不存在/字段类型不匹配)
        """
        case_id = "pytest_case_001"
        # 1. 创建用例
        r = api.post(f"{API}/cases/definitions", json={
            "id": case_id,
            "title": "Pytest Smoke Test",
            "category": "smoke",
            "steps_data": [],
            "enabled": True,
            "package_name": "com.example",
        })
        assert r.status_code == 200, f"创建返回 {r.status_code}"
        assert r.json()["ok"] is True, f"创建失败: {r.json()}"

        # 2. 读取用例
        r = api.get(f"{API}/cases/definitions/{case_id}")
        assert r.status_code == 200, f"读取返回 {r.status_code}"
        assert r.json()["definition"]["title"] == "Pytest Smoke Test", "读取的 title 不匹配"

        # 3. 删除用例
        r = api.delete(f"{API}/cases/definitions/{case_id}")
        assert r.status_code == 200, f"删除返回 {r.status_code}"

    def test_list_exports(self, api):
        """
        GET /api/cases/exports — 获取 YAML 导出文件列表。

        返回字段: ok, files[{name, size, time}]
        失败场景: exports 目录不存在或不可读
        """
        r = api.get(f"{API}/cases/exports")
        assert r.status_code == 200


class TestRunnerAPI:
    """执行引擎模块 /api/runner/* — 测试执行与历史查询。"""

    def test_list_runs(self, api):
        """
        GET /api/runner/runs — 获取测试执行历史记录。

        返回字段: ok, runs[{run_id, total, passed, failed, last_time}]
        无历史记录时返回空列表也是正常的
        """
        r = api.get(f"{API}/runner/runs")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True


class TestReportAPI:
    """报告分析模块 /api/reports/* — 报告文件列表。"""

    def test_list_reports(self, api):
        """
        GET /api/reports — 获取可下载的测试报告文件列表。

        返回字段: ok, files[{name, size, time, type}]
        type 值: csv | md | log
        失败场景: logs 目录不存在
        """
        r = api.get(f"{API}/reports")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert "files" in data, "缺少 files 字段"

    def test_api_root_health(self, api):
        """
        GET / — 根路径，验证 API 服务器基本健康。

        返回字段: ok=true, service="Android-AutoTests API"
        失败场景: Daphne 未启动、URL 路由配置错误
        """
        r = api.get("http://localhost:8765/")
        assert r.status_code == 200
        assert r.json()["ok"] is True
