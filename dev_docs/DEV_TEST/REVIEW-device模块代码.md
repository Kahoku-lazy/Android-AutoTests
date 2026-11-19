# engines/device 代码评审报告

- 评审对象：`engines/device/`（9 个文件，1755 行新增口径）
- 评审日期：2026-11-19
- 评审方式：
  1. **open-code-review v1.13.12 原生模式**：`ocr scan --path engines/device --audience agent`
     - 9 文件 / 23 条意见 / 约 32.4 万 token / 4 分 40 秒
     - 会话 ID：`a76225f8-6a38-40fa-b728-34054bdacdb5`
     - 原始输出：`temps/ocr_scan_device.txt`
  2. **仓库自带机械检查**（补充口，非 OCR 产物）
     - `python -m scripts.check_engines_agents_style --path engines/device` → 7 条 `raises-doc`
     - `python -m scripts.docstrings check --path engines/device` → 90 error / 3 warn
- 说明：OCR 意见已逐条回读源码核实，**误报与降级项单列在末节**；本次只评审、未改任何代码。

## 一、总结论

- 模块整体分层是干净的：`action.py` 是唯一对外入口，`android/` 由 `System` 表按需 import，没有 `apps.*` / `django.*` 反向依赖，动作名与抽象层对齐。
- **有 1 项安全问题必须先修**：输入文本两条路径都把文本直接拼进设备 shell，可被注入命令。
- **有 1 项红线违规**：无线配对码明文写进日志（含 `_run_adb` 二次泄露）。
- **有 3 项契约类缺陷**（ABC 签名断裂、超时不归一、`open_device` 泄漏连接）会在换系统 / 掉线 / 部分失败时变成真实故障。
- **有 4 处「声明了但没接上」**：`U2_OP_TIMEOUT`、`uuid`、`config.ini`、`capture_png` —— 属于文档承诺与实现脱节，比纯死代码更危险，因为调用方会按承诺使用。
- 注释欠账集中在 `Args:` / `Returns:`（74 条），是全文件的存量问题，不是本次引入。

## 二、高（建议本周内修）

### H1. `input_text` 设备侧命令注入（安全）

- 位置：`engines/device/android/android_device.py:643-659`（adb 路径）、`:898-902`（u2 兜底路径）
- 事实：
  - adb 路径 `self.adb.shell(["input", "text", value.replace(" ", "%s")])`：`AdbChannel._exec` 用 argv 列表起进程，但 **adb 客户端会把 `shell` 后的参数空格拼接成一条远端命令**，再由设备 `sh` 重新解析，所以 `;`、`&`、`|`、反引号、`$()` 照样生效，列表形式**不提供保护**。
  - u2 兜底路径 `device.shell(f"input text '{safe}'")`，`safe = text.replace("'", "\\'")`：POSIX 单引号内反斜杠是字面量，`\'` 等于「结束引号 + 反斜杠」，因此 `a'; <cmd>; '` 直接执行。
- 影响：文本来自 Agent 工具入参（LLM 或用户可控），注入面是整台测试设备的 shell。
- 建议：统一 `shlex.quote(text.replace(" ", "%s"))`（`shlex` 提到模块顶部 import）；u2 路径同样改为 `device.shell(f"input text {shlex.quote(...)}")`。

### H2. 配对码明文入日志（违反「不把密钥写入日志」红线）

- 位置：`engines/device/android/android_device.py:178`、`:109-122`
- 事实：`_adb_pair` 打印 `（地址、端口号、配对码）: {endpoint} {code}`；`_run_adb` 又把完整命令行 `" ".join(args)` 打一遍，并对结果再打一遍——同一个凭据进日志两次。
- 建议：调用点只打 endpoint；`_run_adb` 对 `pair` 子命令的末位参数做掩码（如 `pair <addr> ******`），日志文案里不再出现 code 原文。

## 三、中（排期修，或明确写进「已知限制」）

### M1. ABC 契约断裂：`connect` 签名不一致

- 位置：`engines/device/action.py:134-136`（抽象 `connect(self, serial, addr="")`）vs `engines/device/android/android_device.py:187`（实现 `connect(self)` 无参）
- 事实：`open_device` 走 Android 分支时 `connection.connect()`，走通用分支时 `connection.connect(target)`——两条分支依赖互不兼容的签名。新增任一系统、或把 Android 改走通用分支，立刻 `TypeError`。
- 建议：二选一收敛。推荐抽象层改成 `connect()` 无参 + 目标经构造器传入（与现有 Android 实现一致），`open_device` 两分支统一。

### M2. `AdbChannel._exec` 不把超时归一成 `RuntimeError`

- 位置：`engines/device/android/android_device.py:365-373`
- 事实：`subprocess.run(..., timeout=timeout)` 超时抛 `subprocess.TimeoutExpired`，而 `shell` / `shell_bytes` / `exec_out` / `host` 四个公开方法的 docstring 只承诺 `RuntimeError`。按契约写 `except RuntimeError` 的调用方在设备掉线/卡死时会直接崩。
- 建议：`except subprocess.TimeoutExpired as exc: raise RuntimeError(f"adb {' '.join(args)} 超时（{timeout}s）") from exc`，与 `AndroidConnection._run_adb` 的处理对齐。

### M3. `logbus.from_file` 的「降级」承诺漏了一类异常

- 位置：`engines/device/logbus.py:79-83`
- 事实：docstring 承诺「文件缺失或损坏时返回空索引」，但 `Path.read_text(encoding="utf-8")` 遇到非 UTF-8 字节抛 `UnicodeDecodeError`（`ValueError` 子类），不在捕获元组 `(OSError, json.JSONDecodeError)` 内；而 `JSONDecodeError` 本身也是 `ValueError`。
- 建议：改成 `except (OSError, ValueError)`，一次覆盖编码错与 JSON 错；日志照旧给可读原因。
- 触发面：`KeywordIndex.from_file` 现由 `backend/apps/task_list/log_history.py` 直接调用，坏文件会让请求 500 而不是「关键词匹配关闭」。

### M4. `open_device` 部分失败会泄漏连接

- 位置：`engines/device/action.py:408-417`
- 事实：`_android_connection()` 已经把连接建好，紧接着 `System.info(name)(target)` / `System.control(name)(target)` 里 `AdbChannel.__init__` 会调 `adb_binary()`（可能抛 `AdbUnavailableError`）。抛在这里时前面建立的连接无人 `disconnect()`。
- 建议：info / control 构造包 `try/except`，失败先 `connection.disconnect()` 再原样 `raise`。

### M5. `Screenshot.capture` 声明了校验但没做

- 位置：`engines/device/action.py:358-373`
- 事实：docstring 写 `Raises RuntimeError: 控制实现截屏失败或返回的不是图片`，实现却对 `None` / 空字节照常 `base64` 并靠 `getattr` 兜底标成 `image/jpeg`；同时 `DeviceControl.screenshot_b64()` 已提供同一段编码逻辑，这里重复了一遍。
- 建议：`if not raw: raise RuntimeError(...)`；编码复用 `screenshot_b64()`。

### M6. `U2_OP_TIMEOUT` 声明了但从未生效

- 位置：`engines/device/android/android_device.py:43-44`（常量）、`:835-850`（`device` 属性）
- 事实：全仓 grep 只有常量定义（其余命中在已归档的 openspec 文档里），`u2.connect()` 之后没有任何超时调优，u2 默认 `HTTP_TIMEOUT=300`。常量注释说的「设备冻结会永久阻塞」仍然成立：`find_xpath` / `send_keys` 最长可挂 5 分钟。
- 建议：在 `_u2_device` 建立后按原设计写入真超时；或删除常量与注释里的 20 秒承诺。二选一，不要留「看起来设过」的假象。

### M7. `uuid` 字段无人读，USB 连接无探活

- 位置：`engines/device/android/android_device.py:49-63`、`:187-201`
- 事实：`action.py:388` 用 `AndroidConnectionConfig(uuid=target)` 填了 UUID，模块内再没有读；`connect()` 只在有 `pair_code` / `address` 时分支出命令，USB 配置下**直接返回成功**，不做任何存活校验。
- 校正一条 OCR 判断：设备定向本身没坏 —— 真正下命令的 `AdbChannel` 每条都带 `-s <serial>`；坏的只是「USB connect 不验证」。
- 建议：USB 分支加一次 `adb -s <uuid> get-state` 校验（失败抛 `EngineConnectError`），或删字段并在 docstring 写明「USB 无需连接步骤」。

### M8. `config.ini` 既不可解析也无人读

- 位置：`engines/device/config.ini:1-2`
- 事实：没有 section 头（`configparser` 会抛 `MissingSectionHeaderError`）；值是硬编码 `D:\Govee\data\screenshots\engine_shots`；全仓 grep `screenshots_path` 与 `engines/device/config.ini` 都没有消费者（截图路径已改为「不落盘」口径）。
- 建议：直接删文件；要保留就补 `[paths]`、改环境变量/仓库相对路径，并接上唯一入口 `action`。

### M9. `recent_apps` 把设备过程日志写进 Agent 事件流（口径冲突，需定调）

- 位置：`engines/device/android/recent_apps.py:31,56-62,118-120`
- 事实：用的是 `utils.logs.agent_event_log`（写 `agents/agent_events.log`），而 `engines/device/AGENTS.md` 第 6 条要求「用 `utils.logs.device_log`」；该模块 docstring 又自述「过程日志（agent_event_log），不依赖任何 Agent 包」，说明是**有意为之**。
- 判断：不是 bug，是规则与实现的口径不一致。要么按 AGENTS 改 `device_log`，要么在 `engines/device/AGENTS.md` 里把「收尾类过程日志走 agent 事件流」写成例外——**这是规则改动，按根 AGENTS 第 4 条须先请示**。

## 四、低（顺手清）

| 位置 | 问题 | 建议 |
| --- | --- | --- |
| `android_device.py:208-214` | `_bounds_center` 用 `lstrip("-")` 判数字，`"--5"` 能过校验再在 `int()` 炸，违背「解析失败返回 (0,0)」 | 改 `re.fullmatch(r"-?\d+", part.strip())` |
| `android_device.py:865-871` | `find_xpath` 吞掉查询异常且不打日志，「会话失效」与「查不到」不可区分 | `except Exception as exc` 后 `self.log.debug(...)` 再返回 `[]` |
| `action.py:276-279` | `by_direction` 用 falsy 兜底，`distance=0` 静默变 500、`direction=""` 变 `up` | 只对 `None` 取默认，非法值显式拒绝 |
| `logbus.py:107-113` | 行文本 `lower()`、关键词不 `lower()`，大小写不一致时会静默漏匹配 | 构造时统一小写（当前真相源 67 个关键词全小写，暂不触发） |
| `logfiles.py:50-56` | 每轮对已读块全量数 `\n`，O(块数²)；`chunks.insert(0, ...)` 也是 O(n) | 计数器累加 + `append` 后 `reverse()` |
| `android_device.py:225-227` | 模块中途 `from pathlib import Path`、`from utils.adb import adb_binary`，且 `_run_adb`（:113）用的是后置导入的名字 | 提到文件顶部 import 区 |
| `android_device.py:238-254` | `capture_png`（连同上方的 `_run`）全仓无调用，是死代码；它还会落盘，与 `Screenshot` 的「不落盘」口径冲突 | 删除，或明确它属于哪个在用入口 |
| `action.py:237/255/273/291/304/317/334/355` | 8 个动作类都 `self.log = device_log`，但一次都没读 | 删字段或真正使用 |
| `__init__.py:5`、`android/__init__.py:5` | `python -m engines.device` / `python -m engines.device.android` 均无法执行（无 `__main__.py`，已实测报 `No module named ...__main__`） | 补 `__main__.py` 或改成真实可跑的命令 |
| `__init__.py:19-21`、`android/__init__.py:20-21` | 「测试」段路径过期：实际是 `tests/engines/device/unit/test_android_device.py`；`test_tool_device.py`、`test_close_recent_apps.py` 已不存在 | 按实际文件更新或删除条目 |
| 全包 | 注释模板欠账：`docstrings check --path` 报 90 error / 3 warn（`doc-args=37`、`doc-returns=37`、`def-docstring=13`） | 属存量欠账，按规范 §7.1 逐步补齐，不做大扫除 |

## 五、已排除的误报 / 降级项

1. **`recent_apps.py:43` 正则不支持连字符** —— 降为不修。Android 应用 ID 必须是合法 Java 包名（字母/数字/下划线/点），连字符不合法；`com.example.my-app` 这种包名装不上，构造不出触发场景。
2. **「设备定向未实现、多条 adb 命令打到任意设备」** —— 误报。所有动作经 `AdbChannel`，`_exec` 必带 `-s <serial>`；只有主机侧 `devices` 与 `adb connect/pair` 不带 `-s`，本来就不该带。
3. **`config.ini` 缺 section 判定为 high** —— 降为「死配置」。无人读取，运行期不会触发 `MissingSectionHeaderError`，真实风险是误导后来者。
4. **「`open_device` 连接失败不抛 `EngineConnectError`」** —— 部分成立。`_run_adb` 已把 adb 失败包成 `EngineConnectError`；漏的是 `AdbUnavailableError`（平台无 adb）。而 `connection.py:42-44` 明确写了「缺 adb 要按 503 原样上报」，属有意保留。归入「文档措辞待收紧」，不进缺陷清单。

## 六、需要拍板的事（2026-11-19 更新：已按建议执行）

> 需求方回复「按照建议修改」，以下按报告建议落地：
> ① 修复范围取 **H + M + 低危可机械判定项**（未做全量 docstring 大扫除，符合规范 §7.1）；
> ③ `config.ini` 按建议删除；④ 注释只补本次改动行；⑤ `U2_OP_TIMEOUT` / `uuid` 取「补实现」。
> ② `recent_apps` 日志口径按**改代码**处理（迁 `device_log`）：依据是归档设计
> `openspec/changes/archive/2026-10-20-unified-utils-logs/design.md`「engines/device 的设备代码用
> `device_log`」，属既有规格落地，不是规则改动，因此不需要变更申请。

## 七、修复执行结果（2026-11-19）

### 7.1 代码修复

| 编号 | 落地内容 | 位置 |
| --- | --- | --- |
| H1 | 两条 `input_text` 路径统一走新增 `_quoted_input_text()`（空格转 `%s` + `shlex.quote`），注入面关闭 | `android_device.py` |
| H2 | `_masked_command()` 把 `pair` 末位参数打码；`_adb_pair` 只打地址与端口 | `android_device.py` |
| M1 | 抽象 `DeviceConnection.connect()` 改为无参，`open_device` 通用分支改为「构造传标识 → `connect()`」 | `action.py` |
| M2 | `AdbChannel._exec` 捕获超时并转 `RuntimeError`（模块级固定真实异常类，兼容 subprocess 替身） | `android_device.py` |
| M3 | `logbus.from_file` 捕获 `(OSError, ValueError)`，非 UTF-8 文件降级为空索引 | `logbus.py` |
| M4 | `open_device` 在信息/控制构造失败时先 `disconnect()` 再上抛 | `action.py` |
| M5 | 空截屏校验下沉到 `screenshot_b64()`，`Screenshot.capture` 复用它（不重复编码、不重复截图） | `action.py` |
| M6 | 新增 `_tune_u2_http_timeout()`，建会话前把 `uiautomator2.base.HTTP_TIMEOUT` 收到 20s（拿不到常量只记告警） | `android_device.py` |
| M7 | 新增 `_verify_usb()`：USB 配置 `connect()` 时用 `adb -s <uuid> get-state` 校验在线 | `android_device.py` |
| M8 | 删除无人读取、无 section、硬编码 `D:\\Govee\\...` 的 `config.ini` | 已删除 |
| M9 | `recent_apps` 过程日志改 `device_log`，模块头同步 | `recent_apps.py` |
| 低危 | `_bounds_center` 严格整数校验；`by_direction` 只对 `None` 取默认；`find_xpath` 失败留 debug 日志；`tail_lines` 改增量计数 + `append/reverse`；中途 import 归并到顶部；删除死代码 `capture_png`/`_run`；删除 8 个空挂 `self.log`；`__main__` 调试命令改成可执行模块；测试路径与「测试」段按实际文件重写 | 全包 |

### 7.2 测试与检查

- 新增 `tests/engines/device/unit/test_device_log_tools.py`（11 例）：`tail_lines` 顺序/CRLF/缺失/边界、`KeywordIndex` 大小写与坏文件降级。
- `test_android_device.py`：新增 9 例（引号 4 / 配对码脱敏 3 / bounds 严格校验 1 / u2 超时 1）；把「超时原样抛出」的旧断言改为「统一成 `RuntimeError`」。
- 结果：
  - `pytest tests/engines/device/unit tests/device/unit -m unit` → **83 passed**
  - `pytest ... -k U2Lazy` → 5 passed
  - `pytest tests/serial_log/integration/test_keyword_api.py` → 8 passed
  - `ruff check` / `ruff format --check`（`engines/device`、`tests/engines/device`）→ 全通过
  - `engines-agents-style`（`--path engines/device`）→ 0 violation
  - `engines-docstring-check`（改动口径）→ engines/device 零新增违规；整包 error 90 → 61、warn 3 → 0
- `python run.py check`：阻塞项 18/27 通过。**9 项失败全部落在本次未触碰的范围**，且失败文件在会话开始前就已是改动状态：
  - `ruff-format` / `ruff-lint`（平台范围）：backend 的 3 个待格式化文件与 3 条 import 错误
  - `ruff-engines-format` / `ruff-engines-lint`：仅 `engines/backend_bridge/agents/tool_selection.py:30`
  - `openapi-schema` / `openapi-coverage`、`prettier` / `prettier-ts` / `vue-tsc`：frontend 与契约文件
  - 对照：`engines/device` 与 `tests/engines/device` 的 ruff check / format 单点全绿

### 7.3 顺带发现的两个存量问题（未修，未越界）

1. `test_android_device.py::TestAdbInfo::test_current_app_parses_package_and_activity` 的断言写的是 `dumpsys window`，实现早已改读 `dumpsys window displays` —— 该单测在 HEAD 上就是红的，本次一并改正。
2. `tests/arch/unit/test_channels.py::TestAgentScopeChannel::test_agent_scope_no_adapters` 断言 `engines/agents/` 目录存在，而该目录已按退役单删除 —— 与设备模块无关，留给该退役单处理。

### 7.4 仍存欠账（按「不做大扫除」保留）

- `engines/device` docstring 尚有 61 条（`doc-args` 27、`doc-returns` 26、`def-docstring` 8），集中在 `action.py` 的动作类与 `connection.py`，属存量。
- `recent_apps.close_recent_apps` 目前全仓无调用方，属退役残留；是否删除需与调用链负责人确认。
- 本次修复未提交，未跑 `ci-phase1.yml`。

