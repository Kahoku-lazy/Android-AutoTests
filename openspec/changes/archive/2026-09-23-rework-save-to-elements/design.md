## 背景

### 检查器侧（改动前的真实事实）

- 保存入口被前端冻结：`frontend/src/modules/device-inspector/store.ts:41` `SAVE_TO_ELEMENTS_FROZEN = true`，`index.vue:71-79` 为灰键 + 提示，不发请求。
- 勾选根本没进请求体：`store.ts:301-319` 声明了 `element_ids?` 却从未赋值；`checkedIds` 存的是字符串行键 `s{seq}`。
- 保存落库口径：`apps/device_inspector/api.py:432-510` → `apps/element_locator/api_snapshot.py:132-265`，写入 18 个字段（含整屏截图复制与 `thumbnail_path`）。
- 展示保留集不含缩略图：`apps/device_inspector/service.py:100-114` 只为 `actionable` 子集写 `thumbnail_path`，而元素表数据源是全量节点索引 → 检查器缩略图列大面积为空。

### 元素定位侧：数据呈现勘测清单（本次要与之同步变更的面）

元素定位的 Web / API 两域已下线，只剩单一 Android 域，元素数据的呈现集中在六处：

| # | 呈现面 | 位置 | 现状口径 |
|---|---|---|---|
| 1 | 页面元素表 | `frontend/src/modules/element-locator/components/PageElementsWorkbench.vue` | 列：别名 / 文本 / resource-id / XPath / 坐标 / 测试点；XPath 取候选首条 |
| 2 | 新增元素行表单 | `components/PageElementFormDialog.vue` | 字段：别名(必填) / resource-id / 坐标 / class / 文本 / content-desc / XPath / 备注 / 测试点 |
| 3 | 行内编辑与行 DTO | `composables/usePageElements.ts`、`components/EditableCell.vue` | 行 DTO 含坐标四件套；`updateField` 把 `xpath` 映射为 `xpath_candidates`、`bounds` 解析为坐标 |
| 4 | 前端类型与校验 | `api.ts` 的 `PageElementFields`、`helpers/elementRowValidation.ts` | 校验列集合含 class / content-desc 列宽与 XPath 非空 |
| 5 | 后端写入白名单（唯一校验口径） | `apps/element_locator/element_fields.py` | `EDITABLE_FIELDS` 含 class / content-desc / resource-id / bounds / xpath_candidates |
| 6 | 接口返回与写入视图 | `views_page_elements.py`、`views_page_element_batch.py`、`views_snapshot.py` | 列表返回候选 XPath 字符串与页面截图路径；批量新增写 class / content-desc / 候选 |

页面级呈现（`views_pages.py` 的 `_page_payload` 返回 `screenshot_path` / `ocr_json` / `snapshot_id` / `element_count`）与只读消费方（`apps/dashboard/views.py` 元素计数、`apps/device_inspector/api.py` 按 `Element.thumbnail_path` 前缀判定媒体引用、`PageFlow.trigger_element` 外键）随本变更受影响但语义不变。

## 决策

### D1 序号口径 = 快照全量元素的坐标顺序序号（1 基）

沿用分层端点的 `seq` 定义（`algorithms/element_layers.py:331`）。前端把勾选行键由字符串 `s{seq}` 改为整数 `seq` 随请求下发；后端改为在 `snapshot.nodes_json`（全量索引）中按序号取节点，不再从 `dump_json.elements`（展示保留集）取下标。

- 备选 A「改用展示保留集 0 基下标」：否决 —— 元素表展示的是全量元素，保留集是其子集，用户勾到的行与下标无法一一对应。
- 备选 B「前端传 resource_id + bounds 复合键」：否决 —— 无 resource_id 的元素被迫用位置兜底，更脆。

### D2 越界序号返回 400，不静默丢弃

现状对非法下标是静默过滤；按「错误不应默默忽略」改为 400 并如实报出原因。快照不可变，越界只可能来自前端过期状态。

### D3 缩略图在检查器侧裁剪，元素定位只收副本

复用检查器已有的截图裁剪实现与快照整屏截图，产物落到检查器同批缩略图目录，再经 `import_snapshot_page` 复制进元素定位自有目录。

- 备选 A「元素定位侧裁剪」：否决 —— 需要重写裁剪，跨 App 复制检查器内部实现被防火墙 #1 禁止。
- 备选 B「保存时重新抓取设备截图」：否决 —— 设备可能已离开该页面，重拍会使缩略图与元素 bounds 不同源。
- 备选 C「把检查器临时缩略图路径写库（不复制）」：否决 —— 违反「元素定位 MUST NOT 引用检查器媒体路径」，删快照即破图。

### D4 字段集收敛与 `el_elements` 迁移

`import_snapshot_page` 的写入字段收敛为：`alias`、`seq`（新增）、`text_val`、`primary_xpath` + `primary_stable`（新增）、七项交互标志（`clickable`/`enabled`/`scrollable`/`checked` 已有，新增 `long_clickable`/`checkable`/`focusable`）、`thumbnail_path`，加上去重键 `resource_id` 与 `bounds`。

- 既有列（`class_name`/`content_desc`/`x`/`y`/`width`/`height`/`depth`/`index`/`xpath_candidates`）**不删**：手工新增与 AI 保存仍写它们，删列会破坏这些入口；检查器保存链路不再写这些列。
- 迁移为纯新增列（整型/字符/布尔 + 默认值），无数据回填；历史行新列为空，工作台对空值显示占位。

### D5 `import_snapshot_page` 是共用入口，两条链路同口径

`apps/ai_assistant` 的保存工具同样经 `device_inspector.api.save_snapshot_to_elements` → `import_snapshot_page`。本变更把「不落截图 + 字段集收敛」实现在该函数内，两条链路一起收敛。

- 备选「加参数区分两条链路」：否决 —— 元素定位只有一套列与一套语义，两种形状的元素记录无法一致渲染。

### D6 元素定位侧五个呈现面必须同批收敛（一次改动、五处同源）

顺序固定为：**models 列 → `element_fields.py` 白名单 → 接口与写函数 → 前端类型与校验 helper → 表列与表单**。任何一处单独改都会留下「能存不能看 / 能看不能改 / 能改存不进」的错位，这正是本次要避免的。

- 备选「只改表列、接口照旧」：否决 —— 接口仍收 class / content-desc / 候选列表，会继续产生工作台看不见的数据，字段口径再次分叉。

### D7 呈现面与落库面分离

`resource_id` 与 `bounds` 仍落库并作为 `(page, resource_id, bounds)` 唯一键参与判定，但**不作为呈现列**：它们只在「新增一行」表单中出现（新增必须提供其中之一）。类名、内容描述、坐标分量、层级、父内序号与候选 XPath 列表既不呈现、也不再由检查器写入。

- 备选「连列一起删」：否决 —— 破坏性迁移，且手工新增与 AI 链路仍在写这些列。

### D8 可编辑面 = 元素名称 / 文本 / 主定位 / 测试点

缩略图、序号、交互标注是采集产物，保持只读；这四字段与呈现列一一对应（resource-id 与坐标仅在新增表单出现）。前置变更 `element-locator-element-table-editing` 的「双击进入编辑、逐列校验、新增一行、批量删除」交互骨架全部保留，只收敛字段集合。

### D9 人工写入的主定位标记为不稳定

`primary_stable` 表达「同页唯一匹配」这一算法判定；人工输入无法做该判定，故落库时置假，避免把手写表达式冒充为已验证的稳定定位。

### D10 与在途变更 `element-locator-element-table-editing` 的顺序与基线

该变更（任务已全绿、待归档）正在修改同一批文件与同两条 `element-locator-page-workbench` 要求，其 delta 位于 `openspec/changes/element-locator-element-table-editing/specs/element-locator-page-workbench/spec.md`。

- **顺序（已满足）**：它已于 2026-09-23 归档为 `openspec/changes/archive/2026-09-23-element-locator-element-table-editing/`，主规格 `openspec/specs/element-locator-page-workbench/spec.md` 已含其分页条款与「元素行增删改接口契约」。本变更的 delta 已按归档后的主规格补齐：两条换代要求用 REMOVED + ADDED，接口契约用 MODIFIED 收窄白名单。
- **保留**：它的分页（每页 10 行）、双击行内编辑、新增一行、批量删除、逐列校验五组能力。
- **收敛**：它的「元素行增删改接口契约」里「更新接受 class / content-desc / resource-id / bounds / 候选列表」的白名单条款，按本变更 `element-locator-element-fields` 收窄为四字段，需在它归档后改写。

### D11 元素定位不再返回也不持有截图

导入路径不写页面 `screenshot_path`（恒空）；页面元素列表响应不再返回截图路径；页面级 OCR 恒空（既有口径）。工作台本就不渲染截图，故无前端可见变化；`.shot-pane` 与分段筛选的「不渲染」条款照旧成立。

### D12 历史场景名沿用：勾选跨分区与筛选保持

`device-inspector-page` 的该场景名来自已退役的「分区 + 筛选栏」页面形态（本页现已无分区与筛选）。严格校验要求 MODIFIED 块不得丢弃既有场景名，故场景名沿用历史口径、正文改为当前的「切换分组或翻页」。

### D13 「已保存页面」按整体删除处理，不留冻结壳

该功能只剩冻结入口与不可达代码（`SavedPagePicker.vue`、`viewSavedPage`、`apiGetPageView`、`GET /api/inspector/pages/{id}`），存量数据早已作废（`2026-09-22-rework-inspector-layers-view` 的冻结决定），入口恢复没有用户价值 —— 因此按「功能删除」处理：删代码、删端点、删规格要求。

- 备选「保留入口并解冻」：否决 —— 冻结原因（`analysis` 分区口径退役）从未被修复，解冻需要重做页面回看视图，而该回看只是元素定位页面的只读副本，价值低于维护成本。
- 连带删除 `element_locator.api.get_page_full` / `_element_dict`：删除后全仓无调用方（保留即死代码）。
- **不动** `el_pages` / `el_elements` 表与元素定位自身的元素表：页面资产与元素数据仍由元素定位模块承载，检查器只是不再读它们。

## 风险与权衡

- [与在途变更撞车] → 元素定位模块此刻正被另一会话修改（文件修改时间集中在 2026-09-23 12:09–12:24）；apply 前 MUST 确认该变更已归档且工作区稳定，避免双改同文件。
- [前置变更已实现的字段白名单要被收窄] → 属有意收敛：其校验纯函数与双击编辑骨架保留，只改字段集合与表单字段。
- [resource-id 与坐标不再呈现] → 用户在表中无法核对去重键；新增表单仍可填，需要时再补列即可（数据仍在库）。
- [历史 `el_elements` 行没有新列值] → 工作台对新列为空的行显示占位，MUST NOT 破版。
- [给 AI 保存链路带来的行为变化] → 见 D5；AI 侧只依赖别名与定位，收敛后语义更一致。
- [删除回看后，快照媒体保留判定的措辞仍提「页面回看」] → `device-inspector-snapshots` 的三条媒体要求未改（保留判定本身仍然成立：元素定位页面仍展示缩略图），仅「回看」措辞略旧；本次不动该 capability，避免无必要的第三条 delta。

## 门禁

- 后端：`python manage.py check`、`makemigrations --check`、**`python manage.py migrate`（必须跑：`makemigrations --check` 只证明迁移文件与模型一致，不证明 dev 库已应用；本次漏跑导致 dev 库 `Unknown column 'el_elements.seq'`，保存 500、元素表查不出数据）**、`ruff check` + `ruff format --check`、`pytest -m "unit or integration"`（含新增保存契约用例与既有媒体用例改写）
- 前端：`npm run typecheck`（报错文件集不得新增）、`npx vite build`、`npm run lint:styles`、`npx vitest run`（device-inspector 与 element-locator 两个模块）
- 规格：`npx openspec validate rework-save-to-elements --type change --strict`（前置变更归档后需重跑）
- 文档：接口文档与 PRD-03 / PRD-04 与实现同步
