## Context

现状（2026-11-27）：`adb_input_text` 在非 ASCII 时直接失败；`AdbControl.input_text` 同样拒绝非 ASCII；`AndroidControl.input_text` 对中文会静默退回 `input text`（必然无效）。平台执行者只用 `build_adb_tools()`，因此模型能看到的唯一输入工具就是受限的那个。

约束：

- `engines/ae_harness` 与 `engines/device` 在 `.linting` 里互不依赖；`utils` 是 utility 模块，两边都可引用（`android_device.py` 已引用 `utils.adb` / `utils.logs`）。
- 全仓不写注释与普通 docstring；工具函数例外（首行摘要 + `Args:`）。
- `engines/` 不新增自定义异常类，失败用内置异常。
- 仓库是 MIT；ADBKeyboard 是 GPL-2.0，不能把 APK 提交进仓库。

真机验证（RF8N21MSW7A / Android 11）：`ADB_INPUT_B64 --es msg <base64>` 可逐字输入中文，`ADB_CLEAR_TEXT` 可清空，`ime set` 后可恢复原输入法。

## Goals / Non-Goals

**Goals**

- `adb_input_text` 与设备引擎 `input_text` 支持任意 Unicode（中文、emoji、混排）。
- ASCII 输入保持现有快路径与行为不变。
- 输入法按需安装、启用并在结束后恢复；失败可读且不静默截断。
- 支持离线导入同版本安装包。

**Non-Goals**

- 不改写 u2 的元素定位/点击路径，不替换 uiautomator2。
- 不引入剪贴板兜底、不新增第二种输入工具。
- 不修改执行者提示词（DB 配置）与前端。
- 不做跨设备批量输入编排。

## Decisions

1. **用独立 ADBKeyboard，而不是 u2 内置 IME 或自研 IME。**
   - u2 的 `com.github.uiautomator/.AdbKeyboard` 是 MIT，但绑定 ATX 服务与私有广播协议；引入它等于把 u2 运行时变成输入前提。
   - 自研 IME 需要 Android 构建链，成本 2–3 天，收益仅是许可证更宽松。
   - 独立 ADBKeyboard 协议稳定、体积 18KB，已验证可用。GPL-2.0 的合规问题用“不入库、按需下载”解决。

2. **资产不入库：固定版本 + 大小 + SHA-256 + 离线导入。**
   - 复用 `utils/platform_tools.py` 的模式：缓存目录 `tools/.cache/adbkeyboard/`（已 gitignore），下载后校验大小与 SHA256，原子落盘。
   - 版本固定 `v2.4-dev`（Android 11–15）；`v2.5-dev` 是 A16 修复版，不在本次范围。
   - 离线场景用本地文件导入，仍走同一套校验。

3. **协议：base64 广播，不复用 `input text` 拼接。**
   - `am broadcast -a ADB_INPUT_B64 --es msg <base64(utf-8)>` 规避引号、空格、换行与编码问题。
   - 成功判据：输出含 `Broadcast completed: result=0`；缺失或非 0 一律失败。
   - 清空走 `ADB_CLEAR_TEXT`，不用对输入框无效的 `KEYCODE_CLEAR`。

4. **ASCII 保持 `input text` 快路径。**
   - 纯 ASCII 不切输入法，速度与旧行为一致；只有含非 ASCII 才进入 IME 通道。
   - 判定用 `str.isascii()`；混合文本整体走 IME，避免两次提交。

5. **分层：边界内各司其职，不跨层共享实现。**
   - `utils/adb_keyboard.py`：资产下载/校验/安装、设备层协议、`python -m utils.adb_keyboard install|status` CLI、`ensure_ready()`。
   - `engines/ae_harness/tools/adb/ime.py`：纯 adb 协议（`pm list` / `ime set` / `am broadcast` / 恢复），不读写文件、不 import `utils`；设备未装时抛 `AdbError` 并给出安装命令。
   - `engines/device/android/android_device.py`：`AdbControl.input_text` 调 `utils`；删除 `AndroidControl.input_text` 覆盖，让文本输入只有一条实现。
   - 任务启动：`backend/apps/task_list/task_runner.py` 在 SOP 任务开始前调用 `utils.adb_keyboard.ensure_ready(serial)`，失败只警告、不阻塞无需文本输入的任务。
   - 备选“ae_harness 共享 utils”被 `.linting` 的 `ae-harness-isolation` 合同否决；“由 backend 注入 provider”（C）被否决：全局状态、失败晚、入口多。
   - 协议在 tools 与 utils 各一份，用 `tests/arch/unit/test_adb_keyboard_parity.py` 守常量与编码一致，防漂移。

6. **清空策略分通道。**
   - IME 通道：先 `ADB_CLEAR_TEXT` 再提交。
   - ASCII 通道：保留现有 `KEYCODE_MOVE_END` + `KEYCODE_CLEAR`（此时 IME 未激活，广播清空不生效）。

7. **分片阈值 800 字符。**
   - 800 个中文约 2.4KB UTF-8、3.2KB base64，远低于 Windows 命令行与 Binder 限制；按字符切分，不拆多字节字符。

8. **失败语义：抛出内置 `RuntimeError`，由工具层转 `status=false`。**
   - 安装失败、`ime set` 超时、广播非 0 都带原始输出摘要。
   - 不退回 `input text`，避免“看似成功但只写了一半”。

9. **并发与恢复。**
   - 每个 serial 一把 `threading.Lock`，避免两个调用同时切输入法。
   - 进入前读取 `default_input_method`，`try/finally` 恢复；恢复失败只记录，不覆盖输入结果。

## Risks / Trade-offs

- **目标 App 拒绝第三方输入法（银行、游戏、自绘控件）** → 单 App e2e 覆盖；失败时明确报错，不引入剪贴板兜底掩盖问题。
- **进程崩溃导致输入法未恢复** → `finally` + 下次调用重新记录；文档给出人工恢复命令。已在一个真实设备上见过残留，属于已知运营问题。
- **ADBKeyboard 是 debug 签名** → 受 MDM 管控的设备可能拒绝安装；错误信息要提示“设备策略/未知来源”。
- **GPL-2.0** → 仓库不提交 APK，只在运行时从上游下载；文档注明来源与许可证，离线导入由用户自备文件。
- **一次性提交语义** → 输入框只触发一次 `onTextChanged`，与逐字输入不同；对联想/防抖敏感的用例需在 e2e 里显式覆盖。
- **广播成功 ≠ App 接收** → 工具只对“广播成功”负责；输入内容回读由调用方或 e2e 断言。
- **两处协议重复导致漂移** → `tests/arch/unit/test_adb_keyboard_parity.py` 守常量与编码/分片一致；改版本时两处一起改。
- **任务开始多一次 `pm list`，首次可能触发下载/安装（最长 120s）** → 仅 SOP 任务执行、安装成功后跳过；失败只告警，后续输入时再报可读错误。

## Migration Plan

1. 先落 `utils/adb_keyboard.py` 与离线校验脚本（`temps/`，按测试规范不提交），保证下载/校验/分片/解析可离线验证。
2. 再接 `ime.py`、两个调用点与任务启动预装；ASCII 路径不改；同步加常量一致性守护。
3. 真机 e2e 通过后更新文档；`python -m run check` 全绿再提交。
4. 回滚：整体 revert 本次提交即可；无数据库迁移、无接口变更。设备侧残留的输入法不影响使用，可用 `adb uninstall com.android.adbkeyboard` 清除。
