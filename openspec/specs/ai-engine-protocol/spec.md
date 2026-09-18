# ai-engine-protocol Specification

## Purpose
定义 Django 与可替换 AI 引擎之间的进程内协议：Django 仅传入任务表单、三角色模型配置与工具清单，引擎完成「规划 → 执行 → 验收」并返回归一化结果；换框架只换引擎实现，Django 逻辑不变。

## Requirements

### Requirement: AiEngine 协议接口
AI 引擎 SHALL 暴露阻塞接口 `run(TaskRequest) -> TaskResult`；Django 经 `get_ai_engine(settings.AI_ENGINE)` 工厂获取引擎，引擎内部负责框架的异步装配与执行，Django 不感知框架内部实现。

#### Scenario: 调用引擎
- **WHEN** Django 调用 `get_ai_engine("agentscope").run(req)`
- **THEN** 引擎在进程内完成执行并返回 `TaskResult`，Django 无任何 `agent_scope`/`asyncio.run`/`AgentScope` 直接引用

### Requirement: TaskRequest 契约
Django SHALL 通过 `TaskRequest` 传入规划用户输入（字段名仍为 `goal`）、三角色模型配置（planner/executor/verifier，api_key 已解密）、工具清单（`tools`）、`max_loops` 及 `device_serial`/`user_id`/`task_id`/`media_root`/`skill_dirs`。规划用户输入 MUST 为无 Markdown 代码块包裹的 JSON 字符串，键固定为：`任务标题`、`任务目标`、`附件文本内容`、`设备ID`；值为字符串，无附件时 `附件文本内容` 为空字符串，`设备ID` 为已解析的设备 serial。

#### Scenario: 组装请求
- **WHEN** 前端提交任务（`POST /api/ai/tasks/submit`）且任务已落库
- **THEN** `engine_adapter` 从 `AITask` 与 `route_configs`（解密后）组装 `TaskRequest`，模型 api_key 以明文传入引擎，且 `TaskRequest.goal` 为上述四键 JSON

#### Scenario: 规划模型收到结构化任务 JSON
- **WHEN** 引擎启动规划阶段
- **THEN** 规划模型收到的用户输入包含任务标题、任务目标、附件 Markdown（可空）与设备 serial，而不是仅有目标一句自然语言

### Requirement: TaskResult 归一化
引擎 SHALL 返回 `TaskResult`（`status`/`summary`/`completed`/`failed`/`log`/`usage`/`reason`）；两条线路（device_control / platform_task）结果同构，`summary` 落 `AITask.result`。

#### Scenario: 结果落库
- **WHEN** 引擎返回 `TaskResult`
- **THEN** Django 按 `status` 写 `AITask` 状态，`summary` 写 `result`（device_control 不再恒空）

### Requirement: 引擎零 apps 依赖
`ai_engines` SHALL 不 import `apps.*` 内部实现；业务工具经 `TaskRequest.tools` 注入，引擎只负责包装与调用。`ai_engines` 是唯一可触碰第三方 AI 框架的层。

#### Scenario: 工具注入
- **WHEN** 引擎需要平台工具
- **THEN** 工具函数由 Django 层注入（`TaskRequest.tools`），引擎不直接 import `apps` 业务模块

### Requirement: 引擎注册与 fail-fast
`get_ai_engine` SHALL 按 `AI_ENGINE_REGISTRY` 惰性加载引擎并进程内缓存；未注册名 / 不可导入 / 构建失败 SHALL 抛 `ConfigurationError`，不做静默回退。

#### Scenario: 未注册引擎
- **WHEN** `settings.AI_ENGINE` 为未注册名
- **THEN** `get_ai_engine` 抛 `ConfigurationError`（fail-fast）

### Requirement: 装配期配置 fail-fast
Django 侧组装任务时 SHALL 校验配置完整性：`device_control` 线路必须存在，planner / executor / verifier 三角色各自的模型名与可解密密钥必须非空，设备串必须可用。任一项缺失或非法时 SHALL 在装配阶段抛出可读错误并使任务以失败终态结束，MUST NOT 以空模型名 / 空密钥 / 空设备串继续进入工作流。

#### Scenario: 三角色配置缺失
- **WHEN** 智能体配置中缺少 planner / executor / verifier 中任意一个角色
- **THEN** 任务在装配阶段即以明确错误失败，错误文案指明缺失的角色，不进入工作流

#### Scenario: 模型名或密钥为空
- **WHEN** 某角色的模型名为空，或密钥解密后为空
- **THEN** 装配阶段报错并指明角色与字段，任务落 failed

#### Scenario: 无可用设备
- **WHEN** 任务未指定设备串且当前没有在线设备
- **THEN** 装配阶段报错说明无可用设备，MUST NOT 以空设备串启动工作流

### Requirement: provider 配置单一真相源
系统 SHALL 保证「provider → base_url」映射只有一份真相源，且 provider 合法性只由该集合判定。装配阶段收到集合外的 provider SHALL 报错并列出合法集合；引擎侧创建模型连接时对无法处理的 provider SHALL 同样报错，MUST NOT 静默降级为某个兼容实现。装配阶段解析出的 base_url SHALL 生效于模型连接，MUST NOT 被静默丢弃。

#### Scenario: 未知 provider 在装配阶段被拒
- **WHEN** 智能体配置中某角色的 provider 不在合法集合内
- **THEN** 装配阶段报错，错误文案包含该 provider 名与合法集合

#### Scenario: 自定义 base_url 必须生效
- **WHEN** provider 在合法集合内且配置了自定义 base_url
- **THEN** 该 base_url 生效于模型连接；若该 provider 链路不支持自定义地址，则显式报错，不得解析后丢弃

#### Scenario: 兜底分支不再吸收未知 provider
- **WHEN** 引擎收到合法集合之外、且不在 OpenAI 兼容白名单内的 provider
- **THEN** 抛出 ConfigurationError，MUST NOT 按 OpenAI 兼容发起模型请求

#### Scenario: 两侧 provider 集合一致
- **WHEN** 运行一致性测试
- **THEN** 引擎侧可处理的 provider 集合与 Django 侧合法 provider 集合完全相等

### Requirement: TaskRequest 携带三角色系统提示词
Django SHALL 通过 `TaskRequest` 传入规划 / 执行 / 验收三份系统提示词（Markdown 源码字符串）。引擎装配 Agent 时 MUST 使用请求中的对应提示词作为该角色 `system_prompt`。引擎内置提示词常量 MUST 为空字符串，MUST NOT 在运行时作为回退填入 Agent。

#### Scenario: 注入库中提示词
- **WHEN** Django 组装 `TaskRequest` 且平台智能体三份提示词均非空
- **THEN** 引擎三个角色的系统提示词分别等于库中对应正文

#### Scenario: 引擎常量不再回退
- **WHEN** 请求已携带系统提示词
- **THEN** 引擎不得用内置常量覆盖或补全请求中的提示词

### Requirement: 系统提示词装配 fail-fast
Django 侧组装任务时 SHALL 校验规划 / 执行 / 验收三份系统提示词去空白后均非空。任一份缺失或为空时 SHALL 在装配阶段抛出可读错误（指明角色），任务以失败终态结束，MUST NOT 以空系统提示词进入工作流。

#### Scenario: 某角色提示词为空
- **WHEN** 平台智能体某角色系统提示词去空白后为空
- **THEN** 任务在装配阶段失败，错误文案指明该角色，不进入工作流
