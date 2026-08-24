"""AirtestU2Engine 契约测试 — 继承 EngineContractTestBase（新引擎必过基类）。

基类覆盖协议行为（连接流/感知/操作/XPath/生命周期，全 mock）；
本文件只做两件事：
1. 接线：把基类假件接到 AirtestU2Engine 依赖的模块符号（Android/subprocess/u2.connect）
2. AirtestU2 特有的静态辅助测试（probe_u2 / fetch_device_info）
"""

import subprocess

from types import SimpleNamespace

import pytest

from engines.android import airtest_u2 as engine_module
from engines.android.airtest_u2 import AirtestU2Engine, EngineConnectError
from tests.engines.contract_base import (
    CapabilitiesContract,
    ConnectFlowContract,
    EngineContractTestBase,
    FakeU2,
    LifecycleContract,
    OperationsContract,
    PerceptionContract,
    XPathContract,
)

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


class TestAirtestU2Contract(EngineContractTestBase):
    """接线基类契约到 AirtestU2Engine。"""

    ENGINE_CLASS = AirtestU2Engine
    CONNECT_ERROR = EngineConnectError

    def _install_mocks(self, monkeypatch, *, ad, u2, run):
        monkeypatch.setattr(engine_module, "Android", lambda **kw: ad)
        monkeypatch.setattr(
            engine_module,
            "subprocess",
            SimpleNamespace(run=run, TimeoutExpired=subprocess.TimeoutExpired),
        )
        monkeypatch.setattr(engine_module.u2, "connect", lambda target: u2)


# 基类契约按当前引擎参数化实例化（跑同一套协议行为断言）
class TestAirtestCapabilities(CapabilitiesContract, TestAirtestU2Contract):
    pass


class TestAirtestConnectFlow(ConnectFlowContract, TestAirtestU2Contract):
    pass


class TestAirtestPerception(PerceptionContract, TestAirtestU2Contract):
    pass


class TestAirtestOperations(OperationsContract, TestAirtestU2Contract):
    pass


class TestAirtestXPath(XPathContract, TestAirtestU2Contract):
    pass


class TestAirtestLifecycle(LifecycleContract, TestAirtestU2Contract):
    pass


class TestDisplayInfoBackfill:
    """真机发现 #2：Airtest display_info 缺宽高键时从 u2 info 补齐。"""

    def test_missing_width_height_backfilled_from_u2(self, monkeypatch):
        class _ThinAd:
            display_info = {"productName": "Pixel"}  # 真机形态：缺 displayWidth/Height

        monkeypatch.setattr(engine_module, "Android", lambda **kw: _ThinAd())
        monkeypatch.setattr(engine_module.u2, "connect", lambda t: FakeU2())
        monkeypatch.setattr(
            engine_module,
            "subprocess",
            SimpleNamespace(
                run=lambda *a, **k: SimpleNamespace(stdout="connected", stderr=""),
                TimeoutExpired=subprocess.TimeoutExpired,
            ),
        )
        engine = AirtestU2Engine()
        engine.connect("SN", "1.2.3.4:5555")
        assert engine.device_info["displayWidth"] == 1080  # 自 u2 info 补齐
        assert engine.device_info["displayHeight"] == 2400


class TestStaticHelpers:
    """AirtestU2 特有静态辅助（不在通用契约内）。"""

    def test_probe_u2_ok_and_failure(self, monkeypatch):
        monkeypatch.setattr(engine_module.u2, "connect", lambda t: SimpleNamespace(info={}))
        engine_module.AirtestU2Engine.probe_u2("S")  # 不抛

        def _raise(t):
            raise RuntimeError("atx-agent offline")

        monkeypatch.setattr(engine_module.u2, "connect", _raise)
        with pytest.raises(EngineConnectError, match="atx-agent offline"):
            engine_module.AirtestU2Engine.probe_u2("S")

    def test_fetch_device_info(self, monkeypatch):
        monkeypatch.setattr(
            engine_module.u2,
            "connect",
            lambda t: SimpleNamespace(info={"productName": "Pixel", "sdkInt": 30}),
        )
        info = engine_module.AirtestU2Engine.fetch_device_info("S")
        assert info == {"productName": "Pixel", "sdkInt": 30}
