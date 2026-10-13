## Why

`engines/agents/**`（脚手架包）这一轮重构收尾时留下了 4 处已知缺口，都已在早前各变更单里登记为 Non-goal，本次一并关掉。

**缺口 1：规范已生效，代码还有 9 处不符。**
`standardize-raises-docstrings` 把规则写进了 `AGNETS.md` 第 1 条（"函数体内有显式 `raise` 的，docstring **必须**写 `Raises:` 段"），但当时按用户指定只改了 `role/base.py`。AST 实测（`temps/list_raises.py`）：**15 个函数有显式 `raise`，6 个有 `Raises:`，9 个没有** —— 也就是规范落地当天就有 9 处违规。

**缺口 2：`role/config.py` 的 2 处幽灵 `Raises`。**
`ModelConfig`（:38）与 `ChatModelFactory.__init__`（:100-102）都写着 `ValueError: API 密钥不是字符串或 SecretStr 类型`，但**全仓没有抛点**：`ModelConfig.__post_init__` 只做 `isinstance` 判断与 `SecretStr()` 包装，实测 `SecretStr(123)` / `SecretStr(None)` 都静默存值。更糟的是 `ChatModelFactory.__init__` 里还写着 `ValueError: 不支持的模型提供商` —— 那是 `create()` 抛的，**归属错了**（`__init__` 只赋值三行，一行都不抛），而真正会抛它的 `create()` 反而没有 `Raises:` 段（正是缺口 1 的第 2 项）。

**缺口 3：`prompt_config.py` 的两个孤儿类。**
该模块（职责按 `AGNETS.md` 第 20 行是"**配置**智能体提示词"）里却留着 `ModelConfig`（:14，可变 dataclass，`api_key: str`）与 `DeviceExecutionConfig`（:24）—— 是从平台引擎复制过来时的残留，**全仓零引用**（详证见 design.md D3）。归档单 `move-config-classes-to-role-config` 的 Non-goals 与 design D4 已明确登记："不收敛 `engines/agents/prompt_config.py` 里的第三份 `ModelConfig` 与无人引用的 `DeviceExecutionConfig`（按用户决定另立一单）"—— **本单就是那一单**。

**缺口 4：`AGNETS.md` 的 `messaging` 条目是空的。**
第 12 行只有 `3. \`messaging\`:` 后面没内容，而该目录现在承载两件事（对话稿落库、消息解析与上屏渲染）。

## What Changes

- **补齐 9 处 `Raises:` 段**（照 `AGNETS.md` 第 1 条，逐条与代码里的 `raise` 对应）：
  `agents.py` 的 `main`；`role/config.py` 的 `create`；`tools/tool_serial.py` 的 `_parse_log_at` / `read_device_log` / `check_device_log`；`tools/tool_wrapper.py` 的 `call`；`tools_config.py` 的 `select_tools` / `_assigned_tools` / `_skill_sources`。
- **清理 2 处幽灵 `Raises`**：`ModelConfig` 删掉不存在的 `ValueError`（保留真实存在的 `FrozenInstanceError`）；`ChatModelFactory.__init__` 的两条 `ValueError` 一并处理 —— 幽灵那条删掉，"不支持的模型提供商"那条**移到 `create()` 的 `Raises`**（顺带补上缺口 1 里的 `create()`）。
- **删除 `prompt_config.py` 的两个孤儿类**：`ModelConfig`、`DeviceExecutionConfig`，并同步 `__all__`（`DeviceExecutionConfig` 的字段默认值 `field(default_factory=ModelConfig)` 随之消失）。
- **补 `AGNETS.md` 的 `messaging` 条目**：写明该目录存放对话稿与消息解析。
- **Non-goals（本次不做）**：
  - 不改任何异常类型、不改任何运行时行为（除删掉无人引用的两个类）。
  - 不动 `engines/ai/**` 与平台侧的 `ModelConfig` / `DeviceExecutionConfig`（那是生产路径，与脚手架无关）。
  - 不合并 `BaseRole._require_agent` 与 `workflow/steps.py:_require_agent` 两处守卫。
  - 不给"不抛异常"的函数加 `Raises:` 声明。
  - 不动 `AGNETS.md` 的其它条目（含 :19 那处 `,。` 标点小瑕疵）。

## 关联文档

无关联需求编号。本次是脚手架包的注释补齐 + 删除零引用孤儿类，不改变对外可观察行为（删除的两个类全仓零引用，已验证），故不进入项目的 PRD / ARCH 编号体系。按 schema 约定设 `skip_specs: true`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。注释补齐不改变任何异常的类型或触发条件；删除的两个类在 `engines/ai/**`（生产路径）里另有同名的独立实现，`apps/**` 与 `tests/**` 引用的都是平台侧那一份，故不构成能力变更。以 `skip_specs: true` 退出 specs 阶段。

## Impact

- `engines/agents/**` 的 6 个 `.py`：`agents.py`、`role/config.py`、`tools/tool_serial.py`、`tools/tool_wrapper.py`、`tools_config.py`、`prompt_config.py`（均已被 git 跟踪，本次改动会形成 `git diff`）。
- `engines/agents/AGNETS.md`：补一行目录说明。
- 平台侧零改动：`engines/ai/**`、`apps/**`、`frontend/**` 不动。
- 行为风险：注释改动为零；删类需靠"全仓零引用 + 导入冒烟 + 定向测试"三证（见 design.md Risks）。
- 收尾效果：完成后 `temps/list_raises.py` 的缺口应归零，脚手架包与 `AGNETS.md` 的 Raises 规则**完全一致**。
