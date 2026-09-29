"""灰盒·单元测试 — 日志证据的 Django 侧装配与动作打点契约。

零数据库、零设备：
1. `ensure_log_evidence` 在平台总开关关闭、或**没有任何端口在监听**时返回 None（验收降级）；
2. 有端口在监听时给出提供者，读窗按平台配置补齐等待时长（等到「动作 + 取证阈值」）；
3. 产生副作用的动作工具打点 `action_time`，只读工具不打（AST 契约对拍，读源码不改源码）。
"""

from __future__ import annotations

import ast
import socket
import time

from pathlib import Path

import pytest

from django.test import override_settings

from apps.ai_assistant.log_evidence import DeviceLogEvidence, build_config, ensure_log_evidence
from engines.device.logbus import LogBusConfig, LogSourceSpec, start_log_bus, stop_log_bus

TOOLS_SOURCE = Path(__file__).resolve().parents[3] / "apps" / "ai_assistant" / "tools.py"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


# 产生设备副作用的动作工具（必须打点）
SIDE_EFFECT_TOOLS = {
    "app_control",
    "tap_screen",
    "swipe_screen",
    "press_key",
    "input_text",
    "click_ratio",
    "drag_ratio",
    "xpath_action",
}
# 只读工具（不得打点）
READ_ONLY_TOOLS = {"list_devices", "list_apps", "current_app", "screenshot_page"}


class _FakeBus:
    """记录调用参数的假总线（不启动采集、不占端口）。"""

    def __init__(self) -> None:
        self.kwargs: dict = {}

    def open_window(self, device: str, label: str = "") -> str:
        return "w1"

    def read_window(
        self,
        device: str,
        window_id: str = "",
        action_times: list[str] | None = None,
        wait_seconds: float = 0.0,
    ) -> dict:
        self.kwargs = {
            "device": device,
            "window_id": window_id,
            "action_times": list(action_times or []),
            "wait_seconds": wait_seconds,
        }
        return {"conclusion": "no_log"}


@override_settings(DEVICE_LOG_ENABLED=False)
def test_provider_is_none_when_disabled() -> None:
    """开关关闭 → 不提供日志证据（任务照常执行）。"""
    assert ensure_log_evidence() is None


@override_settings(
    DEVICE_LOG_ENABLED=True,
    DEVICE_LOG_TCP_PORT=0,
    DEVICE_LOG_SERIAL_PORT="",
)
def test_provider_is_none_when_no_port_is_listening() -> None:
    """平台开着但没有任何端口在监听（开关全关 / 采集未起）→ 不给日志证据。

    关着的端口 MUST NOT 因为一次设备任务被悄悄打开：`ensure_log_evidence` 不启动采集。
    """
    try:
        assert ensure_log_evidence() is None
    finally:
        stop_log_bus()


def test_provider_is_built_when_a_port_is_listening() -> None:
    """有端口真正在监听时给出提供者（用临时空闲端口，不碰现场端口）。"""
    port = _free_port()
    bus = start_log_bus(
        LogBusConfig(tcp_host="127.0.0.1", sources=[LogSourceSpec(port=port, sku="H6810")])
    )
    try:
        deadline = time.time() + 5.0
        while time.time() < deadline and bus.bound_port != port:
            time.sleep(0.05)
        assert bus.bound_port == port

        with override_settings(DEVICE_LOG_ENABLED=True, DEVICE_LOG_SERIAL_PORT=""):
            provider = ensure_log_evidence()
        assert provider is not None
        assert provider.open_window("dev-1", "step-1").startswith("w")
    finally:
        stop_log_bus()


@override_settings(DEVICE_LOG_WINDOW_SECONDS=7)
def test_provider_defaults_wait_to_platform_threshold() -> None:
    """引擎不传等待时长时，按平台取证阈值等（保证慢日志也进窗口）。"""
    fake = _FakeBus()
    provider = DeviceLogEvidence(fake)  # type: ignore[arg-type]
    provider.read_window("dev-1", window_id="w1", action_times=["2026-09-28 17:01:12.645"])
    assert fake.kwargs["wait_seconds"] == 7.0
    assert fake.kwargs["window_id"] == "w1"
    assert fake.kwargs["action_times"] == ["2026-09-28 17:01:12.645"]


@override_settings(
    DEVICE_LOG_TCP_PORT=7005,
    DEVICE_LOG_SOURCES="",
    DEVICE_LOG_SERIAL_PORT="COM3",
    DEVICE_LOG_SERIAL_BAUD=9600,
    DEVICE_LOG_WINDOW_SECONDS=5.0,
    DEVICE_LOG_BASELINE_SECONDS=30.0,
    DEVICE_LOG_SOURCE_SKU="H6810",
    DEVICE_LOG_SOURCE_BAUD=921600,
)
def test_build_config_maps_settings() -> None:
    """settings → 采集配置逐项映射；来源登记带 SKU 与波特率，通道名用被测设备 SKU。"""
    config = build_config()
    assert (config.tcp_port, config.serial_port, config.serial_baud) == (7005, "COM3", 9600)
    assert (config.window_seconds, config.baseline_seconds) == (5.0, 30.0)
    assert config.channel == "H6810"
    assert config.keyword_file.endswith("device_log_keywords.json")
    assert [(spec.port, spec.channel, spec.baud) for spec in config.sources] == [
        (7005, "H6810", 921600)
    ]


@override_settings(
    DEVICE_LOG_TCP_PORT=7005,
    DEVICE_LOG_SOURCE_SKU="H6810",
    DEVICE_LOG_SOURCE_BAUD=921600,
    DEVICE_LOG_SOURCES='{"7005": {"sku": "H6810", "baud": 921600}}',
)
def test_sources_json_overrides_single_port_fallback() -> None:
    """显式 `DEVICE_LOG_SOURCES` 优先于「单端口 + SKU」退化，且能带波特率。"""
    from apps.ai_assistant.log_evidence import source_specs

    assert [(spec.port, spec.channel, spec.baud) for spec in source_specs()] == [
        (7005, "H6810", 921600)
    ]


@override_settings(
    DEVICE_LOG_TCP_PORT=7005,
    DEVICE_LOG_SOURCE_SKU="H6810",
    DEVICE_LOG_SOURCE_BAUD=921600,
    DEVICE_LOG_SOURCES='{"7005": "H6810", "9100": "H6199"}',
)
def test_sources_json_accepts_legacy_shorthand() -> None:
    """旧简写 `{"端口": "通道"}` 仍可用：波特率回退平台默认值。"""
    from apps.ai_assistant.log_evidence import source_specs

    assert [(spec.port, spec.channel, spec.baud) for spec in source_specs()] == [
        (7005, "H6810", 921600),
        (9100, "H6199", 921600),
    ]


@override_settings(
    DEVICE_LOG_TCP_PORT=7005,
    DEVICE_LOG_SOURCE_SKU="H6810",
    DEVICE_LOG_SOURCE_BAUD=921600,
    DEVICE_LOG_SOURCES="not-json",
)
def test_broken_sources_json_falls_back_without_crashing() -> None:
    """非法 JSON 只记录错误并退化为单端口来源（不因配置写错而停采）。"""
    from apps.ai_assistant.log_evidence import source_specs

    assert [(spec.port, spec.channel) for spec in source_specs()] == [(7005, "H6810")]


@override_settings(DEVICE_LOG_SOURCE_SKU="")
def test_channel_falls_back_to_shared_when_sku_missing() -> None:
    """未配 SKU 时退回共享通道（不报错）。"""
    assert build_config().channel == "*"


def _tools_stamping() -> dict[str, bool]:
    """读 tools.py 源码：各工具函数体内是否出现打点调用。"""
    tree = ast.parse(TOOLS_SOURCE.read_text(encoding="utf-8"))
    result: dict[str, bool] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            dumped = ast.dump(node)
            result[node.name] = "_action_stamp" in dumped and "_with_action_time" in dumped
    return result


def test_side_effect_tools_stamp_action_time() -> None:
    """产生副作用的动作工具都打点并回传 action_time。"""
    stamping = _tools_stamping()
    missing = sorted(name for name in SIDE_EFFECT_TOOLS if not stamping.get(name))
    assert missing == [], f"这些动作工具没打点 action_time: {missing}"


def test_read_only_tools_do_not_stamp() -> None:
    """只读工具不打点 action_time（不参与基准选取）。"""
    stamping = _tools_stamping()
    stamped = sorted(name for name in READ_ONLY_TOOLS if stamping.get(name))
    assert stamped == [], f"这些只读工具不该打点: {stamped}"


@pytest.mark.parametrize("tool", ["xpath_action"])
def test_xpath_read_actions_have_no_stamp_branch(tool: str) -> None:
    """xpath_action 的 exists/get_text 分支不打点（只有 click/long_click 打）。"""
    source = TOOLS_SOURCE.read_text(encoding="utf-8")
    exists_branch = source.split('if action == "exists":', 1)[1].split(
        'if action == "get_text":', 1
    )[0]
    text_branch = source.split('if action == "get_text":', 1)[1].split('if action == "click":', 1)[
        0
    ]
    assert "_action_stamp" not in exists_branch
    assert "_action_stamp" not in text_branch
