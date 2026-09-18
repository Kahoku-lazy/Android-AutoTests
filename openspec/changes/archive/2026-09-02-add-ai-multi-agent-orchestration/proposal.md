## Why

AI 助手要执行「识别 UI 页面、控制设备、编写用例、梳理 UI 页面元素」等繁杂任务，当前"单智能体 = 一套 prompt + 一个模型 + 全量工具"的设计无法有条理完成——该看图的用它推理、该写用例的它去点设备，混在一起。且智能体应是平台级资产，由管理员统一管理，用户只使用。因此把智能体重构为「**多 Harness 编排**」：`Agent = model + Harness`，模型固定池子（vision/pro/强模型），不同任务套不同 Harness，一个对话经「意图识别 → 路由 → 对应 Harness 执行」。

## What Changes

1. 新增 `agent_scope/agent_manager.py`：`Harness`（任务外壳：system_prompt + 工具子集 + 模型参数 + 上下文/循环配置）+ `AgentManager`（4 套 Harness：意图识别/视觉/推理/强模型）+ `build_agent`（model + harness → AgentScope Agent 装配）。
2. 新增 `agent_scope/model_instance.py`：`create_model`（按 provider 用专用模型类，`DeepSeekChatModel` 等）+ `run_intent`（意图识别，输出 `{intent, intent_code, prompt}`）+ `route`（按 code 或强模型开关选 Harness）+ `run`（完整流程，Django 唯一入口，流式）。
3. 新增 `agent_scope/tools.py`：平台工具改为**普通函数 + `FunctionTool` 包装**（框架自带 schema 推导 + 图片返回 + 权限子类），替代现有 `tool_registry.py` + `in_process_tool.py` 手动 ToolBase 子类方案。
4. Django 薄壳改造：`chat_views.py` 退化为「读配置 → 调 `agent_scope` → 存对话记录 → SSE 流式」，不再含智能体逻辑（意图分类、上下文裁剪等逻辑迁入 `agent_scope/`）。
5. 移除 `rag_service.py`（知识库）与 `skill_registry.py`（workspace 技能），本次不涉及；`vision_model_name` 字段由「每 Harness 一个 model_name」取代。

**BREAKING**：`tool_registry.py` + `in_process_tool.py` 被 `tools.py` 替代（工具注册与调用方式改变）；`AIAgent` 单一智能体的模型切换逻辑废弃，改为多 Harness。

## 关联文档

- `apps/ai_assistant/AGENTS.md`（职责划分：Django 薄壳 / agent_scope 内核）
- `dev_docs/项目笔记/AgentScope/多智能体编排-最终骨架设计.md`（本次设计定稿，含 12 条决策）
- `dev_docs/项目笔记/AgentScope/AgentScope 配置智能体.md`（Agent 装配方式）
- `dev_docs/项目笔记/AgentScope/工具/Python 函数工具.md`（FunctionTool 方案）

## Capabilities

### New Capabilities

- `ai-multi-agent-orchestration`: 智能体按「model + Harness」组织为多套专用 Harness（意图识别/视觉/推理/强模型），一个对话经意图识别后路由到对应 Harness 执行，支持强模型手动短路开关。

### Modified Capabilities

（无）

## Impact

- 后端：`apps/ai_assistant/agent_scope/agent_manager.py`（新增）、`model_instance.py`（新增）、`tools.py`（新增）、`provider_registry.py`（保留）、`usage_tracker.py`（保留）；删除 `tool_registry.py` + `in_process_tool.py` + `rag_service.py` + `skill_registry.py`；`views/chat_views.py`（薄壳化）。
- 前端：对话入口不变；智能体配置页随编排结构调整（管理员配置 Harness + 模型，后续跟进）。
- 测试：`tests/ai_assistant/` 中依赖 `tool_registry`/`in_process_tool` 的测试需同步改写；新增 `agent_manager`/`model_instance`/`tools` 单测。
