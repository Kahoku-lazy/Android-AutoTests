## 1. adb 解析器（`utils/adb.py`）

- [x] 1.1 新增 `utils/adb.py`：`adb_binary()` 按 `ADB_PATH` → `tools/platform-tools/adb` → `adbutils` 内置 → 抛 `AdbUnavailableError`；`adb_source()` 返回来源标签；解析结果写入 `ADBUTILS_ADB_PATH`（Windows 另设 `ANDROID_ADB_LOG_PATH=NUL`，见 design D9）。验证：`test_adb_resolver.py` 8 条覆盖四种来源、PATH 诱饵、u2 同步与 Windows 日志规避。
- [x] 1.2 解析结果做进程内缓存并提供 `reset_cache()`。验证：安装后 `reset_cache` 能拿到新路径（`test_reset_cache_picks_up_new_install`）。

## 2. 调用点替换

- [x] 2.1 `backend/apps/device_pool/manager.py`：5 处 `["adb", ...]` 改为 `adb_binary()`；`adb_device_serials()` 不吞 `AdbUnavailableError`，其它异常仍按空集合容错；connect/pair 把该错误映射为 503。验证：`tests/device_pool` 4 条与 `test_device_adb_missing.py` 3 条全绿。
- [x] 2.2 `engines/device/android/android_device.py`：`_run_adb`、`_run`、`AdbChannel` 默认 executable 改为解析器。验证：引擎单测新增「argv0 = 解析路径」，既有断言用 autouse 夹具固定为 `"adb"`。
- [x] 2.3 `utils/live_screen.py` 的 `adb_path()` 改为复用 `utils.adb.adb_binary()`。验证：`python -m utils.live_screen --help` 正常。
- [x] 2.4 `engines/device/connection.py`：`probe_u2` / `fetch_device_info` 前显式解析一次 adb，保证 u2 使用同一份。验证：代码路径审查 + 解析器用例。

## 3. 接口语义

- [x] 3.1 `views.list_devices` 与 `views.scan_device` 捕获 `AdbUnavailableError` → 503 + 「未找到平台自带 adb，请运行 python run.py setup」。验证：`test_device_adb_missing.py` 断言 503 与 message。
- [x] 3.2 其它异常保持原 500 分支。验证：同文件 `test_list_devices_other_errors_still_500`。

## 4. 控制台安装器（`utils/platform_tools.py` + `run.py setup`）

- [x] 4.1 `utils/platform_tools.py`：pin 37.0.2（size + sha1 见常量），下载到 `tools/.cache`、校验、安全解压、原子替换、POSIX chmod、`adb version` 自检、写 `.platform-tools.json`（含 sha256）；替换前 `adb kill-server`。验证：`test_platform_tools_install.py` 7 条（安装/幂等/force/大小/校验和/zip-slip/缺 adb）。
- [x] 4.2 `run.py` 新增 `setup`（`--check` / `--force` / `--from-file`）；`status` 增加 ADB 行；`start` 缺 adb 时提示，`AUTO_SETUP=1` 才自动安装。验证：实测 `setup` 下载 7.7 MB 并落位、`setup --check` exit 0、`status` 显示 `ADB: platform 1.0.41`。
- [x] 4.3 `.gitignore` 增加 `tools/platform-tools/`、`tools/.cache/`。验证：安装后 `git status -- tools` 为空。

## 5. 测试

- [x] 5.1 `tests/graybox/unit/test_adb_resolver.py`（7 条）。
- [x] 5.2 `tests/graybox/unit/test_platform_tools_install.py`（7 条）。
- [x] 5.3 `tests/graybox/unit/test_device_adb_missing.py`（3 条）。
- [x] 5.4 `tests/engines/devices/test_android_device.py`：新增解析路径用例 + autouse 夹具；纯单测部分（TestAdbChannel/TestAdbInfo）通过（`TestAdbInfo::test_current_app_parses_package_and_activity` 的 `dumpsys window displays` 漂移为**变更前既有**失败，本单未触碰该行）。

## 6. 文档

- [x] 6.1 `README.md`：环境要求 ADB 行、安装步骤、启动命令、目录表补 `tools/platform-tools/`。
- [x] 6.2 `manager.py` 模块注释写明 adb 来源与 503 语义。
- [x] 6.3 `run.py` usage 与 argparse help 补 `setup`。

## 7. 收口

- [x] 7.1 门禁：`python run.py check` → **阻塞项 23/23 通过**（engines 告警项 22 条，均为既有 docstring 问题）。
- [x] 7.2 冒烟：`setup --check` exit 0；`status` 显示 `ADB: platform 1.0.41`；`GET /api/devices/` 返回 200（真实接口，adb 已安装）。
- [x] 7.3 人工验收（真实设备）：设备 **RF8N21MSW7A（Samsung SM-G9730）** 经平台 API 完成 —— `POST /api/devices/scan/` 200 且 `count=1`；`GET /api/devices/` 200 且 `current=RF8N21MSW7A`；`POST /api/devices/RF8N21MSW7A/` 200 返回 `SM-G9730 / 1440x3040 / Android 30`。全程使用项目内 `tools/platform-tools/adb.exe`（37.0.2）。macOS/Linux 的 `setup` 仍待用户在有设备的机器上验证。
