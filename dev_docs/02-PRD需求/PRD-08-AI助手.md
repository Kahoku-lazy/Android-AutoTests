# PRD-06 — AI 助手 (AI Assistant)

> 关联需求大纲：[`需求大纲.md`](./需求大纲.md) §5.7
> 版本：v5.0 · 日期：2026-07-27

---

## 1. 功能定位

AI 助手是平台的智能对话中枢。用户在此管理 AI Agent、发起多轮对话、上传附件、通过 SSE 流式接收回复，并查看 Agent 执行任务的状态。页面由 Agent 管理面板 + 对话窗口 + 任务看板三个区域构成。

---

## 2. 设计目录

```
frontend/src/modules/ai-assistant/
├── index.vue                         578 行 · Agent 管理 + 任务看板编排者
├── api.js                            577 行 · 数据层（SSE 流 + AgentScope 健康检查）
├── evaluator-api.js                   75 行 · 评估器 API
├── routes.js                          11 行 · 路由定义
├── composables/
│   ├── useSSE.js                     677 行 · SSE 流处理 + 降级 + HITL 确认
│   ├── useConversation.js            138 行 · 会话 CRUD + 内联重命名
│   ├── useMessageStore.js            112 行 · 消息数组状态 + 重建
│   ├── useAgentTools.js              288 行 · Agent 工具/技能加载
│   ├── useMarkdown.js                 72 行 · Markdown 渲染 + Mermaid
│   ├── useToolCalls.js                11 行 · 工具调用状态
│   └── useToolConfirm.js              11 行 · HITL 确认状态
├── ChatView.vue                      546 行 · 对话窗口（SSE 流 + 消息渲染）
├── ChatView.css                      602 行 · 对话窗口独立样式（⚠ 非 scoped）
├── AgentDetail.vue                   515 行 · Agent 配置（5 步向导）
├── EvaluatorTab.vue                  554 行 · 评估器 Tab（NL 用例生成 + 执行）
├── KnowledgeBase.vue                 235 行 · 知识库管理（KPI + 文档表）
└── components/
    ├── AgentStickyNote.vue           427 行 · Agent 便签卡片（动画）
    ├── MessageBubble.vue             391 行 · 消息气泡（文本/思考块/工具卡片/提示）
    ├── AgentToolsPanel.vue           364 行 · Agent 工具/技能配置面板
    ├── HintCard.vue                  347 行 · SOP 提示卡片（阶段 + 用例 + PRD 预览）
    ├── TaskStickyNote.vue            297 行 · 任务便签卡片（动画）
    ├── ConfirmDialog.vue             233 行 · HITL 确认弹窗
    ├── ChatInput.vue                 200 行 · 消息输入栏（附件 + 发送）
    ├── ToolCallCard.vue              158 行 · 工具调用卡片（折叠展开）
    ├── ThinkingBlock.vue              89 行 · 思考块（可折叠推理过程）
    ├── AgentModelConfig.vue           67 行 · Agent 模型配置
    ├── AgentBasicInfo.vue             61 行 · Agent 基本信息
    ├── AgentAdvancedConfig.vue        49 行 · Agent 高级配置
    ├── AgentFormFooter.vue            48 行 · Agent 表单底部操作栏
    ├── AgentMcpDialog.vue             43 行 · MCP 配置弹窗
    ├── AgentPromptEditor.vue          41 行 · 系统提示词编辑器
    └── WbLoader.vue                   28 行 · 加载动画
```

**架构特征**：L3 评级。Composable 层设计良好（7 个模块，职责清晰），但存在以下违规：useSSE/useConversation 直接调用 ElMessage（BL 层引用 UI 层）、5 个 .vue 文件 ~25 处裸 client 调用 bypass api.js。ChatView.css 为独立文件（非 scoped）。无 constants.js。无 Pinia store（全部 composable + local refs）。共享组件采用率 6/14（43%）。

---

## 3. 核心功能

### 3.1 Agent 管理面板

`index.vue` — 顶部 Agent 便签卡片滚动行（AgentStickyNote × N），底部任务看板（TaskStickyNote × N）。每个 Agent 卡片显示名称、模型、在线状态（绿色圆点）。点击进入 ChatView 对话。新建/编辑 Agent 跳转 AgentDetail.vue（5 步向导：基本信息 → 模型配置 → 系统提示词 → 工具/技能 → 高级配置）。健康检查每 30 分钟轮询一次。

### 3.2 对话窗口 (ChatView)

`ChatView.vue` + `ChatView.css` — 左侧会话列表（新建/重命名/删除），右侧消息流。每条消息通过 MessageBubble 渲染：文本（Markdown + Mermaid 图表）→ 思考块（ThinkingBlock，可折叠）→ 工具调用卡片（ToolCallCard，折叠/展开）→ SOP 提示卡片（HintCard，含阶段进度、用例预览、PRD 摘要）。

**SSE 流生命期**：`useSSE.js` 管理完整流程 — 创建 AgentScope session → 保存用户消息 → 订阅 SSE 流 → 解析 7 种事件类型 → 增量更新消息数组。45 秒看门狗超时。AgentScope 不可用时自动降级到 Django 同步模式。HITL 工具确认通过 `REQUIRE_USER_CONFIRM` 事件 → ConfirmDialog 弹窗 → 用户 ALLOW/DENY → 结果回传 SSE 流。

### 3.3 知识库 (KnowledgeBase)

`KnowledgeBase.vue` — 4 张 KpiCard（文档数/数据库大小/上次索引/状态）+ AppTable 文档列表（名称/来源/块数/状态）。支持手动重索引。筛选栏手写 `.kb-filter-btn` 按钮组（未用 FilterTabs 共享组件）。

### 3.4 评估器 (EvaluatorTab)

`EvaluatorTab.vue` — NL 用例生成 + NL 测试执行。输入自然语言描述 → 选择目标设备 → 生成测试用例或直接执行。子 Tab 切换（用例生成/执行结果）。调用 `evaluator-api.js` 封装 API。

### 3.5 任务看板

`index.vue` 底部 — TaskStickyNote 卡片网格。每张卡片显示任务类型/状态/Agent/进度条。RUNNING 状态任务每 15 秒自动轮询刷新。

---

## 4. 数据流

```
Composables (7, no Pinia)
  ├── useConversation    会话列表 CRUD → api.js
  ├── useMessageStore    消息数组 + 占位符管理
  ├── useSSE             SSE 流核心 → api.js (streamChat) + agentscopeClient
  ├── useAgentTools      Agent 工具/技能/知识库加载 → api.js
  ├── useMarkdown        Markdown + Mermaid 渲染
  ├── useToolCalls       工具调用状态
  └── useToolConfirm     HITL 确认状态

ChatView.vue
  ├── useSSE.sendStreamMessage()  → SSE 连接 → 增量更新 useMessageStore.messages
  ├── useConversation             → 会话列表 + 选择 + 重命名
  └── useMarkdown                 → 渲染消息内容

index.vue
  ├── client.get('/ai/agents')        ← ⚠ 裸调用，应走 api.js
  ├── client.get('/ai/agents/health') ← ⚠
  └── client.get('/ai/tasks')         ← ⚠ 15s 轮询
```

---

## 5. 验收汇总

| 功能编号 | 功能名称 | 验收项 | 通过 | 未验证 |
|:--:|------|:--:|:--:|:--:|
| F-01-01 | Agent 列表 + 便签卡片 | 5 | | 5 |
| F-01-02 | Agent 配置（5 步向导） | 6 | | 6 |
| F-02-01 | SSE 流式对话 | 6 | | 6 |
| F-02-02 | HITL 工具确认 | 4 | | 4 |
| F-02-03 | 文件上传 | 3 | | 3 |
| F-03-01 | NL 用例生成 | 5 | | 5 |
| F-03-02 | NL 测试执行 | 4 | | 4 |
| F-03-03 | 多类型用例生成 (Storage/API/Web) | 4 | | 4 |
| F-03-04 | 用例生成任务卡片 | 4 | | 4 |
| F-04-01 | 知识库管理 | 4 | | 4 |
| **合计** | | **45** | **0** | **45** |

---

## 附录A：测试优先级

| 优先级 | 覆盖范围 | 验收时机 |
|:--:|------|------|
| P0 | F-01-01~F-02-02（Agent 管理 + SSE 对话 + HITL） | 每次 MR 前 |
| P1 | F-02-03~F-03-04（文件上传 + NL 生成 + 任务卡片） | 发版前 |
| P2 | F-04-01（知识库）、降级模式、断线重连 | 大版本前 |

## 附录B：实施状态

| 功能 | 状态 |
|------|:--:|
| Agent CRUD + 模型切换 + 便签卡片 | ✅ |
| SSE 流式对话 + Markdown 渲染 | ✅ |
| HITL 工具确认弹窗 | ✅ |
| 文件上传 | ✅ |
| NL 用例生成 + 执行（评估器） | ✅ |
| 知识库管理（KPI + 文档表 + 重索引） | ✅ |
| 降级模式（AgentScope 不可用→Django 同步） | ✅ |
| 任务看板（15s 轮询） | ✅ |
| F-03-03 多类型用例生成 (Storage/API/Web) | 📋 |
| F-03-04 用例生成任务卡片 | 📋 |
| 裸 client 收敛到 api.js (~25 处) | 📋 |
| useSSE.js 拆分 (677→3 子模块) | 📋 |
| ChatView.css 602 行迁移为 scoped | 📋 |
| constants.js 补全 | 📋 |

## 附录C：已知问题与改进项

| 编号 | 问题 | 严重度 | 记录日期 |
|:--:|------|:--:|:--:|
| IMP-01 | useSSE.js 677 行超标，应拆出 streamClient/fallback/confirm 三个子模块 | 🔴 | 2026-07-27 |
| IMP-02 | 5 个 .vue 文件 ~25 处裸 client/fetch 调用，bypass api.js | 🔴 | 2026-07-27 |
| IMP-03 | ChatView.css 602 行独立文件 + 75 处硬编码 hex，应迁移为 scoped | 🟠 | 2026-07-27 |
| IMP-04 | useSSE + useConversation 直接调用 ElMessage/ElMessageBox（BL 层引用 UI 层） | 🟠 | 2026-07-27 |
| IMP-05 | 346 处硬编码 hex 颜色（271 vue + 75 css），应迁移到 tokens.css 引用 | 🟡 | 2026-07-27 |
| IMP-06 | EvaluatorTab 554 行 + 10 处 console.error 无 ErrorState | 🟡 | 2026-07-27 |
| IMP-07 | KnowledgeBase 手写 .kb-filter-btn 而非用 FilterTabs 共享组件 | 🟢 | 2026-07-27 |
| IMP-08 | index.vue 行 509 样式 bug: `background-color: #fff);` 尾部多余括号 | 🟢 | 2026-07-27 |
