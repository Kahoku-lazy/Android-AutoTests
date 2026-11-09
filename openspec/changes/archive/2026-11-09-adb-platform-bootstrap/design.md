## Context

平台需要「不依赖系统 PATH 的 adb」。现状是 6 处 `subprocess.run(["adb", ...])` 加两个常量 `"adb"`；`adbutils` 依赖里已经带了平台对应的 `adb`，只是没人用它。本设计锁定解析优先级、安装器的落位与校验方式、以及失败时的语义。

## Decisions

### D1 解析优先级：平台自带优先，绝不回退系统 PATH

```
1. ADB_PATH 环境变量（显式覆盖，存在且可执行才生效）
2. <repo>/tools/platform-tools/adb(.exe)      ← run.py setup 安装到这里
3. <site-packages>/adbutils/binaries/adb(.exe) ← pip 依赖自带
4. 抛 AdbUnavailableError（可操作文案）
```

- 不做 PATH 兜底：PATH 上的版本不可控，静默使用会掩盖部署配置问题；确需用系统 adb 的人可以显式设 `ADB_PATH`。
- 解析结果在进程内缓存，同时写入 `ADBUTILS_ADB_PATH`，让 `uiautomator2`/`adbutils` 与平台用同一份二进制。
- 不在模块导入期求值：`run.py setup` 可能在本进程内刚装好 adb，常量式写法会拿到旧值。

### D2 二进制不入库

- 仓库当前 pack 52.65 MiB；三个平台各 7.7/15.4/8.6 MB，入库会让历史永久膨胀，还要处理 Android SDK 再分发许可。
- 下载发生在使用者机器上，不构成再分发；离线装机用 `--from-file`。

### D3 版本 pin，而不是 `latest`

- 固定 `platform-tools 37.0.2`，每平台记录 `file / size / sha1`（取自官方 `repository2-3.xml`，已实测三个 URL 均 200）。
- 校验顺序：`size` → `sha1`；任一不符删除临时文件并报错，不进入解压。
- 官方只给 sha1；安装成功后把 **sha256** 也写进 `tools/platform-tools/.platform-tools.json`，后续排查/升级可对比。
- `--latest` 需要联网解析 XML，本变更不实现（避免“默认联网”）。

### D4 安装是原子替换 + 安全解压

1. 下载/复制 zip 到 `tools/.cache/`（下载写 `.part` 再改名）。
2. 解压到 `tools/.cache/extract-<rand>/`（拒绝绝对路径与 `..` 条目，防 zip-slip）。
3. 校验解压出的 `platform-tools/adb(.exe)` 存在 → 再替换 `tools/platform-tools/`（先移走旧目录，失败回滚）。
4. POSIX `chmod 0755 adb`；执行 `<adb> version` 自检；写 meta。
5. 清理临时目录。

### D5 `uiautomator2` 对齐

`adb_binary()` 成功后执行 `os.environ.setdefault("ADBUTILS_ADB_PATH", resolved)`。
`probe_u2` / `fetch_device_info` 在连接前显式调用一次解析器，保证 u2 不会回落到 PATH。

### D6 控制台行为

- `python run.py setup`：检测 → 缺失/`--force` 才下载 → 安装 → 打印路径与版本。
- `python run.py setup --check`：只检测，缺失时退出码 1（CI/脚本可判）。
- `python run.py setup --from-file <zip>`：离线安装（同样校验 size/sha1）。
- `python run.py start`：解析失败只打印提示，**不自动联网**；`AUTO_SETUP=1` 时先跑安装再启动。
- `python run.py status`：新增 `ADB` 行，显示来源（`platform` / `env` / `bundled` / `MISSING`）与版本。

### D7 设备接口的失败语义

- `DeviceDetector.adb_device_serials()` 不再吞掉 `AdbUnavailableError`（其它异常仍按空集合处理，保持既有容错）。
- `GET /api/devices/` 与 `POST /api/devices/scan/` 捕获该错误 → `503` + `{"message": "未找到平台自带 adb，请运行 python run.py setup"}`。
- 其它异常仍走原有 500 分支。

### D8 不做的事

- 不处理 Linux udev/USB 权限（需要 root，文档写明「`adb devices` 显示 no permissions 时需要配置 udev 规则」）。
- 不处理 macOS 隔离属性（Python `urllib` 下载不会带 `com.apple.quarantine`，以实测为准）。
- 不实现 `--latest`、不做二进制校验签名（官方仅 sha1）。
- 不改变设备动作/协议语义。

### D9 Windows 上的 daemon 日志规避（实测发现）

platform-tools 37.0.2 的 adb daemon 会把日志写到 `%TEMP%\adb.log`；在本机（Windows 11 26200）该文件打不开，
daemon 启动直接失败：

```
F adb : main.cpp:54 cannot open C:\Users\...\Temp\adb.log: Permission denied
could not read ok from ADB Server
```

对照实验：35.0.2 / 36.0.0 可正常起 daemon；把 `ANDROID_ADB_LOG_PATH` 指向 `NUL` 后 37.0.2 也能起，
设备可正常列出。因此 `utils.adb.adb_binary()` 在 Windows 上统一
`os.environ.setdefault("ANDROID_ADB_LOG_PATH", os.devnull)`，代价是 daemon 日志关闭
（客户端 stderr 仍可见错误），换来跨机器可用。该兜底只在 Windows 生效，POSIX 不动。

## Risks

| 风险 | 缓解 |
|---|---|
| 下载失败（无网/代理） | 明确错误 + `--from-file` 离线；不自动触发下载 |
| 文件被占用导致替换失败（Windows） | 先解压后替换；失败回滚旧目录并给出提示 |
| `adbutils` 在未来版本不再内置 adb | 项目内 `tools/platform-tools/` 优先，安装器即兜底 |
| Linux 上装了 adb 仍看不到设备 | 文档明确 udev；接口错误文案只覆盖「adb 缺失」，不误报权限问题 |
| 现有测试断言 `["adb", ...]` | 测试改为注入解析结果；另加一条断言「命令首项 = 解析路径」 |

## Migration Steps

1. 新增 `utils/adb.py`（解析器）与 `utils/platform_tools.py`（下载/校验/解压/安装）。
2. 替换 6 处调用点与 2 个常量；`live_screen` 复用同一解析器。
3. `views.list_devices` / `scan_device` 增加 503 分支。
4. `run.py` 增加 `setup`、`status` 的 ADB 行、`start` 提示与 `AUTO_SETUP`。
5. 测试：解析器优先级、安装器（真 zip 假下载）、zip-slip、缺 adb 的接口语义、引擎命令首项。
6. 文档：README（环境要求/启动/目录表）、`.gitignore`、`backend/apps/device_pool` 说明。
