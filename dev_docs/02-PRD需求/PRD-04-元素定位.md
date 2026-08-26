# PRD-04 — 元素定位 (Element Locator)

> 关联模块：`apps/element_locator/` · 前端：`frontend/src/modules/element-locator/`
> 关联全局：[`需求大纲.md`](./需求大纲.md) §5.4
> 关联上游：[`PRD-03-设备检查器`](./PRD-03-设备检查器.md)（快照数据导入 / 已保存页面只读回看）
> 关联下游：[`PRD-05-用例管理`](./PRD-05-用例管理.md)（测试点元素选取）· [`PRD-06-执行引擎`](./PRD-06-执行引擎.md)（XPath 只读消费）· [`PRD-08-AI助手`](./PRD-08-AI助手.md)（AI 保存到元素定位工具）
> 版本：v7.5 · 状态：评审中 · 日期：2026-08-21

**修订记录**

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v7.5 | 2026-08-21 | 校正 legacy 端点计数 35→36（补端点 36 import-snapshot，前端消费 ❌）；新增偏差登记「列表端点 page_elements 未返回 v7.2 快照扩展字段」；§5.3 快照字段加注写入侧返回 |
| v7.4 | 2026-08-19 | 导航重构：页内 3 Tab 改为侧边栏「元素定位」分组子项（Android元素管理 / Web端元素 / API接口），点击父项展开、点击子项进入对应页面，各自独立路由（/elements/android、/elements/web、/elements/api，/elements 重定向到 /elements/android） |
| v7.3 | 2026-08-19 | PRD/ARCH 分工回退：§4.1 移除私有实现名（`MAX_PAGE_TREE_DEPTH`/`sibling_label_exists`/page_tree.py 章名），改产品口径并指向 ARCH-04 §3.3 |
| v7.2 | 2026-08-19 | 承接设备检查器快照化改造（PRD-03 v1.7）：Android 存储扩展——`el_pages` 增加页面级 OCR JSON 与快照溯源，`el_elements` 补全 dump 完整字段（坐标/深度/缩略图等）；新增快照导入端点（自动建目录 + 页面名 + OCR JSON + 截图）；为检查器提供已保存页面只读读取；AI 保存走同一 api |
| v7.1 | 2026-08-19 | 格式对齐 PRD-03：文头补关联上下游 PRD；§5 端点总览补「前端消费」列（35 端点全 ✅）、新增错误码汇总与契约变更；§10 补 `routes.ts`、`components/ElementManager.css`；登记 DRF ViewSet 附加 detail 路由与 legacy 并存的偏差 |
| v7.0 | 2026-08-14 | 按仪表盘 PRD 格式重构：移除实现细节与已下线功能（设备元素获取/Dump/截图流/8 种 XPath 策略已迁出本模块），聚焦三域元素资产仓库 CRUD；补齐功能详细规格、布局视觉、后端功能逻辑、API 字段级契约（35 端点）、数据来源表、非功能/非目标/约束/索引；校正编号 PRD-02→PRD-04、store.js→composable、.js→.ts |
| v6.0 | 2026-07-27 | 裸 client 收敛到 api 层；GroupTreePanel 接入 Web/API |

---

## 1. 功能定位

元素定位是平台的**元素资产仓库**，集中管理三域定位信息：Android UI 元素、Web 页面元素、API 接口定义。用户在此按「页面树 / 分组树」组织元素，维护定位表达式（XPath/CSS/等）、别名、测试点标记，供用例管理与执行引擎引用。

页面由侧边栏「元素定位」分组下的 3 个子项构成：Android 元素管理 → Web 端元素 → API 接口（点击「元素定位」展开子项，点击子项进入对应页面，各自独立路由）。

**核心职责**：

- **Android 元素**：按页面树组织 UI 元素，维护 XPath 候选、别名、测试点
- **Web 元素**：按分组树组织页面元素，支持 12 种定位方式、批量导入
- **API 接口**：按分组树组织接口定义，维护请求/响应 JSON Schema
- **跳转流**：记录页面/分组间的导航流（Android + Web 两套）

> 设备发现/截图/Dump/XPath 候选生成等实时交互能力已迁出本模块（见 §8 非目标），本模块仅做**持久化元素资产的 CRUD 管理**。

---

## 2. 功能详细规格

### 2.1 Android 元素管理（F-01）

#### 2.1.1 页面树管理（F-01-01）

左侧页面树（目录 + 页面节点），支持 CRUD + 拖拽移动 + 批量移动。

| 能力 | 说明 |
|------|------|
| 目录/页面 | 节点区分 `is_folder`；目录可嵌套**最多 5 层**，页面作为叶子挂目录下 |
| 新建 | 指定 `label` + `parent_id`（仅目录下）+ `is_folder` |
| 重命名 | 同级名称唯一，冲突返回 409 |
| 删除 | 级联删除子节点与元素 |
| 移动 | 校验：不能移到自身/子级内/非目录下；目录嵌套超 5 层拦截 |
| 批量移动 | 排除「祖先也在列表」的节点，避免子项脱钩 |
| 清空 | 二次确认，级联删除全部页面/元素/流 |

**组件**：`ElementManager.vue` + `useElementTree.ts`。

**边界状态**：label 为空 400；同级重名 409；父级非目录 400；父级不存在 404；目录超 5 层 400。

**验收标准**：页面树 CRUD 完整；目录 5 层限制生效；移动校验（自身/子级/非目录）全部拦截；批量移动不脱钩。

#### 2.1.2 元素表格管理（F-01-02）

右侧元素表格（7 列：别名/XPath/class_name/text_val/resource_id/clickable/is_test_point），按页面筛选。

| 能力 | 说明 |
|------|------|
| 列表 | 按页面查询，支持 `filter`（all/clickable/text/testpoint）+ 分页（offset/limit，上限 500） |
| 添加 | 手动添加元素（alias 必填 + xpath_candidates），目录节点不可加元素 |
| 批量保存 | `elements[]` 批量 upsert，返回 saved/updated/skipped |
| 编辑 | 别名/标签/备注/测试点字段更新 |
| 去重 | 同 (page, resource_id, bounds) upsert，不创建重复记录 |
| 快照导入 | 检查器 / AI 经 `import-snapshot` 批量写入：自动创建目录路径 + 页面，页面携带截图与页面级 OCR JSON，元素携带完整 dump 字段（坐标/深度/缩略图路径等，见 §4.4） |

**组件**：`ElementManager.vue` + `useElementTree.ts`。

**边界状态**：alias 空 400；目录加元素 400；重复元素 409（upsert 提示）；快照导入目录超 5 层 / 同级重名 409。

**验收标准**：列表分页/筛选正确；批量保存返回准确计数；upsert 去重生效；快照导入后页面树出现目录/页面、页面含截图与 OCR JSON、元素字段完整。

#### 2.1.3 页面跳转流（F-01-03）

记录 Android 页面间导航流（from_page → to_page，trigger_element 触发）。

**组件**：`PageFlowViewSet`（DRF）/ `flows_handler`（legacy）。

**验收标准**：流列表展示 from/to 标签 + 触发元素；创建/删除正常。

### 2.2 Web 元素管理（F-02）

#### 2.2.1 分组树管理（F-02-01）

Web 分组树（目录 + 分组节点），结构同 Android 页面树（`WebGroup` 自引用）。

**组件**：`WebElementManager.vue` + `useWebGroupTree.ts` + 共享 `GroupTreePanel`。

**验收标准**：分组 CRUD + 批量移动；删除分组后代元素归为未分类（group=None）。

#### 2.2.2 元素表格管理（F-02-02）

Web 元素表格（name/locator_type/locator_value/page_url/description/is_test_point），支持 12 种定位方式 + JSON 批量导入。

| 定位方式（12） | css_selector / xpath / id / class_name / name / tag_name / link_text / partial_link_text / text / test_id / role / placeholder |
|------|------|

**边界状态**：name/locator_value 空 400；locator_type 非法 400；批量导入逐条校验（非法跳过）。

**验收标准**：列表按 search/locator_type/page_url/is_test_point/group_id 筛选；批量导入返回 saved/skipped。

#### 2.2.3 Web 页面跳转流（F-02-03）

Web 分组间导航流（from_group → to_group），目录节点不可作端点，触发元素须属源/目标组。

**验收标准**：目录端点拦截；触发元素归属校验。

### 2.3 API 接口管理（F-03）

#### 2.3.1 分组树管理（F-03-01）

API 分组树，结构同 Web 分组树（`ApiGroup` 自引用）。

**组件**：`ApiEndpointManager.vue` + `useApiGroupTree.ts` + `GroupTreePanel`。

#### 2.3.2 接口表格管理（F-03-02）

API 接口表格（name/method/url/headers/request_body_schema/response_body_schema/description/is_test_point），method 彩色标签（GET/POST/PUT/DELETE/PATCH），JSON 编辑器维护 headers/schema。

**边界状态**：name/url 空 400；method 非法 400。

**验收标准**：列表按 search/method/is_test_point/group_id 筛选；JSON 编辑器保存 schema。

---

## 3. 布局与视觉设计

> 颜色/字号引用 Doodle Craft 令牌（[`frontend/AGENTS.md` §2](../../frontend/AGENTS.md)）。页面图标渐变 `linear-gradient(135deg,#C9B6F2,#a78bfa)`（薰衣草紫）。

### 3.1 页面布局

```
┌─────────────────────────────────────────────┐
│ 侧边栏：「元素定位」分组（可展开，3 子项）        │
│  Android 元素管理 / Web 端元素 / API 接口      │
├─────────────────────────────────────────────┤
│ WorkbenchHeader（标题 + 副标题，随子项切换）    │
├─────────────────────────────────────────────┤
│ 左：页面树 / 分组树（GroupTreePanel）          │
│ 右：元素 / 接口表格（AppTable）                │
└─────────────────────────────────────────────┘
```

- 页面底色：点阵纸纹（`--doodle-bg` + 14px 网格点阵）
- 模块色：薰衣草紫 `--c-element` #A78BFA
- 子项切换：侧边栏分组展开/收起，子项为独立路由（刷新保持）

### 3.2 组件规格

| 元素 | 规格 |
|------|------|
| 分组树 | 左栏 300px，树形嵌套，右键菜单 + 长按拖拽 + 批选 |
| 元素表格 | AppTable + 行内编辑（别名 blur/enter 保存）+ is_test_point Switch |
| method 标签 | GET=绿 / POST=紫 / DELETE=红 等彩色标签 |
| 筛选 Tab | 全部 / 可点击 / 已命名 / 测试点 |

---

## 4. 后端功能逻辑

### 4.1 页面树层级校验

- 目录节点受 **最多 5 层** 限制，页面叶子不受限
- 移动校验：不能移到自身 / 子级内 / 非目录下；移动后子树深度不超 5 层
- 同级 label 唯一（重名 409）

> 层级校验与递归树的实现结构见 ARCH-04 §3.3。

### 4.2 元素去重（upsert）

- 同 `(page, resource_id, bounds)` 视为同一元素，`upsert_element` 更新元数据不重复创建
- 数据库 `UNIQUE(page, resource_id, bounds)` 约束兜底

### 4.3 三域对称架构

| 域 | 分组树 | 元素 | 跳转流 |
|------|------|------|------|
| Android | Page（页面树，device 关联） | Element | PageFlow |
| Web | WebGroup | WebElement | WebPageFlow |
| API | ApiGroup | ApiEndpoint | — |

三域分组树/元素 CRUD 高度对称，Web/API 共享 `GroupTreePanel` 前端组件。

### 4.4 快照导入（供检查器 / AI 调用，承接 PRD-03）

### 4.5 已知偏差登记

| 偏差 | 说明 |
|------|------|
| 列表端点 `page_elements` 未返回 v7.2 快照扩展字段 | `x`/`y`/`width`/`height`/`depth`/`index`/`scrollable`/`checked`/`thumbnail_path` 仅写入侧（add/batch 的 `_element_payload`、import-snapshot 的 `_element_dict`）返回；列表端点 `page_elements`（`views.py:424-444`）响应未含这些字段 |

---

## 5. API 接口功能

鉴权：全部端点需 JWT Bearer 鉴权。响应统一 `{status, data}` / `{status, message}`，JSON 字段 snake_case。

> 说明：本模块同时存在 **legacy Django views（前端消费）** 与 **DRF ViewSets（6 个，并行）**，前端 api.ts 走 legacy 路径（含 `/create`、`/batch`、`/batch-move` 等子路径）。

### 5.1 端点总览

| # | 方法 | 端点 | 功能 | 前端消费 |
|---|------|------|------|:--:|
| 1 | GET | `/api/elements/pages` | 列出页面（含 flow_out/flow_in 计数） | ✅ |
| 2 | POST | `/api/elements/pages/create` | 新建页面/目录 | ✅ |
| 3 | PUT | `/api/elements/pages/{page_id}` | 重命名页面 | ✅ |
| 4 | DELETE | `/api/elements/pages/{page_id}` | 删除页面（级联） | ✅ |
| 5 | POST | `/api/elements/pages/clear` | 清空全部页面/元素/流 | ✅ |
| 6 | POST | `/api/elements/pages/batch-move` | 批量移动页面 | ✅ |
| 7 | GET | `/api/elements/pages/{page_id}/items` | 页面元素列表（筛选+分页） | ✅ |
| 8 | POST | `/api/elements/pages/{page_id}/elements` | 添加元素到页面 | ✅ |
| 9 | POST | `/api/elements/pages/{page_id}/elements/batch` | 批量保存元素 | ✅ |
| 10 | PUT | `/api/elements/items/{el_id}` | 更新元素元数据 | ✅ |
| 11 | GET | `/api/elements/flows` | 列出 Android 跳转流 | ✅ |
| 12 | POST | `/api/elements/flows` | 创建跳转流 | ✅ |
| 13 | DELETE | `/api/elements/flows/{flow_id}` | 删除跳转流 | ✅ |
| 14 | GET | `/api/elements/web` | 列出 Web 元素（筛选） | ✅ |
| 15 | POST | `/api/elements/web/create` | 新建 Web 元素 | ✅ |
| 16 | PUT | `/api/elements/web/{el_id}` | 更新 Web 元素 | ✅ |
| 17 | DELETE | `/api/elements/web/{el_id}` | 删除 Web 元素 | ✅ |
| 18 | POST | `/api/elements/web/batch` | 批量导入 Web 元素 | ✅ |
| 19 | GET | `/api/elements/web-groups` | 列出 Web 分组 | ✅ |
| 20 | POST | `/api/elements/web-groups/create` | 新建 Web 分组 | ✅ |
| 21 | PUT | `/api/elements/web-groups/{group_id}` | 重命名 Web 分组 | ✅ |
| 22 | DELETE | `/api/elements/web-groups/{group_id}` | 删除 Web 分组 | ✅ |
| 23 | POST | `/api/elements/web-groups/batch-move` | 批量移动 Web 分组 | ✅ |
| 24 | GET | `/api/elements/web-flows` | 列出 Web 跳转流 | ✅ |
| 25 | POST | `/api/elements/web-flows` | 创建 Web 跳转流 | ✅ |
| 26 | DELETE | `/api/elements/web-flows/{flow_id}` | 删除 Web 跳转流 | ✅ |
| 27 | GET | `/api/elements/api-groups` | 列出 API 分组 | ✅ |
| 28 | POST | `/api/elements/api-groups/create` | 新建 API 分组 | ✅ |
| 29 | PUT | `/api/elements/api-groups/{group_id}` | 重命名 API 分组 | ✅ |
| 30 | DELETE | `/api/elements/api-groups/{group_id}` | 删除 API 分组 | ✅ |
| 31 | POST | `/api/elements/api-groups/batch-move` | 批量移动 API 分组 | ✅ |
| 32 | GET | `/api/elements/api-endpoints` | 列出 API 接口（筛选） | ✅ |
| 33 | POST | `/api/elements/api-endpoints/create` | 新建 API 接口 | ✅ |
| 34 | PUT | `/api/elements/api-endpoints/{el_id}` | 更新 API 接口 | ✅ |
| 35 | DELETE | `/api/elements/api-endpoints/{el_id}` | 删除 API 接口 | ✅ |
| 36 | POST | `/api/elements/pages/import-snapshot` | 快照导入（自动建目录+页面+元素+OCR，供检查器/AI） | ❌（本模块前端不消费，由设备检查器/AI 工具消费） |

> 36 个 legacy 端点中 35 个被前端 `api.ts` 消费（✅）；端点 36 `import-snapshot` 前端不消费（❌，由设备检查器/AI 工具消费）。DRF ViewSet（6 个）并行注册，额外生成 detail 路由（如 `PATCH /web/{pk}`、`/api-endpoints/{pk}`、`/flows/{pk}`、`/web-flows/{pk}`），前端未消费，属双视图层并行（见 C-05）。

### 5.2 页面（Page）字段

**响应 page 元素字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | number | 页面 ID |
| `device_id` | number \| null | 关联设备 |
| `parent_id` | number \| null | 父节点（树形） |
| `is_folder` | boolean | 是否目录 |
| `depth` | number | 树深度（根=1） |
| `label` | string | 名称（同级唯一） |
| `package` / `activity` | string | Android 包名 / Activity |
| `screenshot_path` | string | 截图路径 |
| `ocr_json` | JSON \| null | 页面级 OCR 结果（v7.2：检查器快照导入时写入；手动创建为 null） |
| `snapshot_id` | number \| null | 来源检查器快照 ID（v7.2 溯源，可空） |
| `element_count` | number | 元素数 |
| `flow_out` / `flow_in` | number | 出/入流计数 |
| `created_at` | string | 创建时间 |

**请求**（创建/重命名）：`label`（必填）、`parent_id`、`is_folder`、`package`、`activity`。

**响应示例**：

```json
{ "status": true, "pages": [ { "id": 1, "parent_id": null, "is_folder": false, "depth": 1, "label": "登录页", "element_count": 12 } ], "max_depth": 5 }
```

### 5.3 元素（Element）字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` / `page_id` | number | 元素 ID / 所属页面 |
| `alias` | string | 中文别名（必填） |
| `class_name` / `text_val` / `content_desc` / `resource_id` / `bounds` | string | 控件属性 |
| `xpath_candidates` | string(JSON) | XPath 候选列表 |
| `x` / `y` / `width` / `height` | number | 坐标与尺寸（v7.2，快照导入写入；⚠️ 写入侧（add/batch/import-snapshot）返回，列表端点未返回——偏差登记） |
| `depth` / `index` | number / string | 层级深度 / 兄弟索引（v7.2，快照导入写入；⚠️ 写入侧（add/batch/import-snapshot）返回，列表端点未返回——偏差登记） |
| `clickable` / `enabled` / `is_test_point` | boolean | 可点击 / 可用 / 测试点 |
| `scrollable` / `checked` | boolean | 可滚动 / 勾选态（v7.2，快照导入写入；⚠️ 写入侧（add/batch/import-snapshot）返回，列表端点未返回——偏差登记） |
| `thumbnail_path` | string | 元素缩略图路径（v7.2，快照导入写入，可空；⚠️ 写入侧（add/batch/import-snapshot）返回，列表端点未返回——偏差登记） |
| `notes` | string | 备注 |

**请求**（添加/批量）：`alias`、`xpath_candidates`（或 `xpath`）、`class_name`、`text_val`、`resource_id`、`bounds`、`clickable`、`content_desc`、`notes`；快照导入（端点 36）另含 `x` / `y` / `width` / `height` / `depth` / `index` / `scrollable` / `checked` / `thumbnail_path`。

### 5.4 Web 元素（WebElement）字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` / `group_id` / `group_name` | number / string | ID / 所属分组 |
| `name` | string | 元素名（必填） |
| `locator_type` | string | 12 种定位方式枚举 |
| `locator_value` | string | 定位表达式（必填） |
| `page_url` | string | 页面 URL |
| `description` / `tags` | string | 描述 / 标签 |
| `is_test_point` | boolean | 测试点 |
| `created_at` / `updated_at` | string | 时间戳 |

### 5.5 API 接口（ApiEndpoint）字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` / `group_id` / `group_name` | number / string | ID / 所属分组 |
| `name` | string | 接口名（必填） |
| `method` | string | GET/POST/PUT/DELETE/PATCH |
| `url` | string | 接口 URL（必填） |
| `headers` / `request_body_schema` / `response_body_schema` | JSON | 请求头 / 请求体 / 响应体 Schema |
| `description` / `tags` | string | 描述 / 标签 |
| `is_test_point` | boolean | 测试点 |

### 5.6 分组（WebGroup / ApiGroup）字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` / `parent_id` | number | ID / 父节点 |
| `name` | string | 分组名（必填） |
| `is_folder` | boolean | 是否目录 |
| `sort_order` | number | 排序权重 |
| `element_count` / `endpoint_count` | number | 子元素/接口计数 |
| `child_count` | number | 子分组计数 |

### 5.7 跳转流（PageFlow / WebPageFlow）字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | number | 流 ID |
| `from_page_id` / `to_page_id`（或 `from_group_id`/`to_group_id`） | number | 源/目标 |
| `trigger_element_id` | number \| null | 触发元素 |
| `trigger_action` | string | 触发动作（默认 click） |
| `from_label` / `to_label`（或 `from_name`/`to_name`） | string | 源/目标显示名 |
| `trigger_text` / `trigger_name` | string | 触发元素文本 |

### 5.8 错误码汇总

| 状态码 | 场景 |
|:--:|------|
| 400 | 必填字段为空（label / alias / name / locator_value / url 等）/ locator_type 或 method 非法 / 目录加元素 / 父级非目录 / 目录超 5 层 / 批量导入逐条非法（跳过） |
| 404 | 父级 / 页面 / 元素 / 分组 / 流不存在 |
| 409 | 同级重名（label / name 冲突）/ 重复元素（upsert 提示） |

### 5.9 契约变更

| 版本 | 变更 |
|------|------|
| v6.0 | 实时交互能力迁出：Dump / 截图流 / XPath 候选生成迁至设备检查器（PRD-03），本模块收敛为元素资产 CRUD |
| v7.0 | 端点总览校正为 35 端点（legacy）；字段契约补齐（Page / Element / WebElement / ApiEndpoint / 分组 / 跳转流） |
| v7.1 | 补「前端消费」列（35 全 ✅）；登记 DRF ViewSet 并行 detail 路由；无字段契约破坏 |
| v7.2 | 新增端点 36 `POST /pages/import-snapshot`（快照导入）；Page 字段 +`ocr_json` / `snapshot_id`；Element 字段 +`x/y/width/height/depth/index/scrollable/checked/thumbnail_path`；均向后兼容（默认值），不破坏既有契约 |

---

## 6. 数据来源表

| 表 | 表前缀 | 说明 |
|------|:--:|------|
| `el_pages` | el_ | 页面/目录树（Android）；v7.2 起页面可携带截图、页面级 OCR JSON（`ocr_json`）与快照溯源（`snapshot_id`） |
| `el_elements` | el_ | UI 元素（UNIQUE page+resource_id+bounds）；v7.2 起补全 dump 完整字段（坐标/深度/缩略图路径等） |
| `el_page_flows` | el_ | Android 页面跳转流 |
| `el_web_groups` | el_ | Web 分组树 |
| `el_web_elements` | el_ | Web 元素 |
| `el_web_page_flows` | el_ | Web 跳转流 |
| `el_api_groups` | el_ | API 分组树 |
| `el_api_endpoints` | el_ | API 接口定义 |

---

## 7. 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|:--:|
| 性能 | 页面列表查询 | 单查询 parent_map 避免 N+1 |
| 容量 | 页面树嵌套 | 最多 5 层目录 |
| 可靠性 | 元素去重 | UNIQUE 约束 + upsert |
| 兼容性 | 分组树 | Web/API 共享 GroupTreePanel |

---

## 8. 非目标（Non-goals）

| 不做的功能 | 原因 |
|------|------|
| 设备元素获取（截图/Dump/XPath 候选生成） | 已迁出到设备检查器（inspector）模块 |
| WebSocket 截图流 | 同迁出 |
| 8 种 XPath 策略引擎 | 同迁出（service.py 现仅 YAML 序列化） |
| 元素在设备上的实时定位验证 | 执行引擎/设备检查器负责 |

---

## 9. 关键约束速查

| 编号 | 约束 | 实施位置 |
|------|------|------|
| C-01 | 目录最多 5 层嵌套 | `page_tree.py` MAX_PAGE_TREE_DEPTH |
| C-02 | 元素去重 upsert（page+resource_id+bounds） | `api.py` + UNIQUE 约束 |
| C-03 | 写操作收敛：View/Tool → api.py → ORM | `api.py` |
| C-04 | 响应统一 `{status, data}`，snake_case | 全部端点 |
| C-05 | 双视图层共存：legacy views（前端消费）+ DRF ViewSet（并行） | `views.py` + `views_drf.py` |
| C-06 | 颜色/字号引用 Doodle Craft 令牌；图标渐变 hex 字面量 | `index.vue` |
| C-07 | 快照导入写库收敛 `api.py`（检查器 / AI Tool 只调 api，不跨模块 ORM 写） | `api.py` + `views.py` 薄层调用 |

---

## 10. 相关文件索引

| 层 | 文件 | 说明 |
|------|------|------|
| 前端 | `frontend/src/modules/element-locator/index.vue` | 3-Tab 容器 |
| 前端 | `frontend/src/modules/element-locator/routes.ts` | 路由定义 |
| 前端 | `frontend/src/modules/element-locator/api.ts` | 数据层（35 端点） |
| 前端 | `frontend/src/modules/element-locator/components/ElementManager.vue` | Android 元素管理 |
| 前端 | `frontend/src/modules/element-locator/components/ElementManager.css` | Android 元素管理样式 |
| 前端 | `frontend/src/modules/element-locator/components/WebElementManager.vue` | Web 元素管理 |
| 前端 | `frontend/src/modules/element-locator/components/ApiEndpointManager.vue` | API 接口管理 |
| 前端 | `frontend/src/modules/element-locator/composables/useElementTree.ts` | Android 页面树状态 |
| 前端 | `frontend/src/modules/element-locator/composables/useWebGroupTree.ts` | Web 分组树状态 |
| 前端 | `frontend/src/modules/element-locator/composables/useApiGroupTree.ts` | API 分组树状态 |
| 后端 | `apps/element_locator/models.py` | 8 表定义 |
| 后端 | `apps/element_locator/views.py` | legacy 视图（前端消费） |
| 后端 | `apps/element_locator/views_drf.py` | DRF ViewSets（6 个，并行） |
| 后端 | `apps/element_locator/serializers.py` | DRF 序列化器 |
| 后端 | `apps/element_locator/api.py` | 跨模块写操作白名单 |
| 后端 | `apps/element_locator/page_tree.py` | 页面树层级校验 |
| 后端 | `apps/element_locator/service.py` | YAML 序列化 |

---

## 附录A：功能边界规则

| 边界 | 规则 |
|------|------|
| 我能做什么 | 管理三域元素资产（Android/Web/API）的 CRUD、页面树/分组树、跳转流；接收检查器/AI 快照导入（自动建目录+页面+元素+页面级 OCR JSON） |
| 我不能做什么 | 设备截屏/Dump/XPath 生成（inspector）、执行用例（执行引擎）、AI 操控（AI 助手） |
| 如需越界 | 通过 api.py 向 case-manager（测试点查询）、执行引擎、dashboard、设备检查器（已保存页面只读）、AI 助手（快照保存工具）提供数据 |
| 数据可见性 | 元素资产为全平台共享库，不按用户隔离 |
