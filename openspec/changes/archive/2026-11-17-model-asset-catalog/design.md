## Context

现状：`engines/agents/models/` 已有清晰边界（门面唯一、包外禁 import 子模块、策略不进包），但模型连接参数被复制进 5 个角色的 `ModelConfig` 段（[agent_config.yaml](../../../engines/agents/config/data/agent_config.yaml)），能力靠手写 `vision: true`，provider 分派是字典分支（`chat_model.py`），`catalog.py` 里还留着一条指向不存在文件的 YAML 覆盖路径。

AgentScope 2.0.9 提供的构造面（`credential` / `model` / `parameters` / `stream` / `max_retries` / `context_size` / `formatter`）已经足够支撑「模型资产化」，本变更只是把这些参数从角色里搬到模型表，并补上校验。

需求见 [proposal.md](proposal.md) 与 `openspec/changes/model-asset-catalog/specs/`；模块实现细则见 `engines/agents/models/AGENTS.md`。

## Goals / Non-Goals

**Goals:**

- 连接参数只存在一处（`models.yaml`），角色只引用；两处同时写立即失败。
- 校验与加载分成两个单向阶段：校验不通过的对象不进入加载。
- 能力（图片 / 上下文长度）由声明推导，删掉手写布尔。
- 模型级参数可配，且覆盖优先级固定可预期。
- 新增 provider 只加一行注册，不改构造分支。

**Non-Goals:**

- 不做远端模型发现（不联网查厂商模型列表）。
- 不改智能体配置页（`ai-agent-config` 那套 UI 与应用层模型选择）。
- 不动重试/退避/降级策略（仍留在 `middleware/model_retry.py`）。
- 不做 provider 插件热加载或市场。
- 不改提示词体系（仍在 `role_sys_prompts.py` + `prompts/*.md`）。

## Decisions

**D1：`models.yaml` 单文件四族，不拆四个文件。**
四族条目总数约 10 条，拆开会让「一次改模型要打开 4 个文件」。备选：按族拆 4 个文件——被否，收益是文件更短，代价是跨族一致性校验要跨文件。表**平铺**（顶层键即模型短名），族由条目的 `family` 字段标注，避免"族 → 短名 → 参数"三层嵌套。

**D2：角色只写 `model` + 调用姿势；连接参数只认模型表。**
角色写 `provider` / `model_name` / `api_key` 直接报错，而不是「角色优先、模型表兜底」。备选：允许角色覆盖——被否，因为那会重新制造两处真相，而这正是本变更要消除的。

**D3：能力由 `input_types` 推导，`vision` 降为只读兼容别名。**
读到 `vision: true` 时转换成 `input_types` 并告警；写盘新配置不再出现该字段。备选：直接删字段——被否，会让历史配置在升级当天全部失败。

**D4：覆盖优先级「框架默认 < 模型表 < 角色 < 调用点」，但连接参数不可覆盖。**
`provider` / `model_name` / `api_key_env` 只认模型表。备选：全字段可覆盖——被否，调用点覆盖模型名会让缓存键与计费口径失去意义。

**D5：校验时机 = 懒校验 + 显式校验命令。**
首次取模型时校验该条目；另提供 `validate_models()` 供门禁/启动检查调用。不在包导入时校验——测试与 CLI 会因此产生副作用。备选：进程启动即全量校验——被否，`engines` 被多个入口导入，导入期副作用难控。

**D6：缓存键 = `(模型短名, 覆盖指纹, 事件循环)`。**
替代现有的「连接参数六元组」。覆盖指纹只包含会改变客户端行为的项（`stream` / `temperature` 等），不包含展示类字段。备选：沿用连接参数指纹——被否，模型表化后连接参数在实例构造时已固定，重复计算无收益。

**D7：交卷关思考从 patch `_call_api` 收敛为 models 包内的装饰器。**
行为等价，但不再在工厂里直接改私有方法；装饰器挂在装配管线上，只挂一次（幂等标记保留）。备选：改走框架 middleware——待评估，因为中间件是 Agent 层钩子，拿不到 `tool_choice` 的强制交卷时机。

**D8：一次性切换门面签名，不保留双入口。**
`get_chat_model(role_key)` 改为 `get_chat_model(model_name)`，调用点只有 5 处（装配层 + 测试）。备选：兼容期同时接受角色键与模型名——被否，字符串无法可靠区分，且会长期留下两条代码路径。

**D9：备用模型继承主模型的能力与调用姿势，只覆盖连接差异。**
备用模型可换 provider，但 `input_types` / `formatter` / `context_size` 默认继承主模型；显式给值才覆盖。

**D10：跨层约束（`tool_result_limit` 与 `context_size`）先只告警，不阻断。**
装配期若 `tool_result_limit ≥ context_size × trigger_ratio`，记录一条明确告警。备选：校验期直接失败——被否，两个字段分属角色与模型两层，强绑定会让调参变脆。

## 模块防火墙自检

- 跨 App import：无。本变更只在 `engines/agents/models`、`engines/agents/config`、`engines/agents/agent_builders.py` 内改动，不触碰 `apps.*` / `django.*`。
- 数据落点：模型数据在 `engines/agents/config/data/models.yaml`，`engines/agents/models/` 内无 `.yaml`。
- 写库：无。本变更不产生任何数据库读写。
- 依赖方向：`models` 不 import `middleware` / `agent_builders` / `role_sys_prompts`，保持现有单向依赖。

## Risks / Trade-offs

- [迁移遗漏：5 处调用点 + 4 个测试断言] → 一次性全局搜索 `get_chat_model(` / `get_fallback_chat_model(`，并把测试断言改为按模型短名。
- [兼容别名 `vision` 与 `input_types` 冲突] → 冲突即校验失败，报错指出两处声明；不自动取舍。
- [`context_size` 不填仍吃框架默认（DeepSeek 65536），与 `tool_result_limit: 400000` 冲突] → 校验期给默认值提示，装配期对越界组合告警（D10）。
- [缓存键变化导致首轮重复建模] → 缓存键只含短名与覆盖指纹，构造次数与现状持平；跨循环仍不复用。
- [角色键误传为模型名] → 未知名报错并列出可用短名，报错信息直接指向模型表。
- [YAML 校验误报阻断启动] → 仅首次取用时校验该条目，未用到的条目不会阻塞；显式命令供门禁使用。

## Migration Plan

1. 新增 `models.yaml`（内容来自现有 5 段 `ModelConfig` 与 `catalog` 内置表）。
2. 角色段改为 `model:` 引用，保留 `stream` 等调用姿势。
3. 加载器切换：先支持新引用，旧的连接参数写法在过渡期解析并告警；同时写两者直接失败。
4. 门面切签名，更新 5 处调用点与测试。
5. 删除内置目录、`config.yaml` 覆盖死路径、兼容代理与 `model_supports_image`。
6. 回滚：保留 `models.yaml` 与旧 `ModelConfig` 段的解析分支一个版本；回滚即恢复角色段并切回旧门面签名。

## Open Questions

- `models.yaml` 是否需要按环境（测试/生产）区分密钥变量前缀？当前结论：不需要，靠部署环境的环境变量名区分。
- `formatter` 是否需要 `auto` 值（按角色数自动选多实体）？当前结论：不需要，显式 `chat` / `multi_agent`。
