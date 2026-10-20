"""
单文件调试指令：python -m pytest tests/engines/devices/test_android_device.py -vv -s --tb=short

1. TestAndroidConnection 类测试 AndroidConnection 类的连接、断开、配对功能。
2. TestAndroidControl 类测试 AndroidControl 类的启动应用、关闭应用（AndroidControl 继承纯 adb 实现）。
3. TestAdbChannel 类测试 AdbChannel 类的命令拼装、解码与失败上报（替身接管 subprocess，不连设备）。
4. TestAdbInfo 类测试 AdbInfo 类的分辨率 / 前台应用 / 包名 / 已连接设备 / 层级解析（替身接管 subprocess，样本取自真机输出）。
5. TestAdbChannelDevice 类用真机验证 AdbChannel 的命令通道（数据取自 test_data.yaml 的 TestAdbChannel）。
6. TestAdbInfoDevice 类用真机验证 AdbInfo 的各查询方法（数据取自 test_data.yaml 的 TestAdbInfo）。

第一、二、五、六类需要真机，第三、四类是纯单测。
"""

import io
import re
import time

from pathlib import Path

import pytest
import yaml

from engines.device.action import EngineConnectError
from engines.device.android import android_device
from engines.device.android.android_device import (
    AdbChannel,
    AdbInfo,
    AndroidConnection,
    AndroidConnectionConfig,
    AndroidControl,
    _bounds_center,
)

_DATA_KEY = "TestAndroidConnection"
_CONFIG_FIELDS = ("uuid", "address", "address_port", "pair_port", "pair_code")


def _yaml_rows(key: str) -> list[dict]:
    """读取同目录 test_data.yaml 中的一组数据。一组对应一轮测试。"""
    path = Path(__file__).with_name("test_data.yaml")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = loaded.get(key) or []
    if isinstance(rows, dict):
        rows = [rows]
    return list(rows)


def _connection_cases() -> list[dict]:
    return _yaml_rows(_DATA_KEY)


def _control_rounds() -> list[dict]:
    """每台连接数据配每一条控制数据，组成一轮。"""
    rounds = []
    for device in _connection_cases():
        for app in _yaml_rows("TestAndroidControl"):
            rounds.append({**device, **app})
    return rounds


def _config(case: dict) -> AndroidConnectionConfig:
    return AndroidConnectionConfig(
        **{name: case[name] for name in _CONFIG_FIELDS if case.get(name) is not None}
    )


def _assert_device_line(listed: str, expected: str, *, present: bool) -> None:
    """打印 adb devices 原文和是否命中，再按 present 断言该行是否存在。"""
    matched = re.search(
        # 行尾允许 \r：adb 在 Windows 上输出 CRLF，按字节解码时不会自动去掉
        rf"^{re.escape(expected)}[ \t]+device\r?$",
        listed,
        re.MULTILINE,
    )
    hit = "命中" if matched else "未命中"
    print(f"\n期望 {expected}    device：{hit}\nadb devices:\n{listed}")
    if present:
        assert matched, listed
    else:
        assert not matched, listed


@pytest.mark.parametrize(
    "case",
    _connection_cases(),
    ids=lambda case: f"{case['address']}:{case['address_port']}",
)
class TestAndroidConnection:
    def test_android_connection(self, case):
        connection = AndroidConnection(_config(case))
        connection.connect()

        expected = f"{case['address']}:{case['address_port']}"
        _assert_device_line(connection.adb_devices(), expected, present=True)

    def test_android_disconnect(self, case):
        connection = AndroidConnection(_config(case))
        connection.connect()
        connection.disconnect()

        expected = f"{case['address']}:{case['address_port']}"
        _assert_device_line(connection.adb_devices(), expected, present=False)


@pytest.mark.unit
class TestAndroidConnectionFailure:
    """AndroidConnection：adb connect 失败时退出码仍是 0，只能按关键词判定。"""

    def _connection(self) -> AndroidConnection:
        return AndroidConnection(AndroidConnectionConfig(address="192.0.2.1", address_port=5555))

    def test_connect_raises_when_server_reports_failure(self, monkeypatch):
        """返回文本不含成功关键词时抛 EngineConnectError。"""
        connection = self._connection()
        monkeypatch.setattr(
            connection,
            "_run_adb",
            lambda *_args, **_kwargs: "cannot connect to 192.0.2.1:5555: timed out",
        )

        with pytest.raises(EngineConnectError, match="connect 失败"):
            connection.connect()

    def test_connect_passes_when_already_connected(self, monkeypatch):
        """已有连接时关键词命中，不抛异常。"""
        connection = self._connection()
        monkeypatch.setattr(
            connection,
            "_run_adb",
            lambda *_args, **_kwargs: "already connected to 192.0.2.1:5555",
        )

        connection.connect()

    def test_connect_passes_on_chinese_success_message(self, monkeypatch):
        """中文成功提示同样命中关键词。"""
        connection = self._connection()
        monkeypatch.setattr(
            connection, "_run_adb", lambda *_args, **_kwargs: "已连接到 192.0.2.1:5555"
        )

        connection.connect()


def _device_uuid(case: dict) -> str:
    if case.get("uuid"):
        return str(case["uuid"])
    return f"{case['address']}:{case['address_port']}"


def _open_info(case: dict) -> AdbInfo:
    AndroidConnection(_config(case)).connect()
    return AdbInfo(_device_uuid(case))


def _wait_foreground(info: AdbInfo, package: str, *, present: bool, timeout: float = 8) -> dict:
    """轮询前台包名，直到与 package 的关系符合 present，或超时。"""
    deadline = time.monotonic() + timeout
    last: dict = {}
    while True:
        last = info.current_app() or {}
        hit = last.get("package") == package
        if hit == present or time.monotonic() >= deadline:
            state = "前台" if hit else "非前台"
            print(f"\n{package} {state}: {last}")
            return last
        time.sleep(0.5)


@pytest.mark.parametrize(
    "case",
    _control_rounds(),
    ids=lambda case: f"{case['address']}:{case['address_port']}:{case['app_package']}",
)
class TestAndroidControl:
    def test_app_start(self, case):
        package = case["app_package"]
        info = _open_info(case)
        AndroidControl(_device_uuid(case)).app_start(package)
        app = _wait_foreground(info, package, present=True)
        assert app.get("package") == package

    def test_app_stop(self, case):
        package = case["app_package"]
        info = _open_info(case)
        control = AndroidControl(_device_uuid(case))
        control.app_start(package)
        _wait_foreground(info, package, present=True)
        control.app_stop(package)
        app = _wait_foreground(info, package, present=False)
        assert app.get("package") != package


# ── AdbChannel：纯单测，不连设备 ──

_SERIAL = "SERIAL-1"


class _FakeProc:
    """subprocess.run 返回值的替身。"""

    def __init__(self, returncode: int = 0, stdout: bytes = b"", stderr: bytes = b"") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _FakeSubprocess:
    """subprocess 模块替身：记录每次调用，按队列返回预设结果或抛出预设异常。"""

    def __init__(self, *results) -> None:
        self.calls: list[dict] = []
        self._results = list(results)

    def run(self, command, capture_output=True, timeout=None):
        self.calls.append(
            {"command": list(command), "capture_output": capture_output, "timeout": timeout}
        )
        result = self._results.pop(0) if self._results else _FakeProc()
        if isinstance(result, BaseException):
            raise result
        return result

    @property
    def command(self) -> list[str]:
        """最近一次调用的完整 argv。"""
        return self.calls[-1]["command"]


@pytest.fixture
def fake_subprocess(monkeypatch):
    """把 android_device 里的 subprocess 换成替身；返回安装函数，参数是预设结果队列。"""

    def _install(*results):
        fake = _FakeSubprocess(*results)
        monkeypatch.setattr(android_device, "subprocess", fake)
        return fake

    return _install


@pytest.mark.unit
class TestAdbChannel:
    """AdbChannel：命令拼装、编解码与失败上报。"""

    def test_shell_decodes_utf8_text(self, fake_subprocess):
        """shell 返回解码后的文本，argv 为 adb -s <serial> shell <args>。"""
        fake = fake_subprocess(_FakeProc(stdout="Physical size: 1080x2340\n".encode("utf-8")))
        output = AdbChannel(_SERIAL).shell(["wm", "size"])

        assert output == "Physical size: 1080x2340\n"
        assert fake.command == ["adb", "-s", _SERIAL, "shell", "wm", "size"]

    def test_shell_bytes_keeps_raw_bytes(self, fake_subprocess):
        """shell_bytes 不解码，二进制原样返回。"""
        png_head = b"\x89PNG\r\n\x1a\n"
        fake_subprocess(_FakeProc(stdout=png_head))

        assert AdbChannel(_SERIAL).shell_bytes(["cat", "x.png"]) == png_head

    def test_exec_out_uses_exec_out_channel(self, fake_subprocess):
        """exec_out 走 exec-out 子命令，不是 shell。"""
        fake = fake_subprocess(_FakeProc(stdout=b"\x89PNG"))
        AdbChannel(_SERIAL).exec_out(["screencap", "-p"])

        assert fake.command[:4] == ["adb", "-s", _SERIAL, "exec-out"]
        assert fake.command[4:] == ["screencap", "-p"]

    def test_host_omits_serial(self, fake_subprocess):
        """host 不带 -s，用于 adb devices 这类主机侧命令。"""
        fake = fake_subprocess(_FakeProc(stdout=b"List of devices attached\n"))
        AdbChannel(_SERIAL).host(["devices"])

        assert fake.command == ["adb", "devices"]

    def test_custom_executable_used_as_argv0(self, fake_subprocess):
        """构造时可指定 adb 可执行文件路径。"""
        fake = fake_subprocess()
        AdbChannel(_SERIAL, executable=r"C:\platform-tools\adb.exe").shell(["getprop"])

        assert fake.command[0] == r"C:\platform-tools\adb.exe"

    def test_timeout_forwarded_to_subprocess(self, fake_subprocess):
        """timeout 原样传给 subprocess.run。"""
        fake = fake_subprocess()

        AdbChannel(_SERIAL).shell(["wm", "size"], timeout=2.5)

        assert fake.calls[0]["timeout"] == 2.5
        assert fake.calls[0]["capture_output"] is True

    def test_failure_raises_with_stderr_and_command(self, fake_subprocess):
        """退出码非 0 时抛 RuntimeError，消息含命令与 stderr。"""
        fake_subprocess(_FakeProc(returncode=1, stderr=b"error: device offline"))

        with pytest.raises(RuntimeError) as exc:
            AdbChannel(_SERIAL).shell(["wm", "size"])

        message = str(exc.value)
        assert "error: device offline" in message
        assert "wm size" in message

    def test_failure_without_stderr_uses_default_message(self, fake_subprocess):
        """stderr 为空时用固定文案，不留空消息。"""
        fake_subprocess(_FakeProc(returncode=1))

        with pytest.raises(RuntimeError, match="未知错误"):
            AdbChannel(_SERIAL).shell(["wm", "size"])

    def test_failure_falls_back_to_stdout(self, fake_subprocess):
        """stderr 为空时用 stdout 作失败详情——设备侧报错走的是 stdout。"""
        fake_subprocess(_FakeProc(returncode=1, stdout=b"ls: /nope: No such file or directory\n"))

        with pytest.raises(RuntimeError) as exc:
            AdbChannel(_SERIAL).shell(["ls", "/nope"])

        assert "No such file or directory" in str(exc.value)

    def test_failure_detail_truncated(self, fake_subprocess):
        """失败详情按上限截断，不把整屏输出灌进异常。"""
        fake_subprocess(_FakeProc(returncode=1, stdout=b"x" * 500))

        with pytest.raises(RuntimeError) as exc:
            AdbChannel(_SERIAL).shell(["dump"])

        message = str(exc.value)
        assert message.count("x") == 200
        assert message.endswith("…")

    def test_non_utf8_output_does_not_raise(self, fake_subprocess):
        """非 UTF-8 字节按替换字符解码，不抛异常。"""
        fake_subprocess(_FakeProc(stdout=b"\xff\xfe"))

        output = AdbChannel(_SERIAL).shell(["cat", "x"])

        assert isinstance(output, str)
        assert "\ufffd" in output

    def test_timeout_expired_propagates(self, fake_subprocess):
        """subprocess 超时异常原样向上抛，不被吞掉。"""
        import subprocess as real_subprocess

        fake_subprocess(real_subprocess.TimeoutExpired(cmd="adb", timeout=2.5))

        with pytest.raises(real_subprocess.TimeoutExpired):
            AdbChannel(_SERIAL).shell(["wm", "size"], timeout=2.5)


@pytest.mark.unit
class TestBoundsCenter:
    """_bounds_center：把 bounds 文本解成中心点。"""

    def test_center_of_quad(self):
        """正常 bounds 取矩形中心。"""
        assert _bounds_center("[80,300][160,380]") == (120, 340)

    def test_odd_size_rounds_down(self):
        """宽高为奇数时向下取整。"""
        assert _bounds_center("[0,0][3,5]") == (1, 2)

    def test_negative_coords(self):
        """负坐标也能解析。"""
        assert _bounds_center("[-8,-4][12,16]") == (2, 6)

    def test_unparsable_returns_zero(self):
        """解析失败返回 (0, 0)，不抛异常。"""
        assert _bounds_center("bad") == (0, 0)
        assert _bounds_center("") == (0, 0)


# ── AdbInfo：纯单测，样本取自真机输出 ──

_WM_SIZE_BOTH = "Physical size: 1080x2340\nOverride size: 720x1560\n"
_WM_SIZE_PHYSICAL = "Physical size: 1080x2340\n"
_DUMPSYS_FOCUS = (
    "  mCurrentFocus=Window{ab5ed3d u0 com.govee.home/"
    "com.govee.h70b3.adjust.H681XSettingAc}\n"
    "  mFocusedApp=ActivityRecord{266269796 u0 com.govee.home/"
    "com.govee.h70b3.adjust.H681XSettingAc t98730}\n"
)
_PM_PACKAGES = (
    "package:com.sec.android.RilServiceModeApp\n"
    "package:com.baidu.carlife\n"
    "package:com.android.settings\n"
)
_ADB_DEVICES = (
    "List of devices attached\n"
    "R5CT62RH88F\tdevice\n"
    "192.168.35.57:39569\tdevice\n"
    "adb-RF8N21MSW7A-7tM54C._adb-tls-connect._tcp\toffline\n"
)
_HIERARCHY_XML = (
    "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>"
    '<hierarchy rotation="0"><node index="0" text="" resource-id="" /></hierarchy>'
)


@pytest.mark.unit
class TestAdbInfo:
    """AdbInfo：命令选择与各解析器的边界。"""

    def test_screen_size_prefers_override(self, fake_subprocess):
        """Override 与 Physical 同时存在时取 Override。"""
        fake = fake_subprocess(_FakeProc(stdout=_WM_SIZE_BOTH.encode("utf-8")))

        assert AdbInfo(_SERIAL).screen_size() == (720, 1560)
        assert fake.command == ["adb", "-s", _SERIAL, "shell", "wm", "size"]

    def test_screen_size_falls_back_to_physical(self, fake_subprocess):
        """只有 Physical 时取 Physical。"""
        fake_subprocess(_FakeProc(stdout=_WM_SIZE_PHYSICAL.encode("utf-8")))

        assert AdbInfo(_SERIAL).screen_size() == (1080, 2340)

    def test_screen_size_raises_when_unparseable(self, fake_subprocess):
        """两种尺寸都解析不到时抛 RuntimeError，不返回 (0, 0)。"""
        fake_subprocess(_FakeProc(stdout=b"garbage\n"))

        with pytest.raises(RuntimeError, match="wm size"):
            AdbInfo(_SERIAL).screen_size()

    def test_current_app_parses_package_and_activity(self, fake_subprocess):
        """从 mCurrentFocus 行取包名与 Activity。"""
        fake = fake_subprocess(_FakeProc(stdout=_DUMPSYS_FOCUS.encode("utf-8")))

        assert AdbInfo(_SERIAL).current_app() == {
            "package": "com.govee.home",
            "activity": "com.govee.h70b3.adjust.H681XSettingAc",
        }
        assert fake.command == ["adb", "-s", _SERIAL, "shell", "dumpsys", "window"]

    def test_current_app_returns_empty_when_no_focus(self, fake_subprocess):
        """没有 mCurrentFocus 时返回空串，不抛异常。"""
        fake_subprocess(_FakeProc(stdout=b"  mFocusedApp=ActivityRecord{1 u0 a/b}\n"))

        assert AdbInfo(_SERIAL).current_app() == {"package": "", "activity": ""}

    def test_packages_returns_all(self, fake_subprocess):
        """空关键词返回全部包名，冒号前缀被剥掉。"""
        fake_subprocess(_FakeProc(stdout=_PM_PACKAGES.encode("utf-8")))

        assert AdbInfo(_SERIAL).packages() == [
            "com.sec.android.RilServiceModeApp",
            "com.baidu.carlife",
            "com.android.settings",
        ]

    def test_packages_filters_case_insensitive(self, fake_subprocess):
        """关键词忽略大小写做子串匹配。"""
        fake_subprocess(_FakeProc(stdout=_PM_PACKAGES.encode("utf-8")))

        assert AdbInfo(_SERIAL).packages("SETTINGS") == ["com.android.settings"]

    def test_connected_devices_keeps_only_device_state(self, fake_subprocess):
        """只保留状态为 device 的行，offline 等一律丢弃。"""
        fake = fake_subprocess(_FakeProc(stdout=_ADB_DEVICES.encode("utf-8")))

        assert AdbInfo(_SERIAL).connected_devices() == [
            "R5CT62RH88F",
            "192.168.35.57:39569",
        ]
        assert fake.command == ["adb", "devices"]

    def test_hierarchy_xml_dumps_then_reads(self, fake_subprocess):
        """先 dump 到固定路径，再 cat 回读；返回 cat 的内容。"""
        fake = fake_subprocess(
            _FakeProc(stdout=b"UI hierchary dumped to: /data/local/tmp/window_dump.xml\n"),
            _FakeProc(stdout=_HIERARCHY_XML.encode("utf-8")),
        )

        xml = AdbInfo(_SERIAL).hierarchy_xml()

        assert fake.calls[0]["command"] == [
            "adb",
            "-s",
            _SERIAL,
            "shell",
            "uiautomator",
            "dump",
            "/data/local/tmp/window_dump.xml",
        ]
        assert fake.calls[1]["command"] == [
            "adb",
            "-s",
            _SERIAL,
            "shell",
            "cat",
            "/data/local/tmp/window_dump.xml",
        ]
        assert xml == _HIERARCHY_XML

    def test_hierarchy_xml_raises_when_dump_fails(self, fake_subprocess):
        """dump 失败时抛 RuntimeError，不再执行 cat。"""
        fake = fake_subprocess(_FakeProc(returncode=1, stdout=b"ERROR: could not get idle state"))

        with pytest.raises(RuntimeError, match="could not get idle state"):
            AdbInfo(_SERIAL).hierarchy_xml()

        assert len(fake.calls) == 1


# ── AdbChannel：真机验证命令通道与二进制安全 ──

_ADB_CHANNEL_KEY = "TestAdbChannel"


def _adb_channel_cases() -> list[dict]:
    return _yaml_rows(_ADB_CHANNEL_KEY)


def _open_adb_channel(case: dict) -> AdbChannel:
    """取一个可用的 AdbChannel；数据里带 address 时先建立无线连接。"""
    if case.get("address"):
        AndroidConnection(_config(case)).connect()
    return AdbChannel(str(case["serial"]))


@pytest.mark.parametrize(
    "case",
    _adb_channel_cases(),
    ids=lambda case: str(case["serial"]),
)
class TestAdbChannelDevice:
    """AdbChannel：真机跑通 shell / shell_bytes / exec-out / host 与两类失败。"""

    def test_shell_returns_device_text(self, case):
        """shell 返回设备侧命令的文本输出。"""
        output = _open_adb_channel(case).shell(["echo", "probe"])
        print(f"\nshell echo probe: {output!r}")
        assert "probe" in output

    def test_shell_returns_build_version(self, case):
        """shell 能取到真实属性值。"""
        version = _open_adb_channel(case).shell(["getprop", "ro.build.version.release"])
        print(f"\nro.build.version.release: {version.strip()!r}")
        assert version.strip()

    def test_shell_bytes_returns_bytes(self, case):
        """shell_bytes 返回 bytes，不解码。"""
        data = _open_adb_channel(case).shell_bytes(["getprop", "ro.product.model"])
        print(f"\nro.product.model: {data!r}")
        assert isinstance(data, bytes)
        assert data.strip()

    def test_exec_out_screencap_is_valid_png(self, case):
        """exec-out 抓图必须是合法 PNG：验证不走 PTY、二进制没被改。"""
        from PIL import Image

        png = _open_adb_channel(case).exec_out(["screencap", "-p"])
        print(f"\nscreencap: {len(png)} 字节，开头 {png[:8]!r}")

        assert png.startswith(b"\x89PNG\r\n\x1a\n")
        with Image.open(io.BytesIO(png)) as img:
            print(f"图片尺寸: {img.size}")
            assert img.size[0] > 0 and img.size[1] > 0

    def test_host_lists_serial(self, case):
        """host 不带 -s，但仍能列出本机；序列号出现在 adb devices 里。"""
        listed = _open_adb_channel(case).host(["devices"])
        serial = str(case["serial"])
        print(f"\nserial: {serial}\nadb devices:\n{listed}")

        # adb 在 Windows 上输出 CRLF，行尾要允许 \r
        matched = re.search(rf"^{re.escape(serial)}[ \t]+device\r?$", listed, re.MULTILINE)
        assert matched, listed

    def test_device_command_failure_raises(self, case):
        """设备侧命令返回非 0 时抛 RuntimeError。"""
        with pytest.raises(RuntimeError) as exc:
            _open_adb_channel(case).shell(["false"])

        print(f"\n失败消息: {exc.value}")
        assert str(exc.value).strip()

    def test_device_failure_detail_uses_stdout(self, case):
        """设备侧报错时详情取自设备输出，不再是「未知错误」。"""
        with pytest.raises(RuntimeError) as exc:
            _open_adb_channel(case).shell(["ls", "/data/local/tmp/definitely-not-here"])

        print(f"\n失败消息: {exc.value}")
        assert "未知错误" not in str(exc.value)

    def test_command_timeout_raises(self, case):
        """命令超时抛 subprocess.TimeoutExpired，不被吞掉。"""
        import subprocess as real_subprocess

        with pytest.raises(real_subprocess.TimeoutExpired):
            _open_adb_channel(case).shell(["sleep", "3"], timeout=0.3)


# ── AdbInfo：真机验证各查询方法的取值合理性 ──

_ADB_INFO_KEY = "TestAdbInfo"


def _adb_info_cases() -> list[dict]:
    return _yaml_rows(_ADB_INFO_KEY)


def _open_adb_info(case: dict) -> AdbInfo:
    """取一个可用的 AdbInfo；数据里带 address 时先建立无线连接。"""
    if case.get("address"):
        AndroidConnection(_config(case)).connect()
    return AdbInfo(str(case["serial"]))


@pytest.mark.parametrize(
    "case",
    _adb_info_cases(),
    ids=lambda case: str(case["serial"]),
)
class TestAdbInfoDevice:
    """AdbInfo：真机跑通分辨率 / 前台应用 / 包名 / 已连接设备 / 层级 XML。"""

    def test_screen_size(self, case):
        """分辨率两项都为正整数，且与 wm size 原文对得上。"""
        info = _open_adb_info(case)
        width, height = info.screen_size()
        raw = info.adb.shell(["wm", "size"])
        print(f"\nscreen_size: {width}x{height}\nwm size: {raw.strip()}")

        assert width > 0 and height > 0
        assert f"{width}x{height}" in raw

    def test_current_app(self, case):
        """能取到当前前台应用，包名与 Activity 都非空。"""
        app = _open_adb_info(case).current_app()
        print(f"\ncurrent_app: {app}")

        assert app["package"]
        assert app["activity"]

    def test_packages(self, case):
        """包名列表非空，且关键词过滤后都命中关键词。"""
        info = _open_adb_info(case)
        names = info.packages()
        narrowed = info.packages("android")
        print(f"\npackages: {len(names)}，android 过滤后 {len(narrowed)}")

        assert names
        assert narrowed
        assert all("android" in name.lower() for name in narrowed)

    def test_connected_devices(self, case):
        """已连接列表里能看到本机序列号。"""
        serials = _open_adb_info(case).connected_devices()
        expected = str(case["serial"])
        print(f"\nconnected_devices: {serials}")

        assert expected in serials

    def test_hierarchy_xml(self, case):
        """层级输出是合法 XML 文本。"""
        xml = _open_adb_info(case).hierarchy_xml()
        print(f"\nhierarchy_xml: {len(xml)} 字符，开头 {xml[:80]!r}")

        assert xml.lstrip().startswith("<?xml") or "<hierarchy" in xml


# ── AndroidControl：u2 会话惰性（纯替身，不连设备） ──

_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def _fake_u2_elements() -> list:
    """u2 xpath 命中结果替身：一条带文本与 bounds 的元素。"""

    class _Element:
        attrib = {"text": "H6110", "bounds": "[100,200][300,400]"}

    return [_Element()]


def _install_u2_spy(monkeypatch, *, raises: Exception | None = None) -> list[str]:
    """把 u2.connect 换成计数替身，返回调用记录（元素是连接时传入的 serial）。"""
    calls: list[str] = []

    class _FakeXpath:
        def all(self):
            return _fake_u2_elements()

    class _FakeDevice:
        def xpath(self, _expr):
            return _FakeXpath()

        def shell(self, *_args, **_kwargs):
            return ""

        def send_keys(self, _text):
            return None

    def _connect(serial):
        calls.append(str(serial))
        if raises is not None:
            raise raises
        return _FakeDevice()

    monkeypatch.setattr(android_device.u2, "connect", _connect)
    return calls


class TestAndroidControlU2Lazy:
    """u2 只在 xpath 查询 / 非 ASCII 输入时连接；构造与截图都不碰 u2。"""

    def test_construct_does_not_connect(self, monkeypatch):
        """构造 AndroidControl 不建立 u2 会话。"""
        calls = _install_u2_spy(monkeypatch)
        android_device.AndroidControl("serial-lazy")

        assert calls == []

    def test_screenshot_does_not_connect(self, monkeypatch):
        """截图只走 adb，不建立 u2 会话。"""
        calls = _install_u2_spy(monkeypatch)
        control = android_device.AndroidControl("serial-lazy")
        monkeypatch.setattr(control.adb, "exec_out", lambda *_a, **_k: _PNG_BYTES)

        assert control.screenshot_bytes() == _PNG_BYTES
        assert calls == []

    def test_xpath_connects_once_and_reuses(self, monkeypatch):
        """xpath 查询才连接，且同一实例复用同一个会话。"""
        calls = _install_u2_spy(monkeypatch)
        control = android_device.AndroidControl("serial-lazy")

        first = control.find_xpath("//x")
        second = control.find_xpath("//x")

        assert len(calls) == 1
        assert first == [{"text": "H6110", "x": 200, "y": 300}]
        assert second == first

    def test_u2_failure_is_readable_and_screenshot_survives(self, monkeypatch):
        """u2 连不上时 xpath 报可读错误，截图照旧成功。"""
        _install_u2_spy(monkeypatch, raises=RuntimeError("agent offline"))
        control = android_device.AndroidControl("serial-lazy")
        monkeypatch.setattr(control.adb, "exec_out", lambda *_a, **_k: _PNG_BYTES)

        assert control.screenshot_bytes() == _PNG_BYTES
        with pytest.raises(RuntimeError) as exc:
            control.find_xpath("//x")

        assert "uiautomator2 连接失败" in str(exc.value)
