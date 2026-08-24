"""engines 注册表工厂单元测试（Step 3a 验收）。"""

import sys

from types import ModuleType

import pytest

from engines import registry

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


@pytest.fixture(autouse=True)
def _clear_cache():
    registry._instances.clear()
    yield
    registry._instances.clear()


def _inject_fake_engine(monkeypatch, module_path, attr="FakeEngine"):
    mod = ModuleType(module_path)
    fake_cls = type(attr, (), {})
    setattr(mod, attr, fake_cls)
    monkeypatch.setitem(sys.modules, module_path, mod)
    return fake_cls


class TestRegistry:
    def test_default_engine_name(self):
        assert registry.DEFAULT_ENGINE == "airtest_u2"

    def test_unknown_engine_raises(self):
        with pytest.raises(registry.ConfigurationError, match="Unknown engine 'nope'"):
            registry.get_device_engine("nope")

    def test_airtest_u2_now_importable(self):
        # 3b 落地实现后：airtest_u2 可构建（不连接设备）
        from engines.android.airtest_u2 import AirtestU2Engine

        engine = registry.get_device_engine("airtest_u2")
        assert isinstance(engine, AirtestU2Engine)

    def test_registered_but_missing_module_raises(self):
        registry.ENGINE_REGISTRY["ghost"] = "engines.android.ghost.Nope"
        try:
            with pytest.raises(registry.ConfigurationError, match="not importable"):
                registry.get_device_engine("ghost")
        finally:
            registry.ENGINE_REGISTRY.pop("ghost", None)

    def test_known_engine_returns_instance_and_caches(self, monkeypatch):
        fake_cls = _inject_fake_engine(monkeypatch, "engines.android.cloud")
        registry.ENGINE_REGISTRY["cloud"] = "engines.android.cloud.FakeEngine"
        try:
            first = registry.get_device_engine("cloud")
            second = registry.get_device_engine("cloud")
            assert isinstance(first, fake_cls)
            assert first is second  # 实例缓存
        finally:
            registry.ENGINE_REGISTRY.pop("cloud", None)

    def test_build_failure_raises(self, monkeypatch):
        class _Boom:
            def __init__(self):
                raise RuntimeError("init boom")

        mod = ModuleType("engines.android.boom")
        setattr(mod, "BoomEngine", _Boom)
        monkeypatch.setitem(sys.modules, "engines.android.boom", mod)
        registry.ENGINE_REGISTRY["boom"] = "engines.android.boom.BoomEngine"
        try:
            with pytest.raises(registry.ConfigurationError, match="failed to build"):
                registry.get_device_engine("boom")
        finally:
            registry.ENGINE_REGISTRY.pop("boom", None)
