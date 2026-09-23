## Context

- 现状（代码事实）：`apps/element_locator/element_fields.py#normalize_element_fields` 只对 `primary_xpath` 做非空校验（`:80-83`），`alias` 仅受 `STRING_MAX_LENGTH` 的长度约束；新增侧 `api.py#create_element` 才校验元素名称必填。结果是「更新可以把元素名称写空，却不能把主定位写空」。
- `frontend/src/modules/element-locator/composables/usePageElements.ts#load` 成功分支无条件 `selectedIds.value = []`（`:110`），而 `updateField` 失败路径会 `await load()`（`:152-157`）——单格更新失败即清空用户已勾选的多行。
- 手动新增撞去重键时的原因是泛化文案：`api.py#create_element` 抛 `ConflictError("该元素已在当前页面中（相同 resource-id 与位置）")`，用户无法知道撞的是哪一行。
- `api.ts` 里 5 个 legacy 端点封装（`apiPageItems` / `apiUpdateElement` / `apiCreatePage` / `apiDeletePage` / `apiGetPages`）返回 `any`，调用侧只能就地断言（`usePageElements.ts:101-106`、`:183-187`、`useLocatorTree.ts:135`）。
- `useLocatorTree.ts#createdLeafId`（`:23-37`）先取 `payload.data.id`，但 `views_pages.py#create_page` 只返回 `{status, page}`（`:194`）——该分支永不命中。
- 死字段/死分支/死导出：`PageElementRow.primary_stable`（`usePageElements.ts:29,48`）零消费；`PageElementFormDialog.validate()` 只在 `primary_xpath` 非空时调 `validatePrimaryXPath`（`:71-74`），而该函数对非空恒返回 `null`；`apiGetPages`（`api.ts:77`）全仓零调用。
- `LocatorFileView` 为拿 `removeFile` 构造了整个 `useLocatorTree`（`:32`）——该 composable 只在 `loadTree()` 里请求目录树（无 `onMounted`、无 immediate watch），而 `removeFile` 删除后会 `loadTree()` 一次；此时页面已跳回目录树，这次请求的结果注定被丢弃。页面自身的树由 `getLocatorProjectTree`（`:59`）加载，因此「进入详情页只有 1 次树请求」这一事实不变，多出来的是删除路径上的无效请求。
- `LocatorFilePanel` 只被 `LocatorFileView` 以 `hide-identity` 使用（`LocatorFileView.vue:135-142`），其身份块与 `kindLabel` 从不生效；`deleteFile` 事件里的 `kind` 恒为 `'page'`（单值枚举壳）。
- 模块 `frontend/src/modules/element-locator/AGENTS.md` 为 0 字节；`tokens.css` 内留有 `/* -> --color-indigo-84 */` 自解释注释。
- 主规格现状：`openspec/specs/element-locator-element-fields/spec.md`（字段集合 / 列表响应）与 `openspec/specs/element-locator-page-workbench/spec.md`（七列呈现、双击编辑手势、元素行增删改接口契约）已由变更 `rework-save-to-elements` 同步；本次只在其上收紧必填口径与交互细节。

## Goals / Non-Goals

**Goals:**

- 元素名称在「更新」入口与「新增」入口同口径不可为空，与主定位保持一致。
- 手动新增撞去重键时的失败可被用户直接定位（文案指认既有元素）。
- 单格更新失败不再连带清空用户勾选。
- 清掉本模块零消费的死代码与死分支，并给 5 个 legacy 端点补 wire DTO 类型（消除 `any` 与就地断言）。
- 补模块 `AGENTS.md`，把信封双轨、校验防线在后端、拖拽双通道登记成模块约束。

**Non-Goals:**

- 不改 `el_elements` 表结构、唯一约束与七列呈现口径（不加 resource-id / 坐标列）。
- 不做触摸拖拽交互增强（长按反馈、边缘自动滚动）——那是交互设计变更，需独立变更。
- 不下线两条前端零调用的后端端点（`POST /api/elements/move/`、`POST /api/elements/files/batch-delete/`），见 Open Questions。
- 不引入新依赖、不改检查器快照导入链路。

## Decisions

### D1 元素名称必填放在「更新」侧，而不是放开主定位

在 `element_fields.py` 对更新入口补「元素名称非空」校验：把已填名称提交为空串 → `ValueError` → HTTP 400，且不写库；前端 `elementRowValidation` 与 `PageElementFormDialog` 同步补同口径校验。理由：主定位非空是既有的定位锚点口径（检查器保存与设备执行都依赖它），而一行没有名称在表里无法辨认——两侧都会变成「不可用状态」，因此收紧而不是放开。

备选：放开主定位可空（保持与元素名称对称）。否决——会削弱「单条主定位」写入口径，且与检查器保存路径的假设冲突。

### D2 撞去重键的报错改为「指认既有元素」，不加列

`create_element` 命中同页既有 `(page, resource_id, bounds)` 时，先取既有行的 `alias`（仅 `only("id", "alias")`）再抛 `ConflictError`，文案形如「该元素已在当前页面中：<元素名称>（id=<n>）」；既有名称为空时退化为只给 id。前端原样展示后端文案。理由：七列口径刚落地上线（`element-locator-element-fields` 明确禁止把 resource-id / 坐标作为列），加列会回退已同步的规格；一句可核对的文案即可让用户找到冲突行。

备选一：给表格加 resource-id / 坐标列。否决——与已同步规格冲突。备选二：409 返回结构化冲突详情（既有元素 id / 名称）供前端拼装。否决——只有一处消费点，属于过度设计。

### D3 勾选保留用 `load` 的可选参数实现

`usePageElements.load(options)` 增加「保留勾选」开关：默认沿用现状（清空），失败重载路径改为保留模式——只保留仍然存在于服务端返回结果中的 id。`removeSelected` 与切换页面仍清空勾选。理由：单格更新失败与「用户的勾选意图」无关；用一次 `filter` 表达，且不引入第二套列表状态。

备选：失败时只回滚被编辑的那一格，不做重载。否决——当前实现刻意用重载保证「界面与服务端一致」（防半写），回滚单元格会掩盖服务端可能已变更的其它字段。

### D4 wire DTO 落在 `types.ts`，视图模型留在 composable

在 `frontend/src/modules/element-locator/types.ts` 新增页面元素 wire DTO（元素 payload、列表响应、写入响应），`api.ts` 的 5 个 legacy 封装标上这些类型与泛型 `Envelope`；`usePageElements.ts` 的 `PageElementRow` 保持为视图模型（含 `flags` 等派生呈现），`toRow` 改以 wire DTO 为入参。理由：`frontend/AGENTS.md` 规定模块 DTO 的真相源是 `types.ts`；视图模型与 wire 形状解耦后，就地断言可以全部删掉。

备选：只在 `api.ts` 内声明并导出这些形状。否决——把 DTO 真相源分裂成两处。

### D5 文件详情页的删除不再复用 `useLocatorTree`

`LocatorFileView` 改为直接调用 `apiDeletePage(fileId)` 并在本页处理成功/失败提示，不再构造 `useLocatorTree`；目录树仍只由该页自己的 `getLocatorProjectTree` 加载。理由：为借用一个 `removeFile` 而创建整套树状态（含 project / tree / loading 与 7 个方法）既冗余，又让「删除」顺带触发一次注定被丢弃的 `loadTree()`。本页只做删除与跳转，直调端点即可。

备选：把 `removeFile` 抽成独立的 `useLocatorFileDelete`。否决——一个函数不值得一个 composable。

### D6 `LocatorFilePanel` 去掉从未生效的身份块与单值 `kind`

删除 `hideIdentity` prop、`kindLabel` 与身份 DOM/样式（全仓只有 `hide-identity` 一种用法），`deleteFile` 事件不再携带恒为 `'page'` 的 `kind`；`types.ts` 中随之无消费的 `FILE_KIND_LABELS` 一并删除，`FILE_KIND_BY_CODE` 保留（详情页找不到节点时的兜底节点仍需要 `kind`）。

备选：保留 prop 以便将来复用。否决——本仓已有的做法是删掉零调用代码（见 `purge-element-locator-dead-code`），需要时再加回成本极低。

### D7 模块 `AGENTS.md` 只写本模块增量

内容限于：模块边界（元素定位只服务 Android 单项目）、契约特例（项目/目录/移动走 `{status,data}` 信封，页面与元素走 legacy 平铺）、校验防线在后端、拖拽双通道（桌面原生 / 触摸长按 1s）、关单附加项（`--check-boundaries` 与人工验收）。不复述根 `AGENTS.md` 的通用规则。

## 模块防火墙自检

- 跨 App import：**不新增**任何跨 App import；后端改动全部落在 `apps/element_locator`，前端改动全部落在 `frontend/src/modules/element-locator/`。
- 写库收敛：`create_element` 与 `update_element` 仍在 `apps/element_locator/api.py`；`views_page_elements.py` 只做参数解析与错误码映射，不出现 View 直写 ORM 的路径。
- 前端唯一 HTTP 出口：改动仍经 `frontend/src/modules/element-locator/api.ts`（内部走 `shared/api-client`）；组件不直连 axios/fetch。
- 无新增 WS / AI / 引擎依赖；前端不直连数据库；不新增跨模块共享件。

## Risks / Trade-offs

- [收紧更新校验影响存量空名称行] → 只拒绝「把已填名称改成空串」的请求；列表照常展示历史上已为空的名称，本变更不做数据清理。
- [报错文案要带既有元素需多取一列] → 撞车判定本来就是一次存在性查询；改为取既有行的 `id` 与 `alias`（`only`），查询量级不变。
- [类型化后与实际信封不符会误导调用方] → DTO 字段以 `views_page_elements.py#_element_payload` 为唯一依据；`api.spec.ts` 钉住方法/URL/body，工作台用例钉住渲染。
- [删死代码漏掉隐式消费] → 删除前用全仓 grep 证明零引用（`apiGetPages`、`primary_stable`、`hideIdentity=false`、`payload.data.id`），删除后用 `vue-tsc` 与 `eslint` 兜底。
- [前后端不同批发布] → 后端收紧 + 前端补校验；若前端未更新，用户会先收到后端 400 中文原因，不会静默失败。

## Migration Plan

- 无数据库迁移、无配置开关、无数据回填。前后端同批发布；回滚 = 还原提交。
- 接口文档同步「更新空元素名称 → 400」与「新增撞车 409 文案指认既有元素」两条口径；路径与状态码不变，不新增端点。

## Open Questions

- 是否在后续变更里下线两条前端零调用的后端端点（`POST /api/elements/move/`、`POST /api/elements/files/batch-delete/`）：已确认仓内（前端 / 工具 / 测试 / 文档）无调用方，但无法排除平台外调用者；属 API 面收缩，留给独立变更决策。
