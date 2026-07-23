# AI Assistant Rules — Android-AutoTests

## 概述

面向测试人员的自然语言 AI 助手，通过对话完成自动化测试全流程。底层由 AgentScope 2.0 驱动，封装为 38 个 Tool，LLM 通过 Function Calling 自动选择。

## 交互架构

```
用户 (Vue ChatView)
    ↓ SSE 流式对话
AgentScope Agent (FastAPI :8000)
    ├── system_prompt: 平台约束 + SOP 四阶段工作流
    ├── toolkit: 38 个 Tool（34 业务 + 4 Plan）
    ├── model: DashScope / OpenAI / Anthropic
    └── reply_stream() → EventType 事件流
    ↓ Tool 调用
Django ORM / API（同进程直接调用）
    ↓
SQLite/MySQL 业务数据库
```

## SOP 四阶段工作流

这是注入到所有 Agent system_prompt 中的核心工作流，引导 AI 按标准流程推进：

### 阶段 1：需求分析与用例设计

```
目标：理解用户需求 → 设计用例方案 → 用户确认
Tool：TaskCreate → TaskUpdate → create_test_sop
产出：case_design JSON（用例名称/描述/步骤）
规则：
  - 需求不明确时必须逐项询问，禁止跳过
  - 设计方案必须等用户确认后才进入下一阶段
```

### 阶段 2：元素准备

```
目标：确保用例所需页面元素已存在
Tool：fetch_page_elements → search_elements → update_test_sop
产出：element_mapping（元素映射表）+ element_gaps（缺失元素）
规则：
  - 缺失元素告知用户具体缺少什么
  - 记录 gaps 到 sop_context
  - 全部就绪后等用户确认
```

### 阶段 3：用例创建与调试

```
目标：创建测试用例 → 调试到 PASS
Tool：save_test_case → debug_test_case → update_test_sop
产出：case_ids（通过的用例 ID 列表）
规则：
  - 步骤中使用阶段 2 获取的 XPath 定位符
  - 调试失败 → 分析原因 → 调整 steps → 重新 save + debug
  - 必须全部 PASS 才能进入执行阶段
```

### 阶段 4：任务执行

```
目标：锁定设备 → 创建任务 → 执行 → 释放
Tool：get_online_devices → acquire_device → create_runner_task
     → run_test → get_run_results → release_device → update_test_sop
产出：run_id + run_results
规则：
  - loop_count 默认为 3（用户未指定时）
  - 执行完毕后必须释放设备
  - 更新 sop_context 的 run_results 字段
```

## 两层工具体系

| 层级 | 工具 | 存储 | 用途 |
|------|------|------|------|
| **Plan 工具** | `TaskCreate` `TaskGet` `TaskList` `TaskUpdate` | agent.state.tasks_context（内存态） | 阶段内子任务拆解和进度追踪 |
| **SOP 工具** | `create_test_sop` `update_test_sop` | Django DB `tr_test_sop`（持久化） | 跨阶段状态机，记录产出和推进阶段 |

> Plan 工具管理"怎么做这个阶段"，SOP 工具管理"做到哪个阶段了"。两者协作：阶段内 Plan 所有子任务完成 → SOP 推进阶段。

## SOP 状态机

```
create_test_sop (phase=1→2)
    → update_test_sop (phase=2→3)
        → update_test_sop (phase=3→4)
            → update_test_sop (phase=4, status='completed')

任意阶段可转为：
    → update_test_sop (status='cancelled')  # 用户取消
```

`sop_context` 字段随阶段推进逐步填充：
- Phase 1 → `requirement` `case_design`
- Phase 2 → `element_mapping` `element_gaps`
- Phase 3 → `case_ids` `debug_notes`
- Phase 4 → `run_id` `run_results`

## 对话流程

```
用户创建 Agent → 注册到 AgentScope (agent_scope_id)
    ↓
创建 Conversation → 创建 AgentScope session (agent_scope_session_id)
    ↓
用户发送消息 → SSE 流式输出
    ↓ ai_messages 表记录
Agent reply → TextBlock/ThinkingBlock/ToolUseBlock/ToolResultBlock
    ↓
前端 EventType 解析 → 实时渲染
    ↓ REPLY_END
调用 save-message API → 持久化完整 blocks 到 ai_messages
```

## 消息持久化

SSE 流结束后，前端调用 `/api/ai/conversations/<id>/save-message`：

```json
{
  "role": "assistant",
  "blocks": "[{\"type\":\"text\",\"text\":\"...\"}, ...]",
  "reason": "normal",
  "tokens": 1234,
  "input_tokens": 567,
  "model_name": "qwen-max"
}
```

`blocks` 字段存储 AgentScope 的完整 ContentBlock 结构：
- `TextBlock` — 文本回复
- `ThinkingBlock` — 思考过程
- `ToolUseBlock` — 工具调用
- `ToolResultBlock` — 工具结果
- `HintBlock` — SOP 状态卡片/任务卡片等前端渲染提示

## 用户确认（HITL）

部分工具（如执行测试）需要用户确认后才执行：

```
Agent → REQURE_USER_CONFIRM 事件（tool_call_id, tool_call_name, tool_call_input）
前端 → 显示确认弹窗
用户 → 点击确认/拒绝
前端 → POST /confirm-result {tool_call_id: "...", decision: "ALLOW/DENY"}
AgentScope → 收到确认结果 → 继续或跳过工具调用
```

## 系统提示词架构

```
_PLATFORM_CONTEXT (平台能力约束)
  + 数据获取规则：所有数据必须通过工具获取
  + 工具选择策略表：用户意图 → 必须调用的工具

_SOP_WORKFLOW_HINT (四阶段工作流)
  + 两层工具体系解释
  + 每个阶段的详细 SOP
  + 状态输出规范（<system-hint> 标签）
  + 用户取消处理

+ [用户自定义提示词]（可选，从 ai_agents.system_prompt 读取）
```

## 对话恢复

SOP 上下文 (`tr_test_sop`) 持久化在数据库，支持跨会话/跨服务恢复：
- 对话中断 → 下次打开同一 Conversation → 读取 `sop_context` → 从上次阶段继续
- AgentScope 重启 → Redis 状态丢失 → 从 Django DB 重建会话
