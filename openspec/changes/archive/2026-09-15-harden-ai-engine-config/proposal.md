## Why

P0 三条「配置错了不报错」的静默行为，故障点发生在配置之外（LLM 调用 / 工具层），排查成本高（依据 `dev_docs/05-开发与测试/设计方案与报告/报告-AgentScope代码核对分析.md` §四 N1/N2/N3、§六 P0）：

| # | 现象 | 证据 |
|---|------|------|
| P0-1 | provider→凭证映射存在两份且无一致性校验：A2 的 `credential_type` **零消费方**（唯一引用是定义处），真正的映射硬编码在 A3；`create_model` 兜底分支把**任何未知 provider 当 OpenAI 兼容**，不报错 | `apps/ai_assistant/provider_registry.py:58` · `engines/ai/agentscope/model.py:217-243` |
| P0-2 | A2 为所有 provider 解析了 `base_url`，A3 的 dashscope 分支**不传** —— 自定义地址被静默丢弃 | `apps/ai_assistant/engine_adapter.py:18-26` · `model.py:233-238` |
| P0-3 | A2 对 `route_configs` 无结构校验：缺失角色会生成 `model_name=""` / `api_key=""` 的空 spec；无在线设备时传空 serial，工作流照常启动 | `engine_adapter.py:56-61` · `:42-49` |

为什么现在：设计方案《AgentScope 设计系统分层》的验收口径之一是「A2 是配置装配的唯一入口」；三条不修则该口径不成立，且与 A1 已实现的 fail-fast 策略（`engines/ai/registry.py:35-52`）自相矛盾。

## What Changes

- **A2 `provider_registry.py`**：删除零消费方的 `credential_type`；`PROVIDER_DEFAULTS` 收敛为「provider → base_url」单一职责
- **A2 `engine_adapter.py`**：新增装配期校验 —— provider 必须在 `VALID_PROVIDERS` 内、三角色 `model_name` 与可解密 `api_key` 非空、`device_control` 线路必须存在；无 `task.device_serial` 且无在线设备时抛出可读错误，不再传空串
- **A3 `model.py`**：`create_model` 去掉「未知 provider 静默降级为 OpenAI 兼容」—— 兜底收窄为显式的 OpenAI 兼容白名单（`openai` / `anthropic` / `gemini` / `custom`），其余抛 `ConfigurationError`；dashscope 分支传递 `base_url`（若该链路确认不支持自定义地址，则必须显式报错，不得解析后丢弃）
- **测试**：新增 `tests/graybox/unit/test_ai_engine_config.py`，并新增一条一致性断言 —— `create_model` 认识的 provider 集合 == `VALID_PROVIDERS`
- **前置数据核查**：改 fatal 之前先核查存量 `ai_agent.route_configs` 中出现过的 provider 取值；若存在集合外的值，先数据订正（`serializers.py:54,78` 已把住写入侧，风险仅来自历史行）
- **BREAKING**（行为层）：配置非法/缺失的智能体由「能启动、晚失败」变为「装配期即失败」；不在白名单的 provider 同理抛错。不影响合法配置、不改 API 契约、不改 DB schema

## 关联文档

- 分析报告（本单来源）：`dev_docs/05-开发与测试/设计方案与报告/报告-AgentScope代码核对分析.md` §四 N1/N2/N3、§六 P0
- 设计方案（对照对象）：`dev_docs/05-开发与测试/设计方案与报告/设计方案-AgentScope设计系统分层.html` §A2/A3（该文件被 `.gitignore:121` 的 `dev_docs/**/*.html` 忽略，不入库）
- ARCH：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（L1c 可替换插槽 · §1.4 通信通道）
- 层约束：`engines/ai/AGENTS.md`（框架版本 2.0.7.post1）· `apps/AGENTS.md`（分层与写库边界）

## Capabilities

### New Capabilities

（无 —— 本次不引入新能力，改的是既有协议能力的输入侧约束）

### Modified Capabilities

- `ai-engine-protocol`: 新增「装配期配置 fail-fast」与「provider 解析单一真相源」两条 Requirement；既有「TaskRequest 契约」「引擎注册与 fail-fast」两条 Requirement 的文本不变，仅在其同族内补强输入侧约束

## Impact

- 源码：`apps/ai_assistant/provider_registry.py` · `apps/ai_assistant/engine_adapter.py` · `engines/ai/agentscope/model.py`（净增约 40 行、净删约 15 行）
- 测试：新增 `tests/graybox/unit/test_ai_engine_config.py`（约 6 条）
- 数据：一次性核查 `ai_agent.route_configs` 的 provider 取值（只读核查，异常才订正）
- 不受影响：`engines/ai/base.py`（A1 契约不动）、前端、DRF 路径与信封、DB schema；`model_test.py` / `ui_pipeline.py` 绕过 A2 的直接装配路径经 A3 拿到同一套 fail-fast
