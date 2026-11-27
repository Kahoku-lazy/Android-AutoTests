# device · 设备控制引擎
> 归属模块：`engines/device` ｜ 类型：引擎模块开发说明
> 代码真相源：`engines/device/action.py`、`engines/device/connection.py`、`engines/device/android/`
> 上级约束：engines/AGENTS.md ｜ 模块索引：engines/AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../../../../engines/AGENTS.md) → **本文件**。本文件只写设备引擎领域增量；**冲突时本文件的领域规则优先**。  
> 风格与检查流程仍以上层「AI 阅读与检查流程」为准。

## 职责

Android 设备控制引擎：连接、只读信息、点击/长按/滑动/拖动/输入/应用控制等。**对外只使用 `action.py`**；Android 具体实现由 `action` 懒加载（`android/`），调用方不应直接依赖实现子包。

| 路径 | 职责 |
| --- | --- |
| `action.py` | **对外入口**：连接 / 信息 / 控制抽象与统一动作名 |
| `connection.py` | 连接辅助 |
| `logbus.py` / `logfiles.py` | 设备侧日志总线与文件 |
| `android/` | Android 实现；由 `action` 加载，非公共导入面 |

Harness 侧经 `engines/ae_harness/tools/adb/` 暴露给调用方，不由 Django View 直调底层。

## 文本输入

`input_text` 按内容分流：纯 ASCII 走 `adb shell input text`（不切输入法）；含非 ASCII 时经设备输入法提交，协议实现在 `utils/adb_keyboard.py`。

1. 设备未装 ADBKeyboard 时，首次使用按固定版本下载到 `tools/.cache/adbkeyboard/`，校验大小与 SHA-256 后安装；离线环境用 `ADB_KEYBOARD_APK` 指向本地安装包。也可 `python -m utils.adb_keyboard install --serial <serial|all>` 预装，SOP 任务开始前会自动调用 `ensure_ready()`。
2. 切换前记录 `default_input_method`，提交结束（含异常）恢复；清空走 `ADB_CLEAR_TEXT`，不依赖 `KEYCODE_CLEAR`。
3. 安装失败、广播失败、切换超时一律抛 `RuntimeError`，不退回 `input text` 造成静默截断。
4. APK 不入库：上游 ADBKeyboard 为 GPL-2.0，仓库只保留下载地址与校验值；目标 App 能否接受第三方输入法需按 App 实测。


## 红线（禁止）

1. **禁止**跳过本文件与上层流程直接改本包对外契约（尤其 `action` 动作名与语义）。
2. **对外入口**：业务与工具只经 `action`（或经 `ae_harness/tools/adb/`）；**禁止**上层 `import engines.device.android...` 绕过抽象。
3. **零 Django**：禁止 `import apps.*` / `django.*` / `backend.apps.*`。
4. **动作名统一**：三端实现 MUST NOT 自创别名；在 `action` 抽象层对齐。
5. **不写业务库**：设备池台账、锁、任务表由 backend 管理；本包不写 ORM。
6. **日志**：用 `utils.logs.device_log`（或既有设备日志约定），不把密钥写入日志。

## AI 阅读与检查流程（必读）

1. 先读 [`engines/AGENTS.md`](../../../../engines/AGENTS.md)。
2. 改设备动作语义、连接模型、对外 API 时再读**本文件**。
3. 写代码前按上层流程读 [`.agents/rules/engines-code-style.md`](../../../../.agents/rules/engines-code-style.md)。
4. 自检：`cd .agents/skills/engines-agents-style-check` → `python -m scripts.check_engines_agents_style --path engines/device`。

## 相关路径速查

| 用途 | 路径 |
|------|------|
| 上层入口 | [`engines/AGENTS.md`](../../../../engines/AGENTS.md) |
| Agent 工具封装 | `engines/ae_harness/tools/adb/` |
| 风格检查技能 | [`.agents/skills/engines-agents-style-check/`](../../../../.agents/skills/engines-agents-style-check/) |
