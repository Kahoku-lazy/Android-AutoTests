"""
单文件调试指令：python -m pytest tests/engines/agents/test_tool_device.py -vv -s --tb=short

本文件是 tool_device 的工具契约测试，全部纯单测（替身接管 open_device，不连设备，约 1 秒）。

1. test_every_tool_* —— 工具表完整性与顺序：9 个工具都要有用例，`_TOOL_ORDER` 固定。
2. test_every_action_* —— 每个动作都必须回传 action_time，并在结束时断开设备。
3. test_click_ratio_* / test_tap_screen_* —— 点击类回传实际点到的像素坐标（含屏幕夹取），且不再读前台应用。
4. test_time_only_* / test_swipe_screen_* —— 滑动 / 拖动 / 输入 / 按键的返回体恰好只有 action_time。
5. test_app_control_* —— 启停 App 回传时间点、包名与启停前后的前台应用（含等待切台与超时收尾）。
6. test_screenshot_page_* —— 截图只回 image（base64 + media_type）：不落盘、格式回落 JPEG、失败转 error。
7. test_xpath_action_* —— xpath 只查询：回文本与中心坐标，无 action_time，0 命中给 count=0。
8. test_*_returns_error —— 失败路径：连接失败 / 动作抛错 / 非法参数（非法参数不碰设备）。
9. test_read_only_flags —— 只读标记：只有截图与 xpath 查询是只读。

全部用例都不需要真机；真机冒烟见 test_tool_device_e2e.py。
"""

from __future__ import annotations

import base64
import json
import re

import pytest

from engines.agents.tools import tool_device

pytestmark = pytest.mark.unit

# 1x1 透明 PNG：截图的原始字节替身
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
# 与 utils.logs.logging_now_stamp 的格式一致：YYYY-MM-DD HH:MM:SS,mmm
_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}$")
_SCREEN = (1080, 2340)

# 每个动作工具的调用参数（test_every_action_returns_action_time 与完整性检查共用）
_ACTION_CALLS: dict[str, dict] = {
    "click_ratio": {"nx": 0.5, "ny": 0.5},
    "tap_screen": {"mode": "click", "x": 10, "y": 20},
    "swipe_screen": {"direction": "down", "distance": 400},
    "drag_ratio": {"nx1": 0.1, "ny1": 0.1, "nx2": 0.2, "ny2": 0.2},
    "input_text": {"text": "hello"},
    "press_key": {},
    "app_control": {"action": "start_app", "package": "com.target"},
}
# 只回时间的工具：返回体必须**恰好**只有 action_time
_TIME_ONLY = ("swipe_screen", "drag_ratio", "input_text", "press_key")


class _Conn:
    """连接对象替身。"""

    def __init__(self) -> None:
        self.closed = False

    def disconnect(self) -> None:
        self.closed = True


class _Info:
    """设备信息替身：按脚本依次给出前台应用，脚本用尽后重复最后一条。"""

    def __init__(self, apps: list[tuple[str, str]] | None = None) -> None:
        self._apps = apps or [("com.before", "com.before.Main")]
        self.reads = 0

    def current_app(self) -> dict:
        index = min(self.reads, len(self._apps) - 1)
        self.reads += 1
        package, activity = self._apps[index]
        return {"package": package, "activity": activity}


class _Control:
    """设备控制替身：记录每次调用，像素换算与真机一致（含夹取）。"""

    screenshot_media_type = "image/png"

    def __init__(self, width: int = _SCREEN[0], height: int = _SCREEN[1]) -> None:
        self.width = width
        self.height = height
        self.calls: list[tuple] = []
        self.found: list[dict] = []
        self.fail_on: str = ""

    def _pixel(self, nx: float, ny: float) -> tuple[int, int]:
        x = min(self.width - 1, max(0, int(float(nx) * self.width)))
        y = min(self.height - 1, max(0, int(float(ny) * self.height)))
        return x, y

    def _record(self, name: str, *args) -> None:
        if self.fail_on == name:
            raise RuntimeError(f"{name} 执行失败")
        self.calls.append((name, *args))

    # ── 点击 / 长按 ──
    def click_coord(self, x: int, y: int) -> None:
        self._record("click_coord", x, y)

    def click_img(self, nx: float, ny: float) -> tuple[int, int]:
        x, y = self._pixel(nx, ny)
        self._record("click_img", x, y)
        return x, y

    def long_click_coord(self, x: int, y: int, duration: float = 0.8) -> None:
        self._record("long_click_coord", x, y)

    def long_click_img(self, nx: float, ny: float, duration: float = 0.8) -> tuple[int, int]:
        x, y = self._pixel(nx, ny)
        self._record("long_click_img", x, y)
        return x, y

    # ── 滑动 / 拖动 / 输入 / 按键 ──
    def swipe(self, direction: str = "up", distance: int = 500) -> None:
        self._record("swipe", direction, distance)

    def swipe_coord(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> None:
        self._record("swipe_coord", x1, y1, x2, y2)

    def drag(self, nx1: float, ny1: float, nx2: float, ny2: float) -> None:
        self._record("drag", nx1, ny1, nx2, ny2)

    def input_text(self, text: str, clear_first: bool = True) -> None:
        self._record("input_text", text, clear_first)

    def press_key(self, key: str = "back") -> None:
        self._record("press_key", key)

    # ── 应用 / 截图 / 查询 ──
    def app_start(self, package: str) -> None:
        self._record("app_start", package)

    def app_stop(self, package: str) -> None:
        self._record("app_stop", package)

    def screenshot_bytes(self) -> bytes:
        self._record("screenshot_bytes")
        return PNG_1PX

    def find_xpath(self, xpath: str) -> list[dict]:
        self._record("find_xpath", xpath)
        return self.found


@pytest.fixture(autouse=True)
def _fast_app_poll(monkeypatch: pytest.MonkeyPatch) -> None:
    """启停 App 的等待改短，避免用例等 6 秒。"""
    monkeypatch.setattr(tool_device, "_APP_SETTLE_TIMEOUT", 0.2)
    monkeypatch.setattr(tool_device, "_APP_POLL_INTERVAL", 0.01)


def _install(
    monkeypatch: pytest.MonkeyPatch,
    apps: list[tuple[str, str]] | None = None,
) -> tuple[_Conn, _Info, _Control]:
    """把假设备装进工具模块，返回三件套供断言。"""
    conn, info, control = _Conn(), _Info(apps), _Control()

    def open_device(*_args, **_kwargs):
        return conn, info, control

    monkeypatch.setattr(tool_device, "open_device", open_device)
    return conn, info, control


def _run(name: str, *args, **kwargs) -> dict:
    """调用工具并解析返回的 JSON。"""
    return json.loads(getattr(tool_device, name)("serial-1", *args, **kwargs))


def _assert_stamp(payload: dict) -> None:
    """返回体里的 action_time 必须是本地时间戳格式。"""
    assert "action_time" in payload, payload
    assert _STAMP.match(payload["action_time"]), payload["action_time"]


def _show(label: str, expected: str, actual) -> None:
    """打印预期与实际，让 PASS 也能看到比对结果（-vv 只给 PASSED，要配 -s）。"""
    if isinstance(actual, dict):
        actual = json.dumps(actual, ensure_ascii=False)
    print(f"\n[预期] {label} → {expected}")
    print(f"[实际] {actual}")


# ══════════════════════════════════════════════════════════════════
# 完整性：所有工具都要有用例，不能漏
# ══════════════════════════════════════════════════════════════════


def test_every_tool_is_covered() -> None:
    """本文件必须覆盖工具表里的每一个工具。"""
    covered = set(_ACTION_CALLS) | {"screenshot_page", "xpath_action"}
    assert covered == {spec.name for spec in tool_device.device_tool_specs()}


def test_every_tool_has_handler() -> None:
    """工具表与实现表一一对应，顺序固定。"""
    tools = tool_device.build_device_tools()
    assert list(tools) == list(tool_device._TOOL_ORDER)
    assert all(callable(func) for func in tools.values())


# ══════════════════════════════════════════════════════════════════
# 每个动作都必须回传动作时间
# ══════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("name", list(_ACTION_CALLS))
def test_every_action_returns_action_time(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    """7 个动作工具都要回传 action_time（滑动/输入/按键只回它）。"""
    _install(monkeypatch)
    payload = _run(name, **_ACTION_CALLS[name])
    assert "error" not in payload, payload
    _assert_stamp(payload)


@pytest.mark.parametrize("name", list(_ACTION_CALLS))
def test_every_action_closes_the_connection(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    """动作结束后必须断开设备。"""
    conn, _info, _control = _install(monkeypatch)
    _run(name, **_ACTION_CALLS[name])
    assert conn.closed is True


# ══════════════════════════════════════════════════════════════════
# 点击类：回传实际点击的像素坐标
# ══════════════════════════════════════════════════════════════════


def test_click_ratio_returns_clicked_pixel(monkeypatch: pytest.MonkeyPatch) -> None:
    """归一化 0.5/0.5 在 1080×2340 上即 (540, 1170)，返回体恰好是坐标 + 时间。"""
    _conn, _info, control = _install(monkeypatch)

    payload = _run("click_ratio", nx=0.5, ny=0.5)
    _show(
        "click_ratio(nx=0.5, ny=0.5)｜1080×2340",
        "{x: 540, y: 1170, action_time: YYYY-MM-DD HH:MM:SS,mmm}，恰好这三个键",
        payload,
    )

    assert (payload["x"], payload["y"]) == (540, 1170)
    assert set(payload) == {"x", "y", "action_time"}
    assert ("click_img", 540, 1170) in control.calls


def test_click_ratio_clamps_to_screen(monkeypatch: pytest.MonkeyPatch) -> None:
    """越界归一化坐标按屏幕边界夹取，回传的必须是真正点到的位置。"""
    _install(monkeypatch)

    payload = _run("click_ratio", nx=1.5, ny=-0.2)

    assert (payload["x"], payload["y"]) == (1079, 0)


def test_click_ratio_does_not_read_foreground(monkeypatch: pytest.MonkeyPatch) -> None:
    """点击不再回传前台应用，因此不应去读 dumpsys（少一次 adb）。"""
    _conn, info, _control = _install(monkeypatch)

    _run("click_ratio", nx=0.5, ny=0.5)

    assert info.reads == 0


def test_tap_screen_click_returns_pixel(monkeypatch: pytest.MonkeyPatch) -> None:
    """像素点击回传的坐标与入参一致。"""
    _conn, _info, control = _install(monkeypatch)

    payload = _run("tap_screen", mode="click", x=12, y=34)
    _show(
        "tap_screen(mode=click, x=12, y=34)",
        "{x: 12, y: 34, action_time: YYYY-MM-DD HH:MM:SS,mmm}",
        payload,
    )

    assert (payload["x"], payload["y"]) == (12, 34)
    assert set(payload) == {"x", "y", "action_time"}
    assert ("click_coord", 12, 34) in control.calls


def test_tap_screen_long_click_returns_pixel(monkeypatch: pytest.MonkeyPatch) -> None:
    """长按同样回传坐标，且走的是长按实现而不是点击。"""
    _conn, _info, control = _install(monkeypatch)

    payload = _run("tap_screen", mode="long_click", x=12, y=34)

    assert (payload["x"], payload["y"]) == (12, 34)
    assert ("long_click_coord", 12, 34) in control.calls
    assert ("click_coord", 12, 34) not in control.calls


def test_tap_screen_default_mode_is_click(monkeypatch: pytest.MonkeyPatch) -> None:
    """不传 mode 时按点击执行。"""
    _conn, _info, control = _install(monkeypatch)

    _run("tap_screen", x=1, y=2)

    assert control.calls[0] == ("click_coord", 1, 2)


# ══════════════════════════════════════════════════════════════════
# 非点击动作：只回传动作时间
# ══════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("name", list(_TIME_ONLY))
def test_time_only_actions_return_only_action_time(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """滑动/拖动/输入/按键的返回体必须**恰好**只有 action_time。"""
    _conn, _info, control = _install(monkeypatch)

    payload = _run(name, **_ACTION_CALLS[name])
    _show(
        f"{name}({_ACTION_CALLS[name]})",
        "{action_time: YYYY-MM-DD HH:MM:SS,mmm}，只有这一个键",
        payload,
    )

    assert set(payload) == {"action_time"}
    _assert_stamp(payload)
    assert control.calls, "动作没有被下发"


@pytest.mark.parametrize("name", list(_TIME_ONLY))
def test_time_only_actions_do_not_read_foreground(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """这些动作不看前台变化，不应额外读 dumpsys。"""
    _conn, info, _control = _install(monkeypatch)

    _run(name, **_ACTION_CALLS[name])

    assert info.reads == 0


def test_swipe_screen_passes_direction_and_distance(monkeypatch: pytest.MonkeyPatch) -> None:
    """方向与距离要原样下发（返回体不重复它们）。"""
    _conn, _info, control = _install(monkeypatch)

    _run("swipe_screen", direction="left", distance=321)

    assert control.calls[0] == ("swipe", "left", 321)


# ══════════════════════════════════════════════════════════════════
# 启停 App：时间点 + 包名 + 前后台
# ══════════════════════════════════════════════════════════════════


def test_app_control_start_returns_before_and_after(monkeypatch: pytest.MonkeyPatch) -> None:
    """启动：回传时间点、包名、动作，以及启动前后的前台应用。"""
    _conn, _info, control = _install(
        monkeypatch,
        apps=[("com.launcher", "com.launcher.Main"), ("com.target", "com.target.Main")],
    )

    payload = _run("app_control", action="start_app", package="com.target")
    _show(
        "app_control(start_app, com.target)",
        "after_app.package = com.target；带 package/action/action_time/before_app/after_app",
        payload,
    )

    _assert_stamp(payload)
    assert payload["package"] == "com.target"
    assert payload["action"] == "start_app"
    assert payload["before_app"] == {"package": "com.launcher", "activity": "com.launcher.Main"}
    assert payload["after_app"] == {"package": "com.target", "activity": "com.target.Main"}
    assert set(payload) == {"package", "action", "action_time", "before_app", "after_app"}
    assert ("app_start", "com.target") in control.calls


def test_app_control_stop_returns_before_and_after(monkeypatch: pytest.MonkeyPatch) -> None:
    """关闭：等前台离开目标包，再回传。"""
    _conn, _info, _control = _install(
        monkeypatch,
        apps=[("com.target", "com.target.Main"), ("com.launcher", "com.launcher.Main")],
    )

    payload = _run("app_control", action="stop_app", package="com.target")
    _show(
        "app_control(stop_app, com.target)",
        "before_app.package = com.target，after_app.package = com.launcher",
        payload,
    )

    assert payload["action"] == "stop_app"
    assert payload["before_app"]["package"] == "com.target"
    assert payload["after_app"]["package"] == "com.launcher"


def test_app_control_waits_for_package_to_appear(monkeypatch: pytest.MonkeyPatch) -> None:
    """启动是异步的：先读到几次旧前台，必须继续等到目标包出现。"""
    _conn, info, _control = _install(
        monkeypatch,
        apps=[
            ("com.launcher", "com.launcher.Main"),  # before
            ("", ""),  # 启动中，读不到焦点
            ("", ""),
            ("com.target", "com.target.Main"),
        ],
    )

    payload = _run("app_control", action="start_app", package="com.target")

    assert payload["after_app"]["package"] == "com.target"
    assert info.reads >= 4


def test_app_control_timeout_returns_last_seen_app(monkeypatch: pytest.MonkeyPatch) -> None:
    """目标一直没出现时按超时收尾，返回最后读到的前台，而不是空等或抛错。"""
    monkeypatch.setattr(tool_device, "_APP_SETTLE_TIMEOUT", 0.05)
    _conn, _info, _control = _install(
        monkeypatch,
        apps=[("com.launcher", "com.launcher.Main")],
    )

    payload = _run("app_control", action="start_app", package="com.target")

    assert payload["after_app"]["package"] == "com.launcher"
    _assert_stamp(payload)


# ══════════════════════════════════════════════════════════════════
# 非动作工具：截图与 xpath 查询
# ══════════════════════════════════════════════════════════════════


def test_screenshot_page_returns_image_without_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """截图回传无损 base64 与格式；不落盘，路径键恒为空串。"""
    _install(monkeypatch)

    payload = tool_device.build_device_tools()["screenshot_page"]("serial-1")
    _show(
        "screenshot_page",
        '{"image": {base64: 原始 PNG 的 base64, media_type: image/png}}，只有这一个键',
        {
            "image.base64(长度)": len(payload["image"]["base64"]),
            "image.media_type": payload["image"]["media_type"],
            "顶层键": sorted(payload),
        },
    )

    assert payload["image"] == {
        "base64": base64.b64encode(PNG_1PX).decode("ascii"),
        "media_type": "image/png",
    }
    assert set(payload) == {"image"}


def test_screenshot_page_does_not_touch_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    """截图不落盘：整个过程不应有任何文件写入。"""

    def forbidden(*_args, **_kwargs):
        raise AssertionError("截图不应该写文件")

    monkeypatch.setattr("pathlib.Path.write_bytes", forbidden)
    monkeypatch.setattr("pathlib.Path.mkdir", forbidden)
    _install(monkeypatch)

    payload = tool_device.build_device_tools()["screenshot_page"]("serial-1")

    assert "error" not in payload, payload


def test_screenshot_page_only_accepts_serial() -> None:
    """参数表只有 serial：keep_local 已删除，传了就是 TypeError（提示词侧已同步）。"""
    screenshot = tool_device.build_device_tools()["screenshot_page"]

    with pytest.raises(TypeError):
        screenshot("serial-1", keep_local=True)


def test_screenshot_page_connection_failure_returns_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """连不上设备时返回截屏失败，不抛异常给模型。"""

    def open_device(*_args, **_kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(tool_device, "open_device", open_device)

    payload = tool_device.build_device_tools()["screenshot_page"]("serial-1")

    assert "截屏失败" in payload["error"]
    assert "offline" in payload["error"]


def test_screenshot_page_capture_failure_returns_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """截屏动作自身失败（如 screencap 不是 PNG）同样转成可读结论。"""
    _conn, _info, control = _install(monkeypatch)
    control.fail_on = "screenshot_bytes"

    payload = tool_device.build_device_tools()["screenshot_page"]("serial-1")

    assert "截屏失败" in payload["error"]
    assert "screenshot_bytes 执行失败" in payload["error"]


def test_screenshot_page_media_type_falls_back_to_jpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    """控制实现没声明 screenshot_media_type 时，格式回落到 JPEG。"""
    monkeypatch.delattr(_Control, "screenshot_media_type")
    _install(monkeypatch)

    payload = tool_device.build_device_tools()["screenshot_page"]("serial-1")

    assert payload["image"]["media_type"] == tool_device.Screenshot.MODEL_MEDIA_TYPE


def test_xpath_action_returns_coordinates_without_action_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """xpath 只查询：回传文本与中心坐标，没有动作时间。"""
    _conn, _info, control = _install(monkeypatch)
    control.found = [{"text": "H6110", "x": 120, "y": 340}]

    payload = _run("xpath_action", xpath="//node")
    _show(
        "xpath_action(//node)｜命中 1 条",
        "{count: 1, text: H6110, x: 120, y: 340}，无 action_time",
        payload,
    )

    assert payload == {"count": 1, "text": "H6110", "x": 120, "y": 340}
    assert "action_time" not in payload


def test_xpath_action_reports_zero_hits(monkeypatch: pytest.MonkeyPatch) -> None:
    """未命中时给 count=0，而不是报错。"""
    _install(monkeypatch)

    payload = _run("xpath_action", xpath="//missing")

    assert payload == {"count": 0, "items": []}


# ══════════════════════════════════════════════════════════════════
# 失败路径：一律转成可读 error，不抛异常给模型
# ══════════════════════════════════════════════════════════════════


def test_connection_failure_returns_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """连不上设备时返回连接失败结论。"""

    def open_device(*_args, **_kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(tool_device, "open_device", open_device)

    payload = _run("press_key")

    assert "连接设备失败" in payload["error"]
    assert "offline" in payload["error"]


def test_action_failure_returns_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """动作本身抛错时返回动作失败结论，不泄漏栈。"""
    _conn, _info, control = _install(monkeypatch)
    control.fail_on = "press_key"

    payload = _run("press_key")

    assert "动作执行失败" in payload["error"]


@pytest.mark.parametrize(
    "name,kwargs,expected",
    [
        ("tap_screen", {"mode": "longclick", "x": 1, "y": 2}, "不支持的点击模式"),
        ("tap_screen", {"mode": "", "x": 1, "y": 2}, "不支持的点击模式"),
        ("swipe_screen", {"direction": "Left"}, "不支持的滑动方向"),
        ("app_control", {"action": "restart", "package": "p"}, "不支持的 App 动作"),
        ("app_control", {"action": "start_app"}, "需要 package"),
    ],
)
def test_invalid_arguments_return_readable_error(
    monkeypatch: pytest.MonkeyPatch, name: str, kwargs: dict, expected: str
) -> None:
    """非法参数直接给可读错误，不静默退回默认动作。"""
    _conn, _info, control = _install(monkeypatch)

    payload = _run(name, **kwargs)

    assert expected in payload["error"]
    assert control.calls == [], "参数非法时不应碰设备"


# ══════════════════════════════════════════════════════════════════
# 只读标记：决定权限放行与并发安全
# ══════════════════════════════════════════════════════════════════


def test_read_only_flags() -> None:
    """截图与 xpath 查询只读；其余动作都会改设备状态。"""
    specs = {spec.name: spec for spec in tool_device.device_tool_specs()}
    assert {name for name, spec in specs.items() if spec.read_only} == {
        "screenshot_page",
        "xpath_action",
    }
