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

Django SHALL 通过 `TaskRequest` 传入规划用户输入（字段名仍为 `goal`）、三角色模型配置（planner/executor/verifier，api_key 已解密）、工具清单（`tools`）、`max_loops`、`device_serial`/`user_id`/`task_id`/`media_root`/`skill_dirs`，以及设备日志证据提供者（`log_evidence`，可空）。规划用户输入 MUST 为无 Markdown 代码块包裹的 JSON 字符串，键固定为：`任务标题`、`任务目标`、`附件文本内容`、`设备ID`；值为字符串，无附件时 `附件文本内容` 为空字符串，`设备ID` 为已解析的设备 serial。日志证据提供者 MUST 以只含标准库类型的协议对象（开窗 / 读窗两个方法）注入，与 `on_progress` 同构；引擎 MUST NOT 为此直接 import `engines.device` 或 `apps.*`。

#### Scenario: 组装请求

- **WHEN** 前端提交任务（`POST /api/tasks/submit`）且任务已落库
- **THEN** `engine_adapter` 从 `task_list.Task` 与 `route_configs`（解密后）组装 `TaskRequest`，模型 api_key 以明文传入引擎，且 `TaskRequest.goal` 为上述四键 JSON

#### Scenario: 规划模型收到结构化任务 JSON

- **WHEN** 引擎启动规划阶段
- **THEN** 规划模型收到的用户输入包含任务标题、任务目标、附件 Markdown（可空）与设备 serial，而不是仅有目标一句自然语言

#### Scenario: 注入日志证据提供者

- **WHEN** 组装 device_control 任务的 `TaskRequest`
- **THEN** `log_evidence` 由 Django 侧注入并实现开窗与读窗两个协议方法，引擎只经协议调用，不直接触碰串口或 TCP 句柄

#### Scenario: 未注入日志证据提供者

- **WHEN** 未配置设备日志采集，`log_evidence` 为空
- **THEN** 引擎仍能完成执行，验收阶段标注「无日志证据」，MUST NOT 因缺少日志证据而中断任务

### Requirement: TaskResult 归一化
引擎 SHALL 返回 `TaskResult`（`status`/`summary`/`completed`/`failed`/`log`/`usage`/`reason`）；两条线路（device_control / platform_task）结果同构，`summary` 落 `task_list.Task.result`。

#### Scenario: 结果落库
- **WHEN** 引擎返回 `TaskResult`
- **THEN** Django 按 `status` 写 `task_list.Task` 状态，`summary` 写 `result`（device_control 不再恒空）

### Requirement: 引擎零 apps 依赖
`ai_engines` SHALL 不 import `apps.*` 内部实现；数据类业务工具经 `TaskRequest.tools` 注入，引擎只负责包装与调用；设备动作类工具 SHALL 由引擎自带（设备工具 + 登记清单），不再经注入，装配时 MUST 跳过注入清单里的同名设备动作工具。`ai_engines` 是唯一可触碰第三方 AI 框架的层。引擎 MUST NOT 直接引用具体设备实现（只能经设备引擎协议），也 MUST NOT 因设备动作而获得对设备池台账与设备日志的直接访问。

#### Scenario: 工具注入
- **WHEN** 引擎需要平台数据类工具（如页面流文档）
- **THEN** 工具函数由 Django 层注入（`TaskRequest.tools`），引擎不直接 import `apps` 业务模块

#### Scenario: 设备动作不经注入
- **WHEN** 引擎装配设备动作工具
- **THEN** 它使用引擎自带的设备工具，注入清单里的同名设备动作工具被跳过，模型可见的设备动作只有一份

#### Scenario: 引擎不碰设备实现与台账
- **WHEN** 引擎执行设备动作
- **THEN** 它只经设备引擎协议（协议实现或替身）取设备句柄，不 import 具体设备实现、不读写设备池台账、不直接访问设备日志

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
系统 SHALL 保证「provider → base_url」映射只有一份真相源，且 provider 合法性只由该集合判定。平台支持的 provider 集合 SHALL 恰为 DeepSeek 与阿里百炼（DashScope）两项。装配阶段收到集合外的 provider SHALL 报错并列出合法集合；引擎侧创建模型连接时对无法处理的 provider SHALL 同样报错，MUST NOT 静默降级为任何兼容实现。装配阶段解析出的 base_url SHALL 生效于模型连接，MUST NOT 被静默丢弃。

#### Scenario: 未知 provider 在装配阶段被拒
- **WHEN** 智能体配置中某角色的 provider 不在合法集合内
- **THEN** 装配阶段报错，错误文案包含该 provider 名与合法集合

#### Scenario: 自定义 base_url 必须生效
- **WHEN** provider 在合法集合内且配置了自定义 base_url
- **THEN** 该 base_url 生效于模型连接；若该 provider 链路不支持自定义地址，则显式报错，不得解析后丢弃

#### Scenario: 兜底分支不再吸收未知 provider
- **WHEN** 引擎收到合法集合之外的 provider（含已移除的 `openai` / `anthropic` / `gemini` / `custom`）
- **THEN** 抛出 `ConfigurationError`，MUST NOT 以任何兼容实现（含 OpenAI 兼容分支）发起模型请求

#### Scenario: 两侧 provider 集合一致
- **WHEN** 运行一致性测试
- **THEN** 引擎侧可处理的 provider 集合与 Django 侧合法 provider 集合完全相等，且恰为 `{deepseek, dashscope}`

### Requirement: 系统提示词随引擎走
规划 / 执行 / 验收三份系统提示词 MUST 由引擎侧的提示词常量（`engines/ai/agents/config.py`）提供，MUST NOT 经 `TaskRequest` 由 Django 注入，MUST NOT 从数据库读取。引擎装配 Agent 时 MUST 取该角色自己声明的提示词常量。`TaskRequest` MUST NOT 存在系统提示词字段；装配工厂 MUST NOT 接受提示词入参。

#### Scenario: 角色提示词来自引擎常量
- **WHEN** 引擎装配任一角色
- **THEN** 该角色的 `system_prompt` 等于引擎该角色的提示词常量
- **AND** 无需 Django 传入任何提示词

#### Scenario: TaskRequest 无提示词通道
- **WHEN** Django 组装 `TaskRequest`
- **THEN** 该对象不含系统提示词字段，引擎侧也无从外部覆盖提示词的入参

#### Scenario: 三份常量均非空
- **WHEN** 读取引擎三份提示词常量
- **THEN** 规划 / 执行 / 验收三份均非空且为 Markdown 正文

### Requirement: 引擎以框架步骤承载执行与验收

引擎 SHALL 使用 AgentScope 的标准作业流程（SOP）承载「执行 + 验收」的步骤化编排，MUST NOT 再自建执行 ↔ 验收的重试循环。引擎对 AgentScope 的依赖版本 SHALL 满足该模块存在；升级依赖 MUST NOT 改变引擎零平台依赖的边界。

#### Scenario: 依赖面满足步骤编排

- **WHEN** 引擎按当前依赖版本装配并运行一次任务
- **THEN** 所用 AgentScope 版本提供 SOP 模块，且引擎既有的模型 / 凭证 / 消息块 / 事件流导入面不受影响

#### Scenario: 引擎仍零平台依赖

- **WHEN** 检查引擎源码的 import
- **THEN** 引擎 MUST NOT import 平台模块；运行状态与过程日志的落点仍由调用方注入

#### Scenario: 编排职责不再重复实现

- **WHEN** 检查引擎的步骤推进实现
- **THEN** 步骤推进、驳回计数与状态由框架步骤承载，引擎侧 MUST NOT 再保留同职责的自建循环
