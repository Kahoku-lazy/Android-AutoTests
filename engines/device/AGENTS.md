# device 模块 AGENTS.md

> 层级：根 `AGENTS.md` → [`engines/AGENTS.md`](../AGENTS.md) → **本文件**。本文件只写设备引擎领域增量；**冲突时本文件的领域规则优先**。  
> 风格与检查流程仍以上层「AI 阅读与检查流程」为准。

## 职责

Android 设备控制引擎：连接、只读信息、点击/长按/滑动/拖动/输入/应用控制等。**对外只使用 `action.py`**；Android 具体实现由 `action` 懒加载（`android/`），调用方不应直接依赖实现子包。

| 路径 | 职责 |
| --- | --- |
| `action.py` | **对外入口**：连接 / 信息 / 控制抽象与统一动作名 |
| `connection.py` | 连接辅助 |
| `logbus.py` / `logfiles.py` | 设备侧日志总线与文件 |
| `android/` | Android 实现；由 `action` 加载，非公共导入面 |

Harness 侧经 `engines/agents/tools/tool_device.py` 暴露给角色，不由 Django View 直调底层。

## 红线（禁止）

1. **禁止**跳过本文件与上层流程直接改本包对外契约（尤其 `action` 动作名与语义）。
2. **对外入口**：业务与工具只经 `action`（或经 agents 的 `tool_device`）；**禁止**上层 `import engines.device.android...` 绕过抽象。
3. **零 Django**：禁止 `import apps.*` / `django.*` / `backend.apps.*`。
4. **动作名统一**：三端实现 MUST NOT 自创别名；在 `action` 抽象层对齐。
5. **不写业务库**：设备池台账、锁、任务表由 backend 管理；本包不写 ORM。
6. **日志**：用 `utils.logs.device_log`（或既有设备日志约定），不把密钥写入日志。

## AI 阅读与检查流程（必读）

1. 先读 [`engines/AGENTS.md`](../AGENTS.md)。
2. 改设备动作语义、连接模型、对外 API 时再读**本文件**。
3. 写代码前按上层流程读 [`.agents/rules/engines-code-style.md`](../../.agents/rules/engines-code-style.md)。
4. 自检：`cd .agents/skills/engines-agents-style-check` → `python -m scripts.check_engines_agents_style --path engines/device`。

## 相关路径速查

| 用途 | 路径 |
|------|------|
| 上层入口 | [`engines/AGENTS.md`](../AGENTS.md) |
| Agent 工具封装 | `engines/agents/tools/tool_device.py` |
| 风格检查技能 | [`.agents/skills/engines-agents-style-check/`](../../.agents/skills/engines-agents-style-check/) |