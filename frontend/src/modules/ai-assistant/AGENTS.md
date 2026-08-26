# ai-assistant 模块 AGENTS.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## 红线（全局表 ai-assistant 行的展开）

| 只做 | 禁止 |
|------|------|
| 智能体看板 / 对话 / 工具箱 / 知识库 / 评测中心 UI | LLM 推理 / 数据库与设备直连 |
| 评测中心契约走 `/evaluator/*`（`evaluator-api.ts`，前端寄宿） | 另起非约定 HTTP 客户端（SSE 的 fetch 是唯一特例） |

- 本模块是 SSE 的**唯一**消费方，禁止新增第二条流式通道。

## 本模块契约（真相源：`api/*.ts` + `evaluator-api.ts`）

- 对话流：`POST /api/ai/conversations/{id}/chat/stream`（协议见下）
- 评测：`/evaluator/banks*` · `/evaluator/frameworks` · `/evaluator/runs*`；body 为 snake_case（`agent_id` / `bank_id` / `judge_model`）
- 其余 REST（agents / conversations / toolbox）：对应 `api/*.ts` 为真相源，端点变更同改

## 本模块特殊布局/样式

- **折叠规则（本模块唯一）**：`ThinkingBlock` 默认折叠手动展开；`ToolCallCard` 默认展开——改动必须保持默认态。

## 本模块协议要点

**SSE（本模块专属，全项目唯一 SSE）**：

- 单请求流式：`streamChat()`（`api/sse.ts`）用原生 `fetch`（axios 不能流式），事件经 `SSEMessageBuilder` 归一化 phase 后按类型渲染（事件→渲染表见全局 §3）。
- 401 → refresh 一次 → 重放一次；仍失败清 token 跳登录。
- `_backend_msg_id` 用于跳过重复 `save-message`；改持久化逻辑不得破坏该去重。

## 关单附加项（全局清单的 delta）

```
[ ] SSE 各事件类型渲染正确；reply_end / exceed_max_iters 双路径都收口
[ ] ThinkingBlock / ToolCallCard 默认折叠·展开态未变
[ ] 断流报错、stale 回调失效、401 刷新重放一次 行为不变
[ ] 评测接口 body snake_case，经 evaluator-api.ts（不旁路新客户端）
```
