## Context

见 proposal.md 的 Why。当前 `build_toolkit` 只把工具和技能放进 AgentScope 2.0.9 的常驻组 `basic`，因此不会注册组开关。`ExecutorRole` 构造时还会把同一技能目录再登记到 `basic`。组的激活状态记在智能体状态上，初始为空，所以非常驻组默认关闭。工具函数、权限放行和截图回图保持现有包装，不随分组改写。

## Goals / Non-Goals

**Goals:**

- 按 `specs/executor-tool-groups/spec.md` 与 `specs/agent-role-skills/spec.md` 组装可开关组，并让每次执行角色拿到自己的工具包。
- 技能登记可以指定目标组；执行角色只把技能放进 `platform_business`。

**Non-Goals:**

- 不改 `engines/ai` 的旧工具装配，不改规划角色和验收角色。
- 不改设备工具函数的入参、返回和权限规则。
- 不改写 `platform-tools-manual` 的正文；本变更只决定它何时出现在模型输入里。
- 不接 MCP。`engines/agents/mcp_config/mcp_config.py` 保持现状。

## Decisions

### 1. 用框架工具组，而不是自己在调用前过滤 schema

可开关组用 `ToolGroup` 交给 `Toolkit(tool_groups=...)`。存在非 `basic` 组时，框架自动注册 `reset_tools`，激活集合记在智能体的 `activated_groups` 上，未激活工具和技能不会进入模型输入。

备选是在每次模型调用前自行删掉 schema。那样要重做「最终状态覆盖」、未激活调用报错和技能说明拼接，和框架已有行为重复。

### 2. 组标识用英文，中文组名写在说明里

| 标识 | 中文组名 | 成员 |
|---|---|---|
| `basic` | 常驻组 | `screenshot_page`、`press_key` |
| `gesture` | 点击滑动 | `click_ratio`、`tap_screen`、`swipe_screen`、`drag_ratio` |
| `xpath` | xpath | `xpath_action` |
| `text_input` | 输入 | `input_text` |
| `app` | 启停应用 | `app_control` |
| `platform_business` | 平台业务工具 | 技能目录 `engines/agents/skills/executor` |

`reset_tools` 的参数名就是组标识，说明字段使用中文组名，让模型知道这组做什么。`drag_ratio` 归入点击滑动，因为它和点击、滑动一样是看图后的手势，不属于 xpath、输入或启停应用。

备选是用中文做参数名。参数名会进 JSON schema，后续改文案会连带改调用契约，所以中文只放说明和使用指引。

### 3. 配置表驱动组装，每次角色新建一份工具包

`tools_config` 保留「改表即改暴露范围」：常驻工具名、可开关组（标识、中文说明、使用指引、工具名、技能目录）分开列出。组装时校验未知工具名和跨组重复。`build_toolkit` 增加可开关组参数；顶层 `tools` 只接收常驻工具。技能目录只放进对应组，不再作为顶层 `skills_or_loaders` 进入 `basic`。

`build_executor_toolkit()` 每次返回新的工具包。`ExecutorRole` 和 `engines/agents/agents.py` 里的执行角色改为调用它，不再共用模块级的一份可变工具包。

### 4. 技能登记按组去重，执行角色指定 `platform_business`

`register_skills` 增加目标组参数。不传时仍登记到 `basic`，现有「未指定组」的行为不变。传入组名时只追加到该组；组不存在则报错并带上组名。同一目录已经出现在工具包任一组时跳过，保证只有一份来源。

执行角色在 `start()` 之前调用 `register_skills`，目标组为 `platform_business`。工具包若已在该组挂上同一目录，第二次构造不会再追加。

### 5. 使用指引写短句，开关语义写进执行提示词

每个可开关组带一段 `instructions`，只在该组被本次开关打开时出现在 `reset_tools` 的返回里：

- `gesture`：看图后的点击、长按、滑动、拖动；有相对位置时用归一化坐标。
- `xpath`：已有 xpath 时检查、读取、点击或长按。
- `text_input`：向当前输入框输入，默认先清空。
- `app`：启动或停止前确认包名。
- `platform_business`：先读取技能全文，再按全文选择工具；技能本身不能当工具调用。

`EXECUTOR_PROMPT` 增加一小节：用某组工具或技能前先打开该组；一次 `reset_tools` 表示全部可开关组的最终状态，没写为打开的组会被关掉；截图和返回键不用打开。

## 模块防火墙自检

- 不新增跨 App import，不写数据库，不改 `api.py`。
- 不改前端，不新增 HTTP 或 WebSocket。
- 改动停在 `engines/agents` 与对应单元测试。设备动作仍走现有 `engines.device.action`。

## Risks / Trade-offs

- [模型忘记先打开组，动作调用得到未激活错误] → 执行提示词写明先打开；框架对未激活工具返回需先调用组开关的错误，模型可以在同一轮补一次开关。
- [一次开关覆盖全部组，模型只打开新组时旧组被关掉] → 提示词写明这是最终状态；开关结果列出当前仍打开的组。
- [多个执行角色共用一份工具包时，后登记的技能会改到别人的包] → 每次构造角色都新建工具包。
- [首轮多一次组开关，短任务多一轮工具调用] → 接受。截图和返回键留在常驻组，看图和返回不必先开关。

## Migration Plan

无数据迁移，无接口迁移。发布就是换执行角色的工具包组装。回滚时恢复「全部工具和技能进入常驻组」的组装，并去掉提示词里的组开关小节。已在跑的智能体按创建时的工具包继续，不热更新。
