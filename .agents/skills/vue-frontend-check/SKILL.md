---
name: vue-frontend-check
description: |
  Vue 前端代码校验 — 带统一判罚量规：布局裁剪、字号≥12px、硬编码色、DRF契约、展示可达性、DTO/信封、SSE/WebSocket/文件下载协议对照。强制逐项记录防同skill结果漂移。
  Keywords: Vue校验, 前端检查, DRF, API契约, 布局裁剪, 字段完整性, 展示组件, SSE, WebSocket, WS事件, 文件下载, vue check, frontend checklist, UI门禁
  Trigger: 用户表达"校验前端/检查 Vue/前端自检/UI 门禁/布局裁剪检查"，或改完 .vue / components / composable / 编辑器后要求确认是否可关单时。
---

# Vue Frontend Check — 前端代码校验门禁

**目的**: 改完 `.vue` / `components/` / composable 后自检。构建通过 ≠ 完成。

**防漂移（必读）**: 同一 skill 两次结果曾不一致 → 判罚必须以 [references/calibration.md](references/calibration.md) 为准，禁止凭感觉升降严重度。

**关联**:
- `frontend/AGENTS.md` §2（风格约束，字号最小 **12px**，禁硬编码 px）+ `frontend/src/shared/styles/tokens.css`（风格值真相源）
- `android-autotests-rules/references/frontend.md`
- 检查细表 → [references/checklist.md](references/checklist.md)
- **量规/例外/强制输出** → [references/calibration.md](references/calibration.md)

**分层口诀**：`api/` 请求对不对 → `composables/` 状态与流程对不对 → `components/` 看得见的对不对。

## 工作流

```
1. 定范围 + 声明验证方式（静态 | 静态+浏览器）
1.5 范围 >30 文件或 >3000 行 → 按「多代理执行与合并」节并行切分
2. 先跑 calibration §7 强制 rg（样式类 + 逻辑/协议类补充），再读文件三块
3. 按清单逐项给 ✅/⚠️/❌/N/A（不得只报缺陷）
4. 严重度只准查 calibration §2 表；§2 无此类别 → 先按 §9 回写量规再定级
5. 输出三块：缺陷表 + 逐项记录 + 结论（🔴 附代码原文，见 calibration §8）
```

**硬性禁止**:
- 未浏览器验证却把一.1 标 ✅（除非 calibration §3 例外且写明理由；关单仍建议浏览器确认）
- 把 `&lt;12px` 字号标成 🟡
- 只输出缺陷表、省略逐项扫描记录
- 🔴 无代码原文引用（文件:行 + ≥3 行上下文）就上报告
- 静态把一.6 判 ❌ 却未满足 calibration §3.1 全部条件
- 只查 api 层就下协议结论，不逐视图走查数据流（checklist「数据流走查」）

## 最短路径

```
改 CSS/布局           → 一.1～一.3、一.6～一.7 + 二 + 浏览器缩窗
改 components/        → 一.4～一.5 + 五（含可点击非 button）+ 三.1/三.3
改详情/列表切换       → 三.5 + 四.3 + 五.3
改 composable 传参    → 三.6
改编辑器/保存/API     → 三.7 + 四全部 + 五（若动面板）
改逻辑/协议/SSE       → 六全部（含 6.5 SSE / 6.6 文件下载 / 6.7 WebSocket）+ calibration §7 逻辑类扫描 + checklist「数据流走查」「SSE 与文件下载」「WebSocket」
改 WS 消费/推送        → 六.7 + checklist「WebSocket」+ 六.4 数据流走查
任意改动               → 六全部（每次必做，作为三.7 和四.1 的执行细则；含 6.4）
```

## 检查清单

完整清单与细则（检查项 + 怎么扫 + 通过标准 + 常见反例）→ [references/checklist.md](references/checklist.md)（**唯一真相源**）。
量规/强制扫描/输出规则 → [references/calibration.md](references/calibration.md)。
协议对照执行细则 → 本文「六、前后端协议对照」。
最短路径与多代理节引用的编号（一.1、二.5、五.10…）对应 checklist.md 的层与序号。

| 层 | 主题 |
|----|------|
| 一、模板层（P0） | 布局裁剪 / Flex 滚动区 / 字段完整性 / 截断 / 弹层 / 视图切换 |
| 二、样式层（P1） | 字号 / 颜色 / 行内 style / z-index / 圆角 / 阴影 / 间距 / 模块色 / 禁项 |
| 三、逻辑层（P2） | 四态 / 响应式 / 文案 / 空值 / 多视图互斥 / composable 入参 / 协议 |
| 四、模块级 | 契约 / 通道 / 父子选中 / 深链 / 守卫 / 体积 / 信封 / DTO / 校验 |
| 五、展示组件层 | 薄组件 / 列表 / 面板 / 危险确认 / 锁态 / emits / 可点击可达 |
| 六、协议对照（每次必做） | 路径 / 信封 / 字段 / 数据流 / SSE / 文件下载 / WebSocket |

### 六、前后端协议对照（每次必做）

> 本项是三.7 和四.1 的**执行细则**。每次校验必须逐接口做三张对照表，不得只写"已确认"。

**6.1 路径对照表**（每个前端 `api.ts` 函数 ↔ 后端 `urls.py` pattern）

| 前端函数 | HTTP 方法 | 后端路由 | 路径一致 |
|---------|:--:|---------|:--:|
| `apiXxx()` | GET/POST | `apps/xxx/urls.py` → `path(...)` | ✅/❌ |

- 如果前端 `djangoClient` 有 `baseURL`，必须拼接验证完整路径
- 遗漏端点（后端有路由但前端无调用）记 🟡 债
- 路径不一致 → 🔴

**6.2 响应信封对照表**（后端返回体 ↔ 前端解包方式）

对照前先确认后端使用哪种响应方式：

| 后端方式 | 识别特征 | 响应格式 |
|---------|---------|---------|
| DRF（`APIView` / ViewSet / `@api_view`） | 全局 `EnvelopeJSONRenderer`（`config/settings.py`）统一包装 | 2xx → `{status, data}`；异常 → `{status, message}` |
| Django `JsonResponse()`（非 DRF 视图） | 视图直接 return，不经 DRF renderer | 手动构造，格式不统一——逐处核对，不得套用 DRF 信封假设 |

- 前端解包代码必须与后端实际格式一致
- 用 `data.data.xxx` 但后端返回顶层字段 → 🔴
- 用 `data.xxx` 但后端套了 `{data: {...}}` → 🔴

**6.3 字段对照表**（后端响应字段 ↔ 前端 TS 类型属性）

逐个对照每个接口的响应字段：

| 接口 | 后端返回字段 | 前端 TS 类型属性 | 类型名 | 一致 |
|-----|-------------|-----------------|-------|:--:|
| `GET /api/xxx` | `status` | `ok` | `ScanResponse` | ❌ |
| `GET /api/xxx` | `message` | `error` | `ScanResponse` | ❌ |

重点检查：
- **字段名**：后端 `status` ↔ 前端类型是否也叫 `status`（不是 `ok`/`success` 等别名）
- **可选性**：后端 `?` 字段 ↔ 前端是否 `optional`
- **嵌套路径**：`data.data.xxx` vs `data.xxx` vs `data.payload.xxx`
- **类型不匹配**：后端 `status: boolean` 但 TS 声明 `ok: boolean` → 🔴（calibration §2）

**6.4 视图数据流走查**（每次必做，防止分层分工漏掉"解包断裂"类 🔴）

> 实测教训：主视图层代理漏掉了让整个页面失效的 `{ok,data}` 信封解包断裂，被协议层代理发现。分层扫描必须补每视图的数据流走查。

按视图逐个走查 `fetch → 解包 → 赋值 → 渲染`（细则见 checklist「数据流走查」），每步对照后端真实信封与字段名。解包字段名/嵌套不一致 → 🔴（calibration §2）。

**6.5 SSE 事件渲染对照**（改 AI 对话/SSE 时必须逐项做；细则见 checklist「SSE 与文件下载」）

| # | 检查点 | 通过标准 |
|---|--------|---------|
| 1 | 事件分派 | 每个 phase 在 `api/sse.ts` dispatch / `useSSE` 回调有消费分支；未知 phase 忽略不抛 |
| 2 | 停止生成 | 停止仅断流，已生成内容保留；旧流回调经 stale 检查失效 |
| 3 | 折叠规则 | `ThinkingBlock` / `ToolCallCard` 折叠状态独立（见 `frontend/AGENTS.md` §3 SSE） |
| 4 | 终端事件 | `reply_end` 与 `exceed_max_iters` 均触发完成；未到终端断流要报错 |

**6.6 文件下载对照**（报告/导出等 FileResponse 接口；细则见 checklist「SSE 与文件下载」）

| # | 检查点 | 通过标准 |
|---|--------|---------|
| 1 | 通道选择 | FileResponse 走 `fetch().text()`（或 blob），不套 JSON `api()` 信封解包 |
| 2 | 错误分支 | 非 2xx 读 text 并提示用户；不静默吞错 |

**6.7 WebSocket 对照**（改 WS 消费/推送时必做；细则见 checklist「WebSocket」）

| # | 检查点 | 通过标准 |
|---|--------|---------|
| 1 | URL 构建 | 经 `wsUrl('/ws/...')`（Vite 代理），禁直连后端端口 |
| 2 | 事件覆盖 | `/ws/test-run/{id}` 前端处理 9 种 type（`log` / `heartbeat` / `case_started` / `step_started` / `step_result` / `iteration_result` / `case_finished` / `run_finished` / `device_error`），每种在 `useTaskWebSocket.ts` switch 有分支；后端另发 `run_started`（前端暂不消费，新增消费时须同步 `frontend/AGENTS.md`） |
| 3 | 编辑广播 | `/ws/case-editing/{id}` 消费 `case_updated`（`group_send` 推送） |
| 4 | 断线重连 | 重连钩子生效，`_wsJustReconnected` 触发 `stepStates` 重置，无僵尸进度/重复首步 |

## 多代理执行与合并（范围 >30 文件或 >3000 行时启用）

| 层 | 范围 | 必做 |
|----|------|------|
| 协议层 | `api/*`、`shared/api-client`、`shared/sse`、后端 `urls/views/serializers/callbacks` | 六.1/6.2/6.3/6.5/6.6/6.7 对照表 + 四.1/2/7/8/9 |
| 主视图层 | 模块根 `.vue/.ts/.css` + 共享壳 | 一/二 + 三.1-5 + 四.3-6 + **六.4 数据流走查** |
| 组件层 | `components/` + `composables/` + `helpers/` | 五全部 + 三.2/3/6 + 一.4-6 |

合并规则（主审 = 发起校验者）：

1. 主审必须**亲证每个 🔴 的代码原文**后再定稿；子代理结论不得直接采信。
2. 同一缺陷多层重复发现 → 合并为一条，标注发现层。
3. 严重度争议 → 只认 calibration §2；§2 无此类 → 按 §9 回写后再定级。
4. 子代理要求：各自独立读 calibration + checklist，输出自包含三块（见 calibration §8.5）。

## 输出格式（强制三块）

```markdown
# Vue 前端校验 — {范围}

验证方式: 静态扫描 | 静态+浏览器
扫描命令: 已执行 calibration §7（是/否）

## 缺陷汇总
| # | 严重度 | 层级 | 文件 | 检查项 | 现象 | 建议 |
|---|--------|------|------|--------|------|------|
| … | 🔴/🟠/🟡 | … | path:Lxx | … | … | … |

> 规则：🔴 行必须含代码原文引用（≥3 行上下文，见 calibration §8）；🟠 至少行号+字段名/选择器。

## 逐项扫描记录
### 一、模板层
| # | 结果 | 备注 |
| 1 | ✅/⚠️/❌/N/A | … |
（二～五同理，不适用标 N/A）

## 结论
- 通过 / 有条件通过 / 不通过
- 验证方式是否满足关单：是/否
- 阻塞关单项：…
```

## 与其它 skill 分工

| 诉求 | 用哪个 |
|------|--------|
| Vue 关单门禁（本文件） | **vue-frontend-check** |
| Python 质量 | `code-health-check` |
| 功能跑测 | `functional-testing` |
| Vue 写法 | `vue` |
| 设计系统落地 | `doodle-craft` |
