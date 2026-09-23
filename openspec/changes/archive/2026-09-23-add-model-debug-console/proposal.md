## Why

平台智能体由规划 / 执行 / 验收三个模型组成，三者各有独立的提示词、模型连接与工具子集。但改完提示词后**没有任何地方能确认「改的这条到底生效没有」**：要么跑一整条设备任务（慢、要真机、影响面大），要么登服务器跑命令行 model_test。工具箱缺一个「单模型可视调试台」。

## What Changes

- 工具箱「工具来源」新增第四项**模型调试**（不绑「交给助手」总闸）；选中后右侧列出规划 / 执行 / 验收三个模型入口，点入口进独立调试子页。
- 新增角色调试子页 /ai-assistant/toolbox/models/:role，只读展示该角色**实际生效**的配置：
  - 系统提示词（Markdown 渲染）
  - 模型连接（provider / model_name / 是否视觉；**不含 api_key 等敏感字段**）
  - 该角色工具子集（逐条标只读/写、是否被平台停用）
  - 当前启用的技能清单（**明示三模型共用**，不得让用户以为按角色分配）
  - 智能体启用的知识库来源（**明示执行链路当前未挂 RAG**，不得让用户以为角色在用知识库）
- 新增**单角色调试对话**：用该角色真实提示词与模型发起一次调用，**不挂工具、不触碰真机**；非流式；**单次超时 5 分钟**；对话**不落库**。
- 调试配置读取与调试对话**仅超级管理员**可用；模型连接缺失（provider / model_name / api_key 任一为空）时返回可读 4xx，不得返回空回复。
- **不**做流式、**不**做真机执行或工具调用开关、**不**把 RAG 接进执行链路、**不**改技能的角色分配、**不**落库调试对话历史。

## 关联文档

- PRD-需求总纲（AI 助手条目）
- PRD-08-AI助手（工具箱增量；总纲登记的模块 PRD，仓库当前缺正文）
- 同构参照：既有能力 ai-platform-tool-debug（平台工具调试页）、ai-device-prompts（提示词唯一真相源）

## Capabilities

### New Capabilities

- ai-model-debug: 工具箱内的单模型调试台——三个角色入口、角色生效配置的只读展示（提示词 / 模型连接 / 工具子集 / 技能 / 知识库来源）、以及单角色文本对话验证提示词是否生效。

### Modified Capabilities

（无）

## Impact

- 后端：新增 apps/ai_assistant/model_debug.py（把 management/commands/model_test.py 的三角色装配抽成命令与 HTTP 共用的 service）+ views_model_debug_drf.py（只读配置 + 调试对话）+ urls.py 路由；model_test 命令改为复用同一 service。
- 前端：helpers/toolbox-assembly.ts（第四个来源）、components/ToolboxPanel.vue（三张角色卡）、新页 ModelDebugPage.vue + ModelDebugPage.style.css、composables/useModelDebug.ts、api/toolbox.ts、routes.ts、constants.ts。
- 接口契约：新增 GET /api/ai/model-debug/{role}/ 与 POST /api/ai/model-debug/{role}/chat（仅超管；对话超时 5 分钟）。
- 测试：后端单测（角色工具子集与脱敏、非超管 403、缺配置 400、对话不落库、改提示词后回复变化）+ 前端 spec + 真实浏览器端到端。
- 文档：AI 助手接口文档补两个端点。
- 迁移 / 依赖：无（不加字段、不加依赖）。
