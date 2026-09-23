## Context

起点节点的模式与参数由四处共同决定，改一处必须四处同步，否则类型与运行时会漂移：

1. 类型真相源 `frontend/src/modules/workflow/types/workflow.ts` 的 `StartKind = 'app' | 'page' | 'url' | 'api'`
2. 状态动作 `stores/workflowStore.ts`：`setStartKind`（含 `start_url` / `start_api` 默认值写入）、`setStartUrl`、`setStartApi`
3. 画布渲染 `components/vueflow/PageFlowNode.vue`：4 个模式按钮 + 3 个参数输入框（包名 / URL / API 地址）；数据经 `composables/useVueFlowAdapter.ts` 的 `startUrl` / `startApi` 传入
4. 后端 `apps/workflow/semantics.py`：起点摘要遍历 `("package_name", "start_url", "start_api")` 输出字段

存量数据实测（MySQL，`wf_documents` 全表遍历，探针见 tasks 前的排查）：**共 2 篇文档，含起点节点 1 个，其 `start_kind='page'`；不存在 `url` / `api` 取值的起点**。该起点的 `properties` 里带有 `start_url` / `start_api` 键，但都是 `setStartKind` 无条件写入的默认值，不承载用户数据。

## Goals / Non-Goals

**Goals:**

- 起点的模式集合、参数集合、属性键、语义摘要四口径一致地收敛为「启动 App / 起始页面」。
- 存量数据不迁移、不报错（无 `url` / `api` 取值，降级路径只作为防御存在）。

**Non-Goals:**

- 不改起点「页面」模式关联页面与元素输出口的既有链路（`linkPage` / `resyncLinkedPage` / `addPort`）。
- 不改 `ai-page-flow-capture` 编译出的起点（`start_kind=app`）。
- 不清理本模块其它历史残留（如 `workflowStore.ts` 的 `initDemo`、`saveToLocal` / `loadFromLocal` / `exportAPI` / `clearAll` 等画布外的本地存储面）——另开。
- 不改后端 `semantics.py` 中 `ApiNode` 时代的 `elif node_type == "api"` 分支（不属起点范围）。

## Decisions

### D1：模式集合收敛为 `'app' | 'page'`，而非保留枚举但隐藏按钮

`StartKind` 直接收敛为两值，同时删掉两个动作与两个参数键。理由：前置变更已删除 Web/API 的全部数据来源与消费方，保留 `url` / `api` 会让它们的取值永远无法产生，属于「宁可留着」的假兼容。

**备选（未采纳）**：保留类型四值、只隐藏按钮 —— 会让 `setStartUrl` / `setStartApi` 成为零调用方的死代码，正是本变更要消除的模式。

### D2：包名输入框标签保持「包名」，不改叫「APP 名称」

用户口径为「起点只需要 APP 名称与页面」。平台内该字段的实际语义与落点是**包名**：`properties.package_name`、占位符 `com.example.app`、执行侧 `adb_start_app` 直接消费。仓库内不存在「应用名称」目录或映射表（全仓无 `app_name` 前端引用）。故按「APP 名称 = 该起点启动的那个 App 的标识（包名）」理解，只保留输入框、不改标签与字段名。

**若用户本意是把标签改为「APP 名称」**，只需改 `PageFlowNode.vue` 的 `<label>` 一处文案，与本次结构收敛无关。

### D3：历史 `url` / `api` 取值在适配层归一到 `app`

适配层把 `start_kind` 映射为 `=== 'page' ? 'page' : 'app'`，使任何非 `page` 的历史取值都落在「启动 App」分支（该分支不需要 URL/API 参数，且有完整渲染路径）。实测无此数据，此为防御性降级，**不做数据迁移**（与前置变更「不改写存量数据」一致）。

### D4：后端语义摘要删掉两个键，保留 `package_name`

`semantics.py` 的起点分支改为只读 `package_name`。删键后历史文档里残留的 `start_url` / `start_api` 键不再出现在摘要里——这正是需求「不再需要 URL 与 API 参数」在 AI 只读出口上的落点。

## 模块防火墙自检

- **跨 App import**：无新增。后端只改 `apps/workflow/semantics.py` 内部（纯函数，本就不 import 其它 App）。
- **写库路径**：无写库改动；本变更不新增任何 INSERT/UPDATE/DELETE，`semantics.py` 是只读摘要构造。
- **前端 → 后端**：不改任何 HTTP 路径、信封或字段契约；`config_json` 内的 `properties` 键由前后端各自读取，本次同步删除，不新增键。
- **前端不直连数据库**：不涉及。

## Risks / Trade-offs

- [历史文档若存在 `url` / `api` 起点，切模式后原参数丢失] → 实测不存在此类数据（`wf_documents` 2 篇 / 起点 1 个 / `start_kind='page'`）；且这两类模式已无任何可用数据来源，参数本就无意义。
- [存量 `start_url` / `start_api` 键仍留在 1 篇文档的 JSON 里] → 语义摘要已不再输出它们（D4），前端也不再读取；不改写数据以保留可回溯性。
- [类型收敛后遗漏调用方导致 `vue-tsc` 报错] → 门禁跑 `vue-tsc --noEmit` 与 `eslint`，全仓 `setStartUrl` / `setStartApi` / `startUrl` / `startApi` 引用点已在排查阶段枚举完毕（仅上述 3 个前端文件）。

## Migration Plan

1. 前端类型 / 动作 / 渲染 / 适配四文件同步收敛，后端语义摘要同步删键。
2. 门禁：`vue-tsc --noEmit`、`eslint src/`、`lint:styles`、`vitest run`、`vite build`。
3. 无数据库迁移、无接口变更，**回滚即 `git revert`**（存量数据未被改写，回滚无数据损失）。
