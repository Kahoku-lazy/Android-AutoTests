"""用例结束后关闭最近任务里的非桌面应用。不连真机。"""

from __future__ import annotations

import asyncio

from engines.agents.workflow.platform_run import bind_cancel, clear_cancel, run_platform_sop
from engines.device.android.recent_apps import (
    FALLBACK_LAUNCHERS,
    close_recent_apps,
    packages_to_stop,
    parse_home_package,
    parse_recent_packages,
)

YAML_TEXT = """
- title: 甲
  steps:
    - action: 点一下
      assert: 页面已打开
- title: 乙
  steps:
    - action: 再点一下
      assert: 页面已切换
""".strip()

RECENTS = """
  intent={cmp=com.govee.home/.Main}
  realActivity=com.govee.home/.Main
  realActivity=com.android.systemui/.recents.RecentsActivity
  realActivity=com.sec.android.app.launcher/.Launcher
  cmp=com.other.app/.Main
"""
HOME = """
priority=0 preferredOrder=0 match=0x108000 specificIndex=-1 isDefault=true
com.sec.android.app.launcher/.Launcher
"""


def test_recent_packages_keep_apps_and_drop_home():
    packages = parse_recent_packages(RECENTS)
    assert packages == [
        "com.govee.home",
        "com.android.systemui",
        "com.sec.android.app.launcher",
        "com.other.app",
    ]
    assert parse_home_package(HOME) == "com.sec.android.app.launcher"
    assert packages_to_stop(packages, parse_home_package(HOME)) == [
        "com.govee.home",
        "com.other.app",
    ]


def test_unknown_home_skips_fallback_launchers():
    launcher = next(iter(FALLBACK_LAUNCHERS))
    packages = [launcher, "com.demo.app", "com.android.systemui"]
    assert packages_to_stop(packages, "") == ["com.demo.app"]
    assert parse_home_package("No activity found") == ""


class _Conn:
    def __init__(self) -> None:
        self.closed = False

    def disconnect(self) -> None:
        self.closed = True


class _Info:
    def __init__(self, recent: str, home: str, *, home_error: bool = False) -> None:
        self.adb = self
        self.recent = recent
        self.home = home
        self.home_error = home_error
        self.shells: list[tuple[str, ...]] = []

    def shell(self, args: list[str]) -> str:
        self.shells.append(tuple(args))
        if args[:2] == ["dumpsys", "activity"]:
            return self.recent
        if self.home_error:
            raise RuntimeError("没有桌面")
        return self.home


class _Control:
    def __init__(self, *, fail_stop: bool = False) -> None:
        self.calls: list[tuple] = []
        self.fail_stop = fail_stop

    def app_stop(self, package: str) -> None:
        if self.fail_stop:
            raise RuntimeError("停不掉")
        self.calls.append(("app_stop", package))

    def press_key(self, key: str = "back") -> None:
        self.calls.append(("press_key", key))


def test_close_stops_apps_then_home(monkeypatch):
    logs: list[str] = []
    conn = _Conn()
    info = _Info(RECENTS, HOME)
    control = _Control()
    monkeypatch.setattr(
        "engines.device.android.recent_apps.write_line",
        lambda model, action: logs.append(action),
    )

    def opener(serial: str):
        assert serial == "R5CT62RH88F"
        return conn, info, control

    close_recent_apps("R5CT62RH88F", opener=opener)
    assert control.calls == [
        ("app_stop", "com.govee.home"),
        ("app_stop", "com.other.app"),
        ("press_key", "home"),
    ]
    assert len(info.shells) == 2
    assert conn.closed is True
    assert logs == ["收尾关闭应用：com.govee.home、com.other.app"]


def test_close_failure_is_logged(monkeypatch):
    logs: list[str] = []
    conn = _Conn()
    monkeypatch.setattr(
        "engines.device.android.recent_apps.write_line",
        lambda model, action: logs.append(action),
    )

    def opener(serial: str):
        return conn, _Info(RECENTS, HOME), _Control(fail_stop=True)

    close_recent_apps("R5CT62RH88F", opener=opener)
    assert conn.closed is True
    assert any("收尾关闭应用失败" in line and "停不掉" in line for line in logs)


def _run(tmp_path, runner, *, serial="R5CT62RH88F", closer=None, task_id=0):
    path = tmp_path / "cases.yaml"
    path.write_text(YAML_TEXT, encoding="utf-8")
    return run_platform_sop(
        str(path),
        "本次要操作的设备 serial 是：R5CT62RH88F。每一步的设备动作都必须带上它。",
        executor_model=None,
        verifier_model=None,
        task_id=task_id,
        device_serial=serial,
        close_recent_apps=closer,
        run_case=runner,
    )


def test_each_finished_case_closes(tmp_path):
    closed: list[str] = []
    result = _run(
        tmp_path,
        lambda title, steps, opening: "completed",
        closer=closed.append,
    )
    assert closed == ["R5CT62RH88F", "R5CT62RH88F"]
    assert result["status"] == "success"
    assert result["completed"] == ["甲", "乙"]


def test_failed_case_closes_once_and_stops(tmp_path):
    seen: list[str] = []
    closed: list[str] = []

    def runner(title, steps, opening):
        seen.append(title)
        return "fail"

    result = _run(tmp_path, runner, closer=closed.append)
    assert seen == ["甲"]
    assert closed == ["R5CT62RH88F"]
    assert result["status"] == "fail"
    assert result["completed"] == []


def test_cancel_during_case_still_closes(tmp_path):
    closed: list[str] = []

    def runner(title, steps, opening):
        raise asyncio.CancelledError()

    result = _run(tmp_path, runner, closer=closed.append)
    assert closed == ["R5CT62RH88F"]
    assert result["status"] == "cancelled"
    assert result["completed"] == []


def test_cancel_before_next_case_does_not_close_again(tmp_path):
    seen: list[str] = []
    closed: list[str] = []
    event = bind_cancel(71)
    try:

        def runner(title, steps, opening):
            seen.append(title)
            event.set()
            return "completed"

        result = _run(tmp_path, runner, closer=closed.append, task_id=71)
    finally:
        clear_cancel(71)
    assert seen == ["甲"]
    assert closed == ["R5CT62RH88F"]
    assert result["status"] == "cancelled"
    assert result["completed"] == ["甲"]


def test_empty_serial_skips_close(tmp_path, monkeypatch):
    logs: list[str] = []
    closed: list[str] = []
    monkeypatch.setattr(
        "engines.agents.workflow.platform_run.write_line",
        lambda model, action: logs.append(action),
    )
    result = _run(
        tmp_path,
        lambda title, steps, opening: "completed",
        serial="",
        closer=closed.append,
    )
    assert closed == []
    assert logs == ["收尾跳过：设备序列号为空", "收尾跳过：设备序列号为空"]
    assert result["status"] == "success"


def test_closer_error_keeps_success(tmp_path, monkeypatch):
    logs: list[str] = []
    monkeypatch.setattr(
        "engines.agents.workflow.platform_run.write_line",
        lambda model, action: logs.append(action),
    )

    def closer(serial: str) -> None:
        raise RuntimeError("adb 断了")

    result = _run(tmp_path, lambda title, steps, opening: "completed", closer=closer)
    assert result["status"] == "success"
    assert result["completed"] == ["甲", "乙"]
    assert logs == ["收尾关闭应用失败：adb 断了", "收尾关闭应用失败：adb 断了"]
