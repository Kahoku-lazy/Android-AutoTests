## Context

- 现状（代码事实）：`frontend/src/modules/element-locator/components/PageElementsWorkbench.vue` 用 `apiPageItems(pageId, 'all', 500)` 一次取回后整表渲染，只有别名与测试点通过 `AppTable` 的 `#cell-alias` / `#cell-test_point` 插槽可编辑；其余列只读。
- 后端 `PUT /api/elements/items/{id}/`（`views_page_elements.py#update_element`）白名单只有 `alias / tags / notes / is_test_point`；`POST /api/elements/pages/{id}/elements/`（`add_element_to_page`）要求 `alias`，按 `(page, resource_id, bounds)` **upsert**；两个端点当前**无前端调用方**。
- `Element` 唯一约束是 `(page, resource_id, bounds)`；模型列宽：`alias/class_name/resource_id/tags` 500、`text_val/content_desc` 2000、`bounds` 200、`index` 50；`x/y/width/height/depth` 为整数。
- `GET /api/elements/pages/{id}/items/` 已支持 `offset/limit`（上限 500）并返回 `total`。
- 共享件 `frontend/src/shared/composables/usePagination.ts` 已存在：默认 `pageSize=10`，提供 `pagedItems / totalPages / currentPage / goPage` 与页码夹取。
- 没有元素级删除端点（`DELETE pages/{id}/` 删的是页面）。

## Goals / Non-Goals

**Goals:**

- 元素表每页固定 10 行、可翻页；定位业务列全量行内可编辑；每格逐列校验；可新增一行；可勾选多行批量删除。
- 前端即时校验 + 后端同口径兜底，非法数据在任何入口都写不进库。

**Non-Goals:**

- 不改 `el_elements` 表结构与 `(page, resource_id, bounds)` 唯一约束（需要迁移的方案已否决）。
- 不做列排序 / 列筛选 / 行拖拽排序；不引入乐观锁或版本号。
- 不改设备检查器导入链路，不引入新依赖（分页复用共享 `usePagination`）。

## Decisions

### D1 分页在前端做，复用共享 `usePagination`

沿用现有一次取回（`limit=500`）+ `usePagination(source, { pageSize: 10 })` 本地切页：默认 10 行、上一页 / 下一页、「第 X / Y 页 · 共 N 条」，不提供行数选择器。理由：接口一次取回后编辑可即时就地更新、翻页零请求，且不重复实现分页逻辑。

备选：改用后端 `offset/limit` 分页。它能让超过 500 条的页面也完整可见，但需要新写一套服务端页码状态与每页重取，且与共享 composable 的本地切片语义冲突——本变更不要求突破 500 条上限，故不采用。

### D2 可编辑列与只读列

可编辑（走 `AppTable` 的 `#cell-*` 插槽 + 受控输入）：别名、文本、content-desc、class、resource-id、XPath、bounds、测试点、备注。只读：id、缩略图、创建时间、depth、index。`x/y/width/height` 不单列编辑，由 bounds 解析后随同一次请求写入。

### D3 校验放在共享纯函数里，两端同口径

新增 `frontend/src/modules/element-locator/helpers/elementRowValidation.ts`：每列一个纯校验函数（bounds 形状与尺寸、数字列非负整数、字符串列宽、XPath 非空），返回中文原因或 `null`。组件只做绑定与提示；后端在 api 层做同口径校验并抛 `ValueError`（→ 400）。前端校验是体验，后端校验是防线。

### D4 新增行复用既有端点，但改为 create-only

`POST /api/elements/pages/{id}/elements/` 从 upsert 改为**仅新增**：命中 `(page, resource_id, bounds)` 既有时返回 HTTP 409，而不是静默覆盖。同时补上「resource-id 与 bounds 至少一个」校验。理由：新 UI 的「+ 新增一行」语义就是新增，静默 upsert 会让用户以为加了一行、实际改了另一行；该端点当前零调用方，改动无兼容风险。

备选：保留 upsert，另加 `mode=create` 参数。多一条分支而无实际收益，暂不采用。

### D5 元素批量删除用新端点

新增 `POST /api/elements/items/batch-delete/`，body `{ids: [int]}`；api 层 `delete_elements(ids)` 整批原子删除并返回 `{deleted}`；空集合 → 400，含不存在的 id → 404 且整批不落库。备选：逐条删（无单删端点、且非原子），否决。

### D6 编辑就地更新，增删后重载并夹取页码

单格编辑成功后只更新本地该行（不整表重载，避免丢焦点）；新增 / 删除成功后重载列表并按 `total` 夹取当前页（删除后当前页可能为空 → 自动回退一页）。

### D12 可编辑单元格默认纯文本，双击进入编辑态

单元格默认只渲染纯文本，`el-input` 仅在编辑态挂载：双击进入编辑（自动聚焦），Enter 提交、Esc 取消、失焦提交，结束后回到纯文本。理由：每格常驻输入框会把表格变成一片控件海（用户实测反馈「不要这个框」），既压低可读性也让行高与列宽失控；纯文本 + 双击是按需编辑的最小交互。

备选：右键弹菜单选「编辑」——多一步且要维护一套浮层菜单，本变更不采用。

### D13 新增行弹窗用两列网格 + 顶部标签，并为错误行留足空间

**现象**：新增行弹窗里红色错误文案被下一格的输入框盖住。
**根因**（读 Element Plus 的 CSS 得到）：`.el-form-item__error` 是 `position: absolute; top: 100%; font-size: 12px`，只占用条目 `margin-bottom` 的那点空间；而我把它覆盖成了 `--app-space-sm`（= `--space-sm` = 8px），小于 12px 错误行实际所需高度，于是错误行溢出到下一行、被 DOM 中后绘制的输入框遮挡。
**修法**：弹窗改 `label-position="top"` + 两列 CSS 网格（宽度 640px；XPath 与备注通栏；body 限高 `60vh` 可滚动；顶部一行必填提示），并把 `el-form-item` 的 `margin-bottom` 提到 `--app-space-lg`（24px），使绝对定位的错误行始终有位置。
**备选**：不用 `el-form`、自己渲染标签与错误行（布局完全可控，但会丢掉 EP `is-error` 的红框反馈），本变更不采用。

## 模块防火墙自检

- 跨 App import：本设计**不新增**任何跨 App import，后端改动全部落在 `apps/element_locator`。
- 写库收敛：扩写后的 `update_element`、新增的 `delete_elements` 与新增行写入都经 `apps/element_locator/api.py`（api 层）；View 只做分发与错误码映射，不出现 View 直写 ORM。
- 前端唯一 HTTP 出口：新增封装加入 `frontend/src/modules/element-locator/api.ts`（内部走 `shared/api-client`），组件不直调 axios/fetch。
- 无新增 WS / AI / 引擎依赖；前端不直连数据库。

## Risks / Trade-offs

- [逐列校验前后端漂移] → 两端各写一份校验并用同一套规则文字；集成测试钉住后端对非法 bounds / 缺必填 / 撞唯一约束的三类拒绝。
- [500 条上限被当成「全部」] → 本地分页仍受接口 `limit` 上限；当接口返回的 `total` 大于本次取回的条数时，工作区 MUST 显式提示「仅显示前 500 条」，不假装完整。
- [并发编辑互相覆盖] → 单格按元素 id 定点更新，不整行覆盖；无版本号，同一格并发以最后一次写为准（引入乐观锁超出本变更范围）。
- [create-only 改变既有端点语义] → 该端点当前零调用方；变更后语义更严格，若将来需要 upsert 再加 `mode` 参数。
- [新增行落在最后一页] → 新增成功后重载并跳到最后一页，避免用户看不到刚加的行。
