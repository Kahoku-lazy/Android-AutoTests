## Context

见 `proposal.md` - Why。AST 实测盘点（`temps/list_raises.py`，扫描 `engines/agents/**`，排除 `skills/` 供应商脚手架）：

**缺 `Raises:` 段（9 个，全部有显式 `raise`）**

| 位置 | 函数 | 抛出 | 触发条件（照代码写） |
|---|---|---|---|
| `agents.py:167` | `main` | `SystemExit` | 未设置 `DEEPSEEK_API_KEY` 环境变量 |
| `role/config.py:155` | `create` | `ValueError` | provider 不在 `deepseek` / `openai` / `dashscope` 名单内（报错会列出可选厂商） |
| `tools/tool_serial.py:46` | `_parse_log_at` | `ValueError` | 时间点不匹配四种支持格式 |
| `tools/tool_serial.py:119` | `read_device_log` | `ValueError` | 无可用日志来源（平台未开日志采集）或日志为空 |
| `tools/tool_serial.py:240` | `check_device_log` | `ValueError` | 同上 |
| `tools/tool_wrapper.py:75` | `call` | `DeveloperOrientedException` | 工具返回 `LOG_EMPTY`（日志为空）时转成开发者可见异常 |
| `tools_config.py:34` | `select_tools` | `ValueError` | 名字表里有未登记的工具（报错会列出可选名） |
| `tools_config.py:58` | `_assigned_tools` | `ValueError` | 同一工具同时列入 `basic` 与某个可开关组 |
| `tools_config.py:228` | `_skill_sources` | `TypeError` | skill 来源既不是目录路径，也不是 `Skill` / `SkillLoaderBase` |

**已有 `Raises:`（6 个，对照）**：`agents.py:41 load_sop_cases`、`agents.py:100 _case_mappings`、`role/base.py:130 _require_agent`、`tools_config.py:207 _tool_group`、`workflow/steps.py:195 _require_agent`、`workflow/steps.py:47 build`。

**幽灵 `Raises`（2 处，均在 `role/config.py`）**：`ModelConfig`（:38）与 `ChatModelFactory.__init__`（:100-102）各写着 `ValueError: API 密钥不是字符串或 SecretStr 类型` —— 无抛点（`__post_init__` 只做 `isinstance` + `SecretStr()` 包装）；`__init__` 还写着"不支持的模型提供商"，而它由 `create()` 抛。

## Goals / Non-Goals

- Goals：把 `AGNETS.md` 的 Raises 规则在代码侧补齐到**零缺口**；清掉 2 处幽灵条目并修正 `create()` 的归属；删掉 `prompt_config.py` 的 2 个零引用孤儿类；补 `AGNETS.md` 的空目录条目。
- Non-Goals：见 proposal 的 Non-goals（不改异常类型与行为、不动平台侧、不合并守卫、不加"不抛"声明、不动其它规范条目）。

## Decisions

**D1：9 处一次补齐，依据是已生效的规范而非临时口径。**
`AGNETS.md` 第 1 条已规定"函数体内有显式 `raise` 的，其 docstring **必须**写 `Raises:` 段，并逐条写明异常类型与触发条件（与代码里的 `raise` 一一对应）"。本次就是把这条规则落到代码；每处的触发条件**照抄代码里的判断与报错文案**，不发明。

**D2：`role/config.py` 用一次编辑同时解决"幽灵条目"与"`create()` 缺段"。**
`ChatModelFactory.__init__`（:91-107）只有三行赋值，**一行都不抛**，所以它的 `Raises:` 段整段都该消失：
- `ValueError: 不支持的模型提供商` → **移**到 `create()`（:155-165，代码里 `if builder is None: raise ValueError(f"不支持的模型提供商: ...；可选：...")`）—— 归属修正，同时补齐 D1 的第 2 项；
- `ValueError: API 密钥不是字符串或 SecretStr 类型` → **删**（实测无抛点）。
`ModelConfig` 同理：删那条 `ValueError`，**保留** `FrozenInstanceError: 模型配置不可变。`（frozen dataclass 的真实行为，只是由装饰器隐式抛出，不被 AST 扫描计入）。

**D3：删 `prompt_config.py` 的两个类 —— 以"全仓零引用"为证。**
检索结论（repo-wide `ModelConfig|DeviceExecutionConfig`，共 54 处命中，逐条归类）：
- `prompt_config.py` 里的 `ModelConfig` / `DeviceExecutionConfig` **只被自己引用**（`:27-29` 的 `field(default_factory=ModelConfig)` 与 `:74/:76` 的 `__all__`）；
- 所有 `from ...prompt_config import ...` 只取**提示词**：`role/executor.py:5`（`EXECUTOR_PROMPT`）、`tests/graybox/unit/test_executor_tool_groups.py:14`（`EXECUTOR_PROMPT`）、`prompts/__init__.py:1`（注释性说明）；
- 平台侧的 `ModelConfig` / `DeviceExecutionConfig` **全部来自 `engines.ai.agents` / `engines.ai.agents.config`**（`apps/ai_assistant/model_assembly.py`、`apps/ai_assistant/management/commands/ui_pipeline.py`、`engines/ai/engine.py`、`engines/ai/workflow/workflow.py`、`tests/engines/test_executor_steps.py`、`tests/graybox/unit/test_ai_*.py`）—— 与脚手架这份无关，不受影响；
- 脚手架自己的模型配置真相源是 `role/config.py:ModelConfig`（`agents.py:19` 与 `role/base.py:19` 都从这里取）。
另有两处旁证：`AGNETS.md:20` 规定该模块职责是"配置智能体提示词"（放配置类属越界）；归档单 `move-config-classes-to-role-config` 的 Non-goals / design D4 已登记"按用户决定另立一单"。
**决策：删两个类并同步 `__all__`**（而不是把它们"改成从 `role/config.py` 再导出"）—— 因为脚手架的三角色合体配置已被"每角色一份 `RoleSpecConfig`"取代，留着再导出只会制造第二个入口。

**D4：`AGNETS.md` 的 `messaging` 条目补说明。**
依据该目录现有两个模块的职责：`dialogue.py` 落对话稿、`messages.py` 做消息与工具输出解析、用量费用计算与上屏渲染。写成一句与该文件其它条目同长度的话。

**D5：异常类型一个都不改、不新增。**
沿用 `standardize-raises-docstrings` 的 D2：只用内置或框架既有类型。

**D6：以 `skip_specs: true` 退出 specs 阶段。**
注释补齐与删除零引用内部类，均无对外行为变化。

## Risks / Trade-offs

- [删类可能删到隐藏引用（动态导入、字符串引用）] → 三证：①repo-wide 检索（含 `apps/` `tests/`）已做，只剩自身；②改后跑 `python -c "import engines.agents.prompt_config as m; print(m.__all__)"` 导入冒烟；③跑定向测试（`test_executor_tool_groups.py` 等使用脚手架提示词/工具的用例）。
- [`Raises:` 内容与代码不符] → 要求逐条照抄代码里的判断与报错文案；完成后用 AST 脚本断言"缺口为 0"且"docstring 列出的类型覆盖代码里 `raise` 的类型"。
- [只改注释却误改代码] → 校验脚本断言 9 处 `raise` 节点的异常类型与位置逐字未变（除 `create()` 只加 docstring）。
- [规范与代码再次漂移] → 本单以"缺口归零"为验收口径，脚本可复用。
- [动 `__all__` 影响 `import *`] → 全仓检索无 `from engines.agents.prompt_config import *`。

## Migration Plan

无部署动作、无迁移。改动落在 docstring、删除两个零引用类、补一行规范。回退：`git checkout -- engines/agents/prompt_config.py` 等方式直接还原。

## Open Questions

- 是否给"不抛异常"的公开函数也加声明 —— 不做（噪音大于收益）。
- `AGNETS.md:19` 的 `,。` 标点瑕疵是否顺手修 —— 建议**顺手修**（同一文件同一节，1 个字符），但不作为验收项。
