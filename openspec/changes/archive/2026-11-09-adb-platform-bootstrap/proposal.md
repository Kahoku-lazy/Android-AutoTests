## Why

平台目前把 `adb` 当成 PATH 上的外部命令：后端设备池 5 处、设备引擎 1 处 + 2 个常量，全部直接执行字面量 `"adb"`（[`manager.py`](../../backend/apps/device_pool/manager.py)、[`android_device.py`](../../engines/device/android/android_device.py)）。这带来三个问题：

1. **换机器就要先配环境**：新机器/新同事必须先装 platform-tools 并配 PATH，否则设备页静默显示为空；
2. **失败不可读**：`adb devices` 的 `FileNotFoundError` 被 `except Exception` 吞成空集合；无线连接/配对的同类异常直接冒成 500；
3. **版本不可控**：不同机器的系统 adb 版本不同，无线配对/`exec-out` 行为有差异时很难排查。

平台其实已经有可用的“自带 adb”基础：`adbutils` 依赖里打包了 `<site-packages>/adbutils/binaries/adb(.exe)`，`utils/live_screen.py` 也已经写过「PATH → adbutils 内置」的解析。本次把这条链路升格为平台统一策略，并补一个控制台安装器，让“项目环境里没有 adb”可以一条命令自愈。

## What Changes

- 新增 `utils/adb.py`：统一的 adb 可执行文件解析（`ADB_PATH` 环境变量 → 项目内 `tools/platform-tools/adb` → `adbutils` 包内置 → 抛 `AdbUnavailableError`），**不回退系统 PATH**。
- 新增 `utils/platform_tools.py` + `python run.py setup`：按当前系统下载官方 platform-tools（版本 pin 死、带 size + sha1 校验、安全解压、`chmod`、`adb version` 自检），安装到 `tools/platform-tools/`（gitignore）；支持 `--check` / `--force` / `--from-file`（离线）。
- 6 处硬编码 `"adb"` 与 2 个常量改为调用解析器；进程启动时把解析结果写进 `ADBUTILS_ADB_PATH`，让 `uiautomator2` 也使用同一份 adb。
- adb 缺失时 `/api/devices/` 与扫描接口返回 **503 + 可操作提示**（指向 `python run.py setup`），不再静默空列表或 500。
- 文档与环境约定：README 环境要求、`run.py` usage、`tools/platform-tools/` 的 gitignore。

## Impact

- 新增能力：`python run.py setup`（唯一会联网的命令，默认不自动执行）。
- 行为变化：adb 缺失时设备列表由「静默为空」变为「503 + 提示」。
- 不改变：设备协议、动作语义、鉴权、任务链路；Linux udev 权限不在本变更范围（文档注明）。
- 体积：仓库不新增二进制；安装产物在 `tools/platform-tools/`（约 8–16 MB，gitignore）。
