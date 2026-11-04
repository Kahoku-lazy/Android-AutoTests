"""前台应用读取：优先轻量 dumpsys window displays，取不到再退回 activity 栈。"""

from __future__ import annotations

import pytest

from engines.device.android.android_device import AdbInfo, _parse_current_app

pytestmark = [pytest.mark.unit]


class _FakeAdb:
    """按命令回放的 adb 替身。"""

    def __init__(self, responses: dict[str, str]) -> None:
        self.responses = dict(responses)
        self.calls: list[list[str]] = []

    def shell(self, args, timeout: float = 30.0):
        """回放预置输出。

        Args:
            args: adb shell 参数。
            timeout: 未使用。

        Returns:
            预置文本。
        """
        del timeout
        self.calls.append([str(item) for item in args])
        return self.responses.get(" ".join(str(item) for item in args), "")


def test_parse_focus_window():
    """window 段：mCurrentFocus 里带包名与 Activity。"""
    text = (
        "  mCurrentFocus=Window{1fb9097 u0 com.govee.home/"
        "com.govee.home.HomeActivity}\n"
    )

    assert _parse_current_app(text) == {
        "package": "com.govee.home",
        "activity": "com.govee.home.HomeActivity",
    }


def test_parse_resumed_activity():
    """activity 段：mResumedActivity 也能解析。"""
    text = (
        "    mResumedActivity: ActivityRecord{87085533 u0 "
        "com.sec.android.app.launcher/.activities.LauncherActivity t98665}\n"
    )

    assert _parse_current_app(text) == {
        "package": "com.sec.android.app.launcher",
        "activity": ".activities.LauncherActivity",
    }


def test_parse_returns_empty_when_nothing_matches():
    """两段都没有时返回空包名，调用方据此回退。"""
    assert _parse_current_app("mCurrentFocus=null\n") == {"package": "", "activity": ""}


def test_current_app_prefers_light_displays_dump():
    """先读 dumpsys window displays；不再读整份 dumpsys window（本机要 5.5s）。"""
    info = AdbInfo("R5CT62RH88F")
    info.adb = _FakeAdb(
        {
            "dumpsys window displays": (
                "  mCurrentFocus=Window{1 u0 com.govee.home/com.govee.home.HomeActivity}\n"
            )
        }
    )

    app = info.current_app()

    assert app["package"] == "com.govee.home"
    assert [call for call in info.adb.calls] == [["dumpsys", "window", "displays"]]


def test_current_app_falls_back_to_activity_stack():
    """displays 段没有焦点窗口时，退回 activity 栈（同样约 0.2s）。"""
    info = AdbInfo("R5CT62RH88F")
    info.adb = _FakeAdb(
        {
            "dumpsys window displays": "  mCurrentFocus=null\n",
            "dumpsys activity activities": (
                "    mResumedActivity: ActivityRecord{1 u0 com.govee.home/.HomeActivity}\n"
            ),
        }
    )

    app = info.current_app()

    assert app["package"] == "com.govee.home"
    assert info.adb.calls == [
        ["dumpsys", "window", "displays"],
        ["dumpsys", "activity", "activities"],
    ]
