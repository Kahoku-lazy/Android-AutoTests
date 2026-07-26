# SPEC — AI 助手模块重构

> 基于 SPEC-模块重构规范.md，针对 ai-assistant 模块的逐阶段执行计划。
> 版本：v1.0 · 日期：2026-07-25

---

## 当前状态快照

```
frontend/src/modules/ai-assistant/
├── index.vue                         578 行 · 智能体看板 + 任务看板
├── AgentDetail.vue                   515 行 · Agent 编辑页（已拆 6 子组件）
├── ChatView.vue                      546 行 · 对话界面
├── ChatView.css                      602 行 · 对话页 CSS
├── KnowledgeBase.vue                 268 行 · 知识库管理
├── EvaluatorTab.vue                  554 行 · 评测中心
├── api.js                            577 行 · API 层（SSE + AgentScope）
├── evaluator-api.js                   75 行 · 评测 API（✅ 已集中）
├── routes.js                          11 行
├── constants.js                       ❌ 缺失
├── components/ (16 文件)
│   ├── AgentStickyNote.vue           427 行
│   ├── MessageBubble.vue             391 行
│   ├── AgentToolsPanel.vue           364 行
│   ├── HintCard.vue                  347 行
│   ├── TaskStickyNote.vue            297 行
│   ├── ConfirmDialog.vue             233 行
│   ├── ChatInput.vue                 200 行
│   ├── ToolCallCard.vue              158 行
│   ├── ThinkingBlock.vue              89 行
│   ├── AgentModelConfig.vue           67 行
│   ├── AgentBasicInfo.vue             61 行
│   ├── AgentAdvancedConfig.vue        49 行
│   ├── AgentFormFooter.vue            48 行
│   ├── AgentMcpDialog.vue             43 行
│   ├── AgentPromptEditor.vue          41 行
│   └── WbLoader.vue                   28 行
└── composables/ (7 文件)
    ├── useSSE.js                     677 行 · SSE 流式连接
    ├── useAgentTools.js              288 行 · Agent 工具配置
    ├── useConversation.js            138 行 · 对话管理
    ├── useMessageStore.js            112 行 · 消息状态
    ├── useMarkdown.js                 72 行 · Markdown 渲染
    ├── useToolCalls.js                11 行
    └── useToolConfirm.js              11 行
```

**架构评级**：L3。16 子组件 + 7 composables，拆分最彻底的模块。缺 constants.js。

**模块总行数**：~3726（9 模块中第二大，仅次于 case-manager ~4876）。

---

## 关键问题

| 问题 | 严重度 | 说明 |
|------|:--:|------|
| **~20 处裸调 API** | 🟠 | API 调用分散在 Vue 文件和 composables 中，api.js 只覆盖 SSE/AgentScope |
| **Section 标题不一致** | 🟡 | index.vue 用标准 doc-section__title；EvaluatorTab + AgentDetail 自定义 .section-title |
| **缺 KpiCard** | 🟡 | KnowledgeBase 手写 .kb-stat 网格；EvaluatorTab 手写 .score-badge |
| **缺 FilterTabs** | 🟢 | KnowledgeBase 手写 .kb-filter-btn；EvaluatorTab 手写 sub-tab 按钮 |
| **EvaluatorTab 554 行** | 🟠 | 无子组件拆分，5 个评测 Tab 全在一个文件 |
| **ChatView.css 602 行** | 🟡 | 独立 CSS 文件，结构与 ChatView.vue 分离 |
| **raw fetch 绕过 api-client** | 🟡 | ChatView.vue 文件上传用 raw fetch，绕过 JWT 拦截器 |
| **字体** | ✅ | 无 Caveat/Quicksand 残留 |
| **背景** | ✅ | 点阵图案已在使用（.dot-board） |
| **WbLoader 可替换** | 🟢 | 自定义加载组件 → shared SkeletonCard |

---

## 阶段 1：基础设施 — 已完成 ✅

背景 + 字体 + 全宽已全局统一。

---

## 阶段 2：Section 标题标准化

| 文件 | 当前 | 修改 |
|------|------|------|
| EvaluatorTab.vue | 自定义 `.section-title` | 改为 `doc-section__header > h3.doc-section__title + span.doc-tag` |
| AgentDetail.vue | 自定义 `.section-title` + `.section-num` | 同上，num 改为 doc-tag |
| KnowledgeBase.vue | 无标题 | 加统计概览标题 |

---

## 阶段 3：KpiCard 替换手写统计

### KnowledgeBase — 手写 `.kb-stats` 网格

```
当前: <div class="kb-stat"> 文档总数 12 </div>
替换: <KpiCard value="12" label="文档总数" color="var(--c-ai)" shape="diamond" />
```

4 个卡片：文档总数 / 已索引 / 待索引 / 存储大小

### EvaluatorTab — 手写 `.score-badge`

```
当前: <div class="score-badge"> 85.3 </div>
替换: <KpiCard :value="`${score}%`" label="通过率" color="var(--c-ai)" shape="circle" />
```

---

## 阶段 4：API 层补全

### 问题

api.js 577 行但只覆盖 SSE 流 + AgentScope 运维。Agent CRUD / Conversation CRUD / Tasks / Knowledge 全裸调。

### 操作

从 api.js 追加导出或在 api/ 子目录新建：

```
api/
├── agents.js          ← listAgents / getAgent / createAgent / updateAgent / deleteAgent
├── conversations.js   ← listConversations / getConversation / renameConversation / deleteConversation
├── knowledge.js       ← getKnowledgeStatus / listDocuments / reindexDocuments
├── tasks.js           ← listTasks
└── models.js          ← detectModels
```

或者在现有 api.js 追加——但 api.js 已经 577 行，拆分子目录更好。

---

## 阶段 5：FilterTabs 替换手写筛选

| 文件 | 当前 | 替换 |
|------|------|------|
| KnowledgeBase.vue | 手写 `.kb-filter-btn` 按钮组 | `<FilterTabs :tabs="..." v-model="..." />` |
| EvaluatorTab.vue | 5 个手写 sub-tab div | `<FilterTabs>` 或 `<AppTabs>` |

---

## 阶段 6：EvaluatorTab 拆分

554 行，5 个评测框架 Tab 各 80-120 行逻辑。拆为：

```
components/evaluator/
├── EvaluatorTab.vue          ~150 行 · Tab 容器
├── SelfTestPanel.vue          ~80 行 · 自检评测
├── KbTestPanel.vue            ~80 行 · 知识库评测
├── EvalScopePanel.vue         ~80 行 · EvalScope
├── DeepEvalPanel.vue          ~80 行 · DeepEval
└── MasEvalPanel.vue           ~80 行 · MasEval
```

---

## 阶段 7：constants.js 补全

| 当前位置 | 内容 |
|------|------|
| index.vue | `VIEW_TABS`（智能体看板/知识库/评测中心） |
| KnowledgeBase.vue | `KB_FILTERS`（筛选按钮配置） |
| EvaluatorTab.vue | `EVAL_TABS`（5 个评测框架 Tab）、`FRAMEWORKS` 配置 |
| AgentDetail.vue | Form steps、provider list、memory modes |

---

## 阶段 8：PRD 更新

参照 PRD-00 格式更新 PRD-06-AI助手.md。

---

## 执行顺序

```
1. Section 标题标准化              →  1h   ─ 3 文件
2. KpiCard 替换手写统计             →  1h   ─ KnowledgeBase + EvaluatorTab
3. API 层补全（拆分 api/ 子目录）    →  2h   ─ 裸调 20→0
4. FilterTabs 替换                  →  0.5h ─ 2 文件
5. EvaluatorTab 拆分                →  3h   ─ 554→150 + 5 子组件
6. constants.js 补全               →  0.5h
7. PRD 更新                         →  1h
                                   ─────
                                    9h
```

## 验证

```bash
npx vite build --mode development
grep -rn "client\.\(get\|post\)" modules/ai-assistant/ --include="*.vue" | grep -v api.js
ls modules/ai-assistant/constants.js
```
