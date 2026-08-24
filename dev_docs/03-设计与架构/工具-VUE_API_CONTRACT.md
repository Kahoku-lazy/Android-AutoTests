# Vue ↔ 后端 交互契约

> 📅 最后同步：2026-07-27 | 覆盖模块：8/8（设备/元素/用例/执行/报告/AI助手/工作流）| 下次复查：新增端点时

当修改 Vue 或后端时，按此表逐项校验，确保前后端一致。

## 一、REST API 映射

### 设备管理

| Vue 状态/方法 | HTTP | 端点 | 请求体 | 响应体关键字段 |
|---|---|---|---|---|
| `loadDevices()` | GET | `/api/devices` | — | `{ok, devices:[{serial,model,screen,sdk}], current}` |
| `connectCurrentDevice()` | POST | `/api/devices/{serial}/activate` | `{serial}` | `{ok, current}` |
| `disconnectDevice()` | POST | `/api/devices/{serial}/disconnect` | `{serial}` | `{ok}` |
| 设备信息初始化 | GET | `/api/devices/current` | — | `{serial, screen_w, screen_h, package}` |

### UI 操作

| Vue 状态/方法 | HTTP | 端点 | 请求体 | 响应体关键字段 |
|---|---|---|---|---|
| `dumpPage()` | POST | `/api/elements/dump` | `{}` | `{ok, page_id, package, activity, element_count, elements:[{class_name,text,resource_id,bounds,xpaths,clickable,...}], actionable}` |
| `doAction('click')` | POST | `/api/elements/action` | `{action:"click", x, y}` | `{ok}` |
| `doInput()` | POST | `/api/elements/action` | `{action:"input", text, x, y, clear_first}` | `{ok}` |

### 页面与跳转

| Vue 状态/方法 | HTTP | 端点 | 请求体 | 响应体关键字段 |
|---|---|---|---|---|
| `loadPages()` | GET | `/api/elements/pages` | — | `{ok, pages:[{id,label,package,activity,element_count,created_at}]}` |
| `recordPage()` | PUT | `/api/elements/pages/{page_id}` | `{label}` | `{ok}` |
| `editPageLabel(p)` | PUT | `/api/elements/pages/{page_id}` | `{label}` | `{ok}` |
| `loadPages()` 中的 flows | GET | `/api/elements/flows` | — | `{ok, flows:[{id,from_page_id,to_page_id,from_label,to_label,trigger_text,trigger_rid}]}` |
| `createFlow()` | POST | `/api/elements/flows` | `{from_page_id, to_page_id, trigger_element_id, trigger_action}` | `{ok}` |
| `deleteFlow(id)` | DELETE | `/api/elements/flows/{flow_id}` | — | `{ok}` |

### 导出

| Vue 状态/方法 | HTTP | 端点 | 请求体 | 响应体关键字段 |
|---|---|---|---|---|
| `exportYAML()` | POST | `/api/cases/export/yaml` | `{test_case_name, page_ids:[]}` | `{ok, filename, yaml}` |

### 测试用例 CRUD

| Vue 状态/方法 | HTTP | 端点 | 请求体 | 响应体关键字段 |
|---|---|---|---|---|
| `loadTestDefinitions()` | GET | `/api/cases/definitions` | — | `{ok, definitions:[{id,title,category,description,steps,enabled,steps_data:[{type,xpath,xpath2,timeout,expected_text,index,description}],package_name}]}` |
| `saveCurrentCase()` | POST | `/api/cases/definitions` | `{id,title,category,description,steps,enabled,steps_data,package_name}` | `{ok, id}` |
| `deleteCurrentCase()` | DELETE | `/api/cases/definitions/{case_id}` | — | `{ok}` |
| `selectCase(id)` → 加载单个 | GET | `/api/cases/definitions/{case_id}` | — | `{ok, definition:{...}}` |

### 测试执行

| Vue 状态/方法 | HTTP | 端点 | 请求体 | 响应体关键字段 |
|---|---|---|---|---|
| `startTestRun()` | POST | `/api/runner/run` | `{case_ids:[], loop_count, package_name}` | `{ok, run_id, case_count, loop_count, ws_url}` |
| `stopTestRun()` | POST | `/api/runner/run/{run_id}/stop` | — | `{ok}` |
| — (未在 UI 中使用) | GET | `/api/runner/run/{run_id}/status` | — | `{ok, status, is_running, selected_cases, loop_count}` |

### 报告

| Vue 状态/方法 | HTTP | 端点 | 请求体 | 响应体关键字段 |
|---|---|---|---|---|
| `loadReportFiles()` | GET | `/api/reports` | — | `{ok, files:[{name,size,time,type}]}` |
| `viewReport(rf)` | GET | `/api/reports/{filename}` | — | **FileResponse** (不是 JSON) — `fetch().then(r=>r.text())` |
| `loadRunHistory()` | GET | `/api/runner/runs` | — | `{ok, runs:[{run_id,total,passed,failed,last_time}]}` |

### 工作流

| Vue 状态/方法 | HTTP | 端点 | 请求体 | 响应体关键字段 |
|---|---|---|---|---|
| `lib.bootstrapIfEmpty()` | GET | `/api/workflow/directories` | — | `{ok, directories:[{id,name,parent_id}]}` |
| `lib.createFolder()` | POST | `/api/workflow/directories` | `{name, parent_id}` | `{ok, directory:{id,name}}` |
| `lib.renameNode()` | PUT | `/api/workflow/directories/{id}` | `{name}` | `{ok}` |
| `lib.deleteNode()` | DELETE | `/api/workflow/directories/{id}` | — | `{ok}` |
| `lib.loadPageFlowPayload()` | GET | `/api/workflow/documents/{id}` | — | `{ok, document:{id,name,content,type}}` |
| `lib.savePageFlowPayload()` | PUT | `/api/workflow/documents/{id}` | `{name,content}` | `{ok}` |
| `lib.createDocument()` | POST | `/api/workflow/documents` | `{name,type,parent_id}` | `{ok, document:{id}}` |
| `lib.deleteDocument()` | DELETE | `/api/workflow/documents/{id}` | — | `{ok}` |
| `getDefinition()` (import) | GET | `/api/case-manager/definitions/{id}` | — | `{ok, definition:{steps_data,...}}` |
| `lib.saveCaseDraft()` | PUT | `/api/workflow/documents/{id}` | `{name,blocks,linked_case_id}` | `{ok}` |

### AI 助手

> 信封：全部端点统一 `{status, data}` / `{status, message}`（DRF `EnvelopeJSONRenderer`），JSON snake_case。
> Agents/Conversations 组为 DRF ViewSet；SSE 与工具网关为豁免端点（详见 PRD-08 §5 与 ARCH-08 §4）。

| Vue 状态/方法 | HTTP | 端点 | 请求体 | 响应体关键字段 |
|---|---|---|---|---|
| `listAgents()` | GET | `/api/ai/agents` | — | `{status, data:{agents:[{id,name,model_provider,model_name,tool_count,...}]}}` |
| `getAgentDetail(id)` | GET | `/api/ai/agents/{id}` | — | `{status, data:{agent:{...}}}`（api_key 脱敏 `sk-***xxxx`） |
| `saveAgent()` 新建 | POST | `/api/ai/agents/create` | `{name, model_provider, api_key, ...}` | `{status, data:{id}}` |
| `saveAgent()` 更新 | POST | `/api/ai/agents/{id}/update` | `{...}`（api_key 含 `***` 时跳过更新） | `{status, data:{id}}` |
| `deleteAgent(id)` | POST | `/api/ai/agents/{id}/delete` | — | `{status, data:{}}` |
| `checkAgentsHealth()` | GET | `/api/ai/agents/health` | — | `{status, data:{agents:[{id,name,is_connected,last_checked}]}}` |
| `testAgent(id)` | POST | `/api/ai/agents/{id}/test` | — | `{status, data:{connected, available_models, message}}` |
| `detectModels()` | POST | `/api/ai/models/detect` | `{model_provider, api_key, base_url}` | `{status, data:{models}}` |
| `listConversations(agentId)` | GET | `/api/ai/agents/{id}/conversations` | — | `{status, data:{conversations:[...]}}` |
| `createConversation()` | POST | `/api/ai/agents/{id}/conversations/create` | `{title}` | `{status, data:{id, agent_scope_session_id}}` |
| `getMessages(convId)` | GET | `/api/ai/conversations/{id}/messages` | — | `{status, data:{messages:[...]}}` |
| `saveMessage()` | POST | `/api/ai/conversations/{id}/save-message` | `{role, content, blocks, ...}` | `{status, data:{id}}` |
| `renameConversation()` | POST | `/api/ai/conversations/{id}/rename` | `{title}` | `{status, data:{title}}` |
| `deleteConversation()` | POST | `/api/ai/conversations/{id}/delete` | — | `{status, data:{}}` |
| HITL 确认 | POST | `/api/ai/conversations/{id}/confirm-result` | `{reply_id, confirm_results}` | `{status, data:{}}` |
| `listTasks()` | GET | `/api/ai/tasks` | — | `{status, data:{tasks:[...]}}` |
| 对话任务 | GET | `/api/ai/conversations/{id}/tasks[/{run_id}]` | — | `{status, data:{tasks:[...]}}` / `{status, data:{task}}` |

> 鉴权：除 `/api/ai/tools/*`（网关白名单）外全部需要 JWT Bearer；错误统一 `{status:false, message}` + HTTP 状态码。
> 权限语义：对象级检查先于存在性检查 —— 不存在/无权资源均返回 403（不泄露存在性）。

---

## 二、WebSocket 映射

### WS-1: 实时截图 `/ws/screenshot` — 已移除（v1.7 快照化）

> 设备检查器 v1.7 起无实时截图流：`ScreenshotConsumer` / `stream.py` 已删除，`ws/screenshot` 路由下线。
> 截图与页面数据改由 HTTP 快照链路获取（见下方 REST 表）；前端 `ScreenshotView` 仅静态展示快照截图 + 边界框 overlay。

**设备检查器快照 REST 端点（替代原 WS-1 + dump/ocr）**：

| 方法 | 路径 | 请求 | 响应 |
|---|---|---|---|
| POST | `/api/inspector/capture` | `{serial, method: dump\|ocr\|both}` | `{status, data:{snapshot_id, elements, actionable, texts, screenshot_path, ...}}` |
| GET | `/api/inspector/snapshots?offset=&limit=` | — | `{status, data:{total, items:[...]}}` |
| GET | `/api/inspector/snapshots/{id}` | — | `{status, data:{...同 capture}}` |
| DELETE | `/api/inspector/snapshots/{id}/delete` | — | `{status, data:{deleted:true}}` |
| POST | `/api/inspector/snapshots/{id}/save-elements` | `{page_label, folder_path?, include_ocr?, element_ids?}` | `{status, data:{saved, updated, skipped, page_id}}` |
| GET | `/api/inspector/pages/{page_id}` | — | `{status, data:{label, screenshot_path, ocr_json, elements:[...]}}` |

### WS-2: 测试执行进度 `/ws/test-run/{run_id}`

| 方向 | type | 关键字段 | 触发时机 | Vue 消费 |
|---|---|---|---|---|
| 后端→前端 | `log` | `message` | 每步执行日志 | `runLogs.value.push(msg.message)` |
| 后端→前端 | `case_started` | `case_id, case_title, loop_count` | 开始执行一个用例 | `runProgress.currentCase` 更新 |
| 后端→前端 | `step_result` | `case_id, iteration, step_index, step_type, description, result` | 每个步骤执行完成 | 步骤级进度更新 |
| 后端→前端 | `iteration_result` | `case_id, iteration, result, duration_ms` | 每轮迭代完成 | `runProgress.current++`, 更新 pass/fail 计数 |
| 后端→前端 | `case_finished` | `case_id, pass, fail, rate` | 一个用例执行完毕 | `caseResults.value.push(...)` |
| 后端→前端 | `run_finished` | `summary, csv_path, log_path` | 全部用例执行完毕 | `testRunning=false`, `loadReportFiles()` |
| 后端→前端 | `device_error` | `error` | 设备连接失败 | `testRunning=false`, 弹 toast |

**Vue 相关变量**: `testWs`, `testRunning`, `testRunId`, `runProgress`, `runLogs`, `caseResults`, `reportFiles`

### WS-3: AI 助手 SSE 流式 `/agentscope/chat`

> 直连 AgentScope `:8000`，不经 Django。详见 `frontend/CLAUDE.md` ③。

| 方向 | SSE 事件 | 关键字段 | 触发时机 | Vue 消费 |
|---|---|---|---|---|
| 后端→前端 | `textGenerated` | `text` (增量) | LLM 逐 token 输出 | 追加文本到 `MessageBubble`（打字效果） |
| 后端→前端 | `toolCallStart` | `tool_name, tool_input` | Tool 开始执行 | 渲染 `ToolCallCard`（loading 态） |
| 后端→前端 | `toolCallEnd` | `tool_name, result` | Tool 执行完毕 | 更新 `ToolCallCard`（结果摘要） |
| 后端→前端 | `thinkingStart` | — | 模型推理开始 | 渲染 `ThinkingBlock`（可折叠） |
| 后端→前端 | `thinkingEnd` | — | 模型推理结束 | 折叠 `ThinkingBlock` |
| 后端→前端 | `messageEnd` | — | 消息完成 | 调 `loadConversation()` 从 DB 拉完整历史 |
| 后端→前端 | `error` | `message` | 连接/模型错误 | 显示错误提示 + 允许重试 |
| 前端→后端 | — | `POST /agentscope/stop` | 用户点"停止" | 关闭 SSE，保留已生成内容 |

**Vue 相关变量**: `sseConnection`, `streamMode` (`sse`/`fallback`), `isStreaming`, `stopGeneration()`

---

## 三、Vue 方法 → 后端依赖校验清单

### 定位元素管理页 (`currentPage === 'elements'`)

| Vue 方法 | 依赖的后端 | 校验点 |
|---|---|---|
| `connectWS()` | WS `/ws/screenshot` | `screenshotB64` 实时更新 |
| `dumpPage()` | POST `/api/elements/dump` | `allElements` 结构含 `_idx, _xpaths, _testpoint`；`lastDump.page_id` |
| `doAction('click')` | POST `/api/elements/action` | 请求体 `{action, x, y}` 字段名匹配 |
| `doInput()` | POST `/api/elements/action` | 请求体含 `clear_first` |
| `toggleTestPoint()` | 纯前端 | 不影响后端 |
| `exportYAML()` | POST `/api/cases/export/yaml` | `hasTestPoints` 由前端 `_testpoint` 标记计算 |
| `recordPage()` | PUT `/api/elements/pages/{page_id}` | 依赖 `lastDump.value.page_id` |

### 用例执行页 (`currentPage === 'runner'`)

| Vue 方法 | 依赖的后端 | 校验点 |
|---|---|---|
| `loadTestDefinitions()` | GET `/api/cases/definitions` | `testDefinitions` 需含 `steps_data`, `enabled` |
| `startTestRun()` | POST `/api/runner/run` + WS `/ws/test-run/{id}` | `case_ids` 字段名；WS URL 从 `data.ws_url` 或拼接 |
| `stopTestRun()` | POST `/api/runner/run/{id}/stop` | `run_id` 匹配 |
| `connectTestWS(runId)` | WS `/ws/test-run/{run_id}` | 6 种消息 type 的处理逻辑 |
| `loadReportFiles()` | GET `/api/reports` | `files[].name` 能用于下载链接 |

### 测试报告页 (`currentPage === 'reports'`)

| Vue 方法 | 依赖的后端 | 校验点 |
|---|---|---|
| `loadReportFiles()` | GET `/api/reports` | `files[].time, .size, .type` 字段存在 |
| `loadRunHistory()` | GET `/api/runner/runs` | `runs[].run_id, .total, .passed, .failed` |
| `viewReport(rf)` | GET `/api/reports/{filename}` | **不是 JSON** — 用 `r.text()` 而不是 `r.json()` |
| `formatSize(bytes)` | 纯前端 | 不依赖后端 |

### 测试用例页 (`currentPage === 'cases'`)

| Vue 方法 | 依赖的后端 | 校验点 |
|---|---|---|
| `loadTestDefinitions()` | GET `/api/cases/definitions` | 同上 |
| `selectCase(id)` | GET `/api/cases/definitions/{case_id}` (当列表数据不完整时) | 当前实现直接从 `testDefinitions` 数组取值，不调 API |
| `saveCurrentCase()` | POST `/api/cases/definitions` | `steps_data` 序列化为 JSON 时 `TestStep` 字段完整 |
| `deleteCurrentCase()` | DELETE `/api/cases/definitions/{case_id}` | — |
| `pasteXPathToStep()` | 纯前端 (从 `selectedXPaths` 取值) | 不调 API |

### 页面跳转页 (`currentPage === 'flows'`)

| Vue 方法 | 依赖的后端 | 校验点 |
|---|---|---|
| `loadPages()` | GET `/api/elements/pages` + GET `/api/elements/flows` (并发) | — |
| `createFlow()` | POST `/api/elements/flows` | `trigger_element_id` 可为 null |
| `deleteFlow(id)` | DELETE `/api/elements/flows/{flow_id}` | — |

---

## 四、修改校验流程

```
修改 Vue 时:
  1. 改 Vue 代码
  2. 查上表 → 确认涉及的 API/WS 端点
  3. 检查请求体字段名是否与后端一致
  4. 检查响应体字段名是否正确解构
  5. 如果新增了字段需求 → 去后端添加

修改后端时:
  1. 改 Python 代码
  2. 查上表 → 确认响应体字段名未被修改
  3. 如果改了字段名 → 搜 Vue 中所有引用该字段的地方
  4. 如果是 FileResponse → 确认前端用的是 fetch().text() 而非 api()
```

---

## 五、常见断裂点

| 问题 | 前端表现 | 原因 |
|---|---|---|
| 后端改了字段名 | 页面空白，无报错 | `data.xxx` 为 undefined |
| api() 拿到了非 JSON | 解析异常 | 后端返回了 HTML 或纯文本 |
| WS type 不匹配 | 日志不更新 | `handleTestMessage` switch 未命中 |
| 请求体字段名不一致 | `{"status":false,"message":"..."}` | 后端 `data.get("xxx")` 取不到值 |
| `api()` vs `fetch()` 混用 | 报告内容为乱码 | 报告下载是 FileResponse，须用 `r.text()` |
