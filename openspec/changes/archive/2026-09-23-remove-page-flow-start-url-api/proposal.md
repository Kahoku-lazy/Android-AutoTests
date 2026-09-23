## Why

页面流的起点节点（`StartNode`）仍保留 **URL** 与 **API** 两种模式及其参数输入框（「URL」「API 地址」），但 Web 与 API 两域已随前置变更 `remove-element-locator-web-api` 整体下线：`ApiNode` 已删、`pageCatalog` 的 Web/API 素材拉取已删、元素定位只剩 Android 一个域。起点的 URL/API 模式**既无数据来源也无消费方**——是需求变更后被替代、却未一并清理的残留。

前置变更当时把起点排除在范围外（其 proposal 只把节点类型收敛到 `PageNode` / `PopupNode` / `StartNode` / `EndNode`），本轮补上这最后一处。

## What Changes

- 前端起点模式类型 `StartKind` 由 `'app' | 'page' | 'url' | 'api'` 收敛为 `'app' | 'page'`。
- 起点节点（`PageFlowNode.vue`）删除「URL」「API」两个模式按钮与对应的「URL」「API 地址」输入框；模式区只剩「启动 App」「页面」。
- `workflowStore` 删除 `setStartUrl` / `setStartApi` 两个动作与其导出，`setStartKind` 不再写入 `start_url` / `start_api` 属性。
- 节点数据适配层（`useVueFlowAdapter.ts`）不再向节点渲染数据映射 `startUrl` / `startApi`。
- 后端 `workflow/semantics.py` 的起点摘要不再读取 `start_url` / `start_api`（`package_name` 保留）。
- **非目标**：起点「启动 App」的包名输入、起点「页面」模式的关联页面与元素输出链路均不变；AI 编译出的页面流（`start_kind=app`，见 `ai-page-flow-capture`）不变。

## 关联文档

- PRD-09（工作流工作台；需求总纲登记为「无子 PRD」）
- 前置变更：`remove-element-locator-web-api`（Web/API 域整体下线）

## Capabilities

### New Capabilities

- `page-flow-start-node`: 页面流起点节点的模式与参数契约——只允许「启动 App」（包名）与「起始页面」（关联页面 + 元素）两种模式，不得提供 URL / API 模式或承载 `start_url` / `start_api` 属性。

### Modified Capabilities

（无）

## Impact

- 前端 4 个文件：`frontend/src/modules/workflow/types/workflow.ts`、`stores/workflowStore.ts`、`composables/useVueFlowAdapter.ts`、`components/vueflow/PageFlowNode.vue`
- 后端 1 个文件：`apps/workflow/semantics.py`（起点摘要字段）
- 数据：**不改写存量数据**。已实测库中 `wf_documents` 共 2 篇、含起点节点 1 个，其 `start_kind='page'`——**不存在 `url` / `api` 取值的起点**，无需迁移
- 测试：无既有用例覆盖起点模式（`grep StartNode frontend/tests tests` 命中 0），按新增 capability 补前端单测
- 规格：新增 `page-flow-start-node`；不改 `ai-page-flow-capture`（其起点仍为 `start_kind=app`）
