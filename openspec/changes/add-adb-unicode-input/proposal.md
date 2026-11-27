## Why

平台执行者通过 `adb_input_text` 向设备输入文本，但该工具在非 ASCII 时直接返回失败；设备层 `AdbControl.input_text` 同样拒绝非 ASCII。结果是：用例里只要出现中文（搜索、备注、名称）就无法执行，模型只能改用点击/粘贴等不稳定绕法。

根因不是 adb 不能打中文，而是 `adb shell input text` 本身只接受 ASCII；Android 侧的正解是切到一个支持广播提交文本的输入法。2026-11-27 已在 `RF8N21MSW7A`（SM-G9730 / Android 11）实测通过：安装独立 ADBKeyboard、`ime set` 后用 `am broadcast -a ADB_INPUT_B64` 输入「中文验证ABC123」，`uiautomator dump` 读回逐字一致，恢复原输入法后设备无残留。

## What Changes

- 新增 `utils/adb_keyboard.py`：固定版本 `v2.4-dev`（URL、大小、SHA256），首次使用下载到 `tools/.cache/adbkeyboard/` 并校验；支持离线文件导入；`install_on(serial)` 幂等安装。**APK 不入库**（GPL-2.0 合规选择）。
- 新增 `engines/ae_harness/tools/adb/ime.py`：IME 生命周期（检测/安装/启用/切换/恢复）与 Unicode 文本提交（base64 广播、分片、清空）。
- `adb_input_text`：ASCII 保持现有 `input text` 快路径；非 ASCII 走 IME 广播；失败返回可读原因，**不再静默降级**。
- `engines/device/android/android_device.py`：`AdbControl.input_text` 支持 Unicode；`AndroidControl.input_text` 去掉「中文静默退回 `input text`」的兜底。
- 文档补「中文输入的前提、代价与恢复」。

**不破坏现有契约**：工具名、入参、JSON 返回形状、ASCII 输入行为、依赖方向均不变；不新增自定义异常类。

## 关联文档

无 PRD 条目：设备文本输入能力补齐，需求来自 2026-11-27 的人工真机验证与 B1 方案决策。

## Capabilities

### New Capabilities

- `device-text-input`: 设备文本输入的对外行为——ASCII 快路径、Unicode 经 IME 广播、输入法安装与恢复、清空与分片、失败语义。

### Modified Capabilities

（无 —— `engine-protocol` 只要求存在 `input_text` 原语，未限定字符集；`ai-device-action` 的工具名/入参/返回形状不变，无需改其需求）

## Impact

- **代码**：`utils/adb_keyboard.py`（新）、`engines/ae_harness/tools/adb/ime.py`（新）、`engines/ae_harness/tools/adb/tools.py`、`engines/device/android/android_device.py`
- **测试**：新增 `tests/` 下的纯函数用例与一条 `e2e` 真机用例
- **文档**：`.agents/docs/engines/device/device_control_engine.md`、`.agents/docs/engines/ae_harness_tools/ae_harness_tools_domain_tools.md`
- **外部依赖**：设备侧安装 ADBKeyboard（GPL-2.0，按需下载，不入库）
- **生产接口 / 数据库 / 前端**：0 变更
