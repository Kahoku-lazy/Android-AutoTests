"""设备启停应用：优先按 LAUNCHER 组件启动，包名写错时给出可定位的错误。"""

from __future__ import annotations

import pytest

from engines.device.android.android_device import AdbControl

pytestmark = [pytest.mark.unit]


class _FakeAdb:
    """按命令最长前缀回放的 adb 替身。"""

    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = dict(responses)
        self.calls: list[list[str]] = []

    def shell(self, args, timeout: float = 30.0):
        """回放预置结果；没准备就抛 RuntimeError。

        Args:
            args: adb shell 参数。
            timeout: 未使用，保持与真实通道一致。

        Returns:
            预置的输出文本。
        """
        del timeout
        self.calls.append([str(item) for item in args])
        key = " ".join(str(item) for item in args)
        for prefix in sorted(self.responses, key=len, reverse=True):
            if key.startswith(prefix):
                value = self.responses[prefix]
                if isinstance(value, Exception):
                    raise value
                return value
        raise RuntimeError(f"没有为命令准备结果: {key}")


def _control(responses: dict[str, object]) -> tuple[AdbControl, _FakeAdb]:
    """造一个不连真机的 AdbControl，并换上替身通道。"""
    control = AdbControl("R5CT62RH88F")
    fake = _FakeAdb(responses)
    control.adb = fake
    return control, fake


def test_start_uses_resolved_launcher_component():
    """解析到 LAUNCHER 组件时用 am start 启动，不再走 monkey。"""
    control, fake = _control(
        {
            "cmd package resolve-activity": (
                "priority=0 preferredOrder=0 match=0x108000 specificIndex=-1 isDefault=false\n"
                "com.govee.home/.HomeActivity\n"
            ),
            "am start -W -n": "Status: ok\n",
        }
    )

    control.app_start("com.govee.home")

    commands = [" ".join(call) for call in fake.calls]
    assert any(cmd.startswith("am start -W -n com.govee.home/.HomeActivity") for cmd in commands)
    assert not any(cmd.startswith("monkey") for cmd in commands)


def test_start_falls_back_to_monkey_when_component_missing():
    """解析不到组件时退回 monkey，成功即返回。"""
    control, fake = _control(
        {
            "cmd package resolve-activity": "No activity found\n",
            "monkey -p com.govee.home": "Events injected: 1\n",
        }
    )

    control.app_start("com.govee.home")

    commands = [" ".join(call) for call in fake.calls]
    assert any(cmd.startswith("monkey -p com.govee.home") for cmd in commands)


def test_start_reports_wrong_package_with_installed_hint():
    """包名写错时，错误信息里给出设备上相近的已安装包。"""
    control, _ = _control(
        {
            "cmd package resolve-activity": "No activity found\n",
            "monkey -p govee.home.com": RuntimeError(
                "** No activities found to run, monkey aborted."
            ),
            "pm list packages": "package:com.govee.home\npackage:com.govee.life\n",
        }
    )

    with pytest.raises(RuntimeError) as err:
        control.app_start("govee.home.com")

    message = str(err.value)
    assert "未安装或没有 LAUNCHER 入口" in message
    assert "com.govee.home" in message


def test_stop_refuses_unknown_package():
    """停止未安装的包要报错：am force-stop 对它也会返回成功，不校验会误判。"""
    control, fake = _control(
        {
            "pm list packages govee.home.com": "package:com.govee.home\n",
            "pm list packages": "package:com.govee.home\npackage:com.govee.life\n",
        }
    )

    with pytest.raises(RuntimeError) as err:
        control.app_stop("govee.home.com")

    assert "未安装" in str(err.value)
    assert "com.govee.home" in str(err.value)
    assert not any("force-stop" in " ".join(call) for call in fake.calls)


def test_stop_installed_package_runs_force_stop():
    """已安装的包正常执行 am force-stop。"""
    control, fake = _control(
        {
            "pm list packages com.govee.home": "package:com.govee.home\n",
            "am force-stop com.govee.home": "",
        }
    )

    control.app_stop("com.govee.home")

    assert any("force-stop com.govee.home" in " ".join(call) for call in fake.calls)
