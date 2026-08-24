"""UiEngine 契约测试基类 — L1c §六 EngineContractTest（新引擎必过）。

本基类只定义「协议行为应当如何」，不绑定具体引擎实现：
- 连接流（无线 adb 判定 / USB 跳过 / 连接失败消息映射）
- 感知格式（JPEG bytes / dump→Node / app_current）
- 操作原语转发、XPath 冒烟、生命周期（is_alive/reconnect）

子类职责（见 test_airtest_u2_contract.py）：
- 声明 ENGINE_CLASS 与 CONNECT_ERROR（连接失败异常类型）
- 实现 `_install_mocks(monkeypatch, ad, u2, run)` —— 把本引擎依赖的模块级
  符号（Android 构造 / subprocess / u2.connect）接上假件

注册表联动：新引擎落地时继承本基类；未过即不可注册。
"""

import base64

from types import SimpleNamespace

import numpy as np
import pytest

from models.ui_nodes import Node

SAMPLE_XML = (
    '<?xml version="1.0" encoding="UTF-8"?><hierarchy>'
    '<node class="android.widget.Button" text="确定" bounds="[1,2][11,22]" clickable="true"/>'
    "</hierarchy>"
)


class FakeU2:
    """u2 侧假件（dump/信息/Toast/XPath）。"""

    def __init__(self):
        self.settings = {}
        self.info = {"productName": "Pixel", "displayWidth": 1080, "displayHeight": 2400}
        self.toast = SimpleNamespace(reset=lambda: None, get_message=lambda t: "toast msg")
        self._results = [SAMPLE_XML]

    def dump_hierarchy(self, *a, **k):
        r = self._results.pop(0) if len(self._results) > 1 else self._results[0]
        if isinstance(r, BaseException):
            raise r
        return r

    def app_current(self):
        return {"package": "com.x", "activity": "Main"}

    def xpath(self, expr):
        el = SimpleNamespace(exists=True)
        el.get = lambda: SimpleNamespace(attrib={"text": "确定"})
        el.wait = lambda timeout: True
        return el


class FakeAd:
    """Airtest 侧假件（操作记录 + BGR 截图）。"""

    def __init__(self):
        self.display_info = {"displayWidth": 1080, "displayHeight": 2400}
        self.calls = []

    def snapshot(self, quality=None):
        self.calls.append(("snapshot", quality))
        return np.full((20, 10, 3), (255, 0, 0), dtype=np.uint8)  # BGR 红

    def touch(self, *a, **k):
        self.calls.append(("touch", a, k))

    def swipe(self, *a, **k):
        self.calls.append(("swipe", a, k))

    def text(self, t):
        self.calls.append(("text", t))

    def shell(self, cmd):
        self.calls.append(("shell", cmd))
        return "out"

    def start_app(self, pkg):
        self.calls.append(("start_app", pkg))

    def stop_app(self, pkg):
        self.calls.append(("stop_app", pkg))


class EngineContractTestBase:
    """协议行为契约 —— 子类提供引擎类与 mock 接线。"""

    ENGINE_CLASS = None  # 子类声明
    CONNECT_ERROR = RuntimeError  # 连接失败异常类型（子类可覆盖为具体异常）

    @pytest.fixture
    def engine_cls(self):
        assert self.ENGINE_CLASS is not None, "子类必须声明 ENGINE_CLASS"
        return self.ENGINE_CLASS

    @staticmethod
    def _default_run():
        return lambda *a, **k: SimpleNamespace(stdout="connected", stderr="")

    def _make(self, monkeypatch, *, ad=None, u2=None, run=None):
        """接线 mock 并构造引擎（不连接）。"""
        ad = ad or FakeAd()
        u2 = u2 or FakeU2()
        run = run or self._default_run()
        self._install_mocks(monkeypatch, ad=ad, u2=u2, run=run)
        return self.ENGINE_CLASS()

    def _build(self, monkeypatch, *, ad=None, u2=None, run=None):
        """构造并完成无线连接；返回 (engine, ad, u2)。"""
        ad = ad or FakeAd()
        u2 = u2 or FakeU2()
        run = run or self._default_run()
        self._install_mocks(monkeypatch, ad=ad, u2=u2, run=run)
        engine = self.ENGINE_CLASS()
        engine.connect("SN", "1.2.3.4:5555")
        return engine, ad, u2

    # ── 子类实现：把假件接到引擎依赖的模块符号上 ──

    def _install_mocks(self, monkeypatch, *, ad, u2, run):
        raise NotImplementedError("子类实现 mock 接线（Android/subprocess/u2.connect…）")


class CapabilitiesContract(EngineContractTestBase):
    def test_capabilities_declared(self, engine_cls):
        caps = engine_cls().capabilities
        assert caps.xpath_locate is True
        assert caps.toast_wait is True
        assert caps.ocr is False


class ConnectFlowContract(EngineContractTestBase):
    def test_wifi_connect_success(self, monkeypatch):
        engine, fake_ad, fake_u2 = self._build(monkeypatch)
        assert engine.airtest is fake_ad
        assert engine.u2 is fake_u2
        assert engine.device_info["displayWidth"] == 1080
        assert engine.device_info["productName"] == "Pixel"

    def test_usb_skips_adb(self, monkeypatch):
        def _boom(*a, **k):
            raise AssertionError("USB 不应 adb connect")

        engine = self._make(monkeypatch, run=_boom)
        engine.connect("SERIAL")  # 无冒号 → 跳过 adb
        assert engine.device_info["displayWidth"] == 1080

    def test_connect_failure_message_mapping(self, monkeypatch):
        class _BadAd:
            @property
            def display_info(self):
                raise RuntimeError("atx-agent offline")

        engine = self._make(monkeypatch, ad=_BadAd())
        with pytest.raises(self.CONNECT_ERROR, match="ATX Agent not running"):
            engine.connect("SN", "1.2.3.4:5555")


class PerceptionContract(EngineContractTestBase):
    def test_screenshot_returns_jpeg_bytes(self, monkeypatch):
        engine, _, _ = self._build(monkeypatch)
        raw = engine.screenshot()
        assert raw[:2] == b"\xff\xd8"

    def test_screenshot_b64_and_file(self, monkeypatch, tmp_path):
        engine, _, _ = self._build(monkeypatch)
        raw = base64.b64decode(engine.screenshot_b64())
        assert raw[:2] == b"\xff\xd8"

        path = tmp_path / "shot.png"
        engine.screenshot_file(str(path))
        assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

    def test_dump_hierarchy_returns_nodes(self, monkeypatch):
        engine, _, _ = self._build(monkeypatch)
        nodes = engine.dump_hierarchy()
        assert isinstance(nodes, list)
        assert all(isinstance(n, Node) for n in nodes)
        # 现状行为：根元素计入节点
        assert len(nodes) == 2
        assert nodes[1].text == "确定"
        assert (nodes[1].x, nodes[1].y) == (1, 2)
        assert nodes[1].clickable is True

    def test_dump_fallback_and_failure(self, monkeypatch):
        engine, _, fake_u2 = self._build(monkeypatch)
        fake_u2._results = [RuntimeError("x"), SAMPLE_XML]
        nodes = engine.dump_hierarchy()
        assert len(nodes) == 2

        fake_u2._results = [RuntimeError("a"), RuntimeError("b"), None]
        with pytest.raises(RuntimeError, match="all strategies failed"):
            engine.dump_hierarchy()

    def test_app_current(self, monkeypatch):
        engine, _, _ = self._build(monkeypatch)
        assert engine.app_current() == {"package": "com.x", "activity": "Main"}


class OperationsContract(EngineContractTestBase):
    def test_operations_forward(self, monkeypatch):
        engine, fake_ad, _ = self._build(monkeypatch)
        engine.click(1, 2)
        engine.long_click(1, 2, 0.8)
        engine.swipe(1, 2, 3, 4)
        engine.input_text("hi")
        engine.press_key("HOME")
        engine.start_app("com.x")
        engine.stop_app("com.x")
        assert ("touch", ((1, 2),), {}) in fake_ad.calls
        assert ("swipe", ((1, 2), (3, 4)), {"duration": 0.5}) in fake_ad.calls
        assert ("text", "hi") in fake_ad.calls
        assert ("shell", "input keyevent HOME") in fake_ad.calls
        assert ("start_app", "com.x") in fake_ad.calls
        assert ("stop_app", "com.x") in fake_ad.calls

    def test_shell_returns_output(self, monkeypatch):
        engine, _, _ = self._build(monkeypatch)
        assert engine.shell("ls") == "out"


class XPathContract(EngineContractTestBase):
    def test_exists_get_text_wait_toast(self, monkeypatch):
        engine, _, _ = self._build(monkeypatch)
        assert engine.exists("//x") is True
        assert engine.get_text("//x") == "确定"
        assert engine.wait_toast("确定", timeout=0.5) is True


class LifecycleContract(EngineContractTestBase):
    def test_is_alive_disconnect_reconnect(self, monkeypatch):
        engine, _, _ = self._build(monkeypatch)
        assert engine.is_alive() is True
        engine.disconnect()
        assert engine.is_alive() is False
        assert engine.reconnect() is True
        assert engine.is_alive() is True
