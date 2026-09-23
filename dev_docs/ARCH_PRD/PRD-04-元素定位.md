# 元素定位 业务功能需求

> 版本：v1.0 · 日期：2026-09-21 · 状态：新建（对照 HEAD 实测）
> 范围：`apps/element_locator`（后端 26 条路由 + 5 张表）· `frontend/src/modules/element-locator/`（`/elements` 三个页面）
> 关联：[平台总体架构](ARCH-平台总体架构.md) · [需求总纲](PRD-需求总纲.md) · [API-元素定位](../DEV_TEST/接口文档/API-元素定位.md) · [PRD-03-设备检查器](PRD-03-设备检查器.md)
> 规格真相源：`openspec/specs/` 下的 element-locator-projects · element-locator-page-workbench · api-path-convention · frontend-l4-data-surface · frontend-l5-overlay

---

## 产品功能

> 模块在数据链路上的位置：**设备检查器 →（采集 UI 元素）→ 元素定位 →（提供元素与页面信息）→ 页面流**。
> 元素定位是平台**唯一持久的元素资产库**：按「项目 → 目录 → 页面文件 → 元素」组织，既是人工维护的定位库，也是检查器快照的落盘目标。
> **单项目约束**：2026-09-21 起 Web / API 两域整体下线，系统只剩 `android` 一个不可新建、改名、删除的项目，叶子类型只剩 `page`。

### 项目列表

#### UI交互

1. **模版** —— 一页项目卡片墙（路由 `/elements`，标题「元素定位」）：
   1. 页头 —— 标题「元素定位」，副标题「系统内置的 Android 页面与控件定位库」。
   2. 主体 —— 卡片网格，`repeat(auto-fill, minmax(280px, 1fr))`；每张卡含项目名、描述、元信息「N 个文件 · 日期」。
   3. 侧栏入口 —— `sidebarNavConfig.ts` 的 `{ path: "/elements", icon: "crosshair", label: "元素定位" }`，是可展开分组的父项。
   `ProjectList.vue` · `shared/components/sidebarNavConfig.ts`
2. **业务逻辑**
   1. 进页面即拉一次项目列表。
   2. 加载中显示骨架卡；失败显示错误条 +「重试」；成功但列表为空则显示空态「暂无元素项目 / 系统应预置 Android 项目，请稍后重试」。
   3. 卡片描述取项目自身 `description`；为空时回退到前端常量 `PROJECT_HINTS`（android = 「Android 页面与控件定位库」）；再没有则「暂无描述」。
   4. 点卡片 → 进入该项目工作台 `/elements/projects/{code}`。
   `composables/useLocatorProjects.ts` · `types.ts`
3. **样式** —— 以实际代码为准。卡片用共享件 `SketchCard`（色调与倾斜按序号轮转）；页头渐变收尾色来自模块令牌 `--locator-header-icon-end`。
   `ProjectList.vue` · `tokens.css`
4. **校验** —— 无字段级校验；本页只读。
5. **出口** —— `GET /api/elements/projects/`。
   `api.ts`（`listLocatorProjects`）

#### API契约

项目列表接口：GET api/elements/projects/

1. **入口**
   1. 方法与路径：`GET api/elements/projects/`（DRF router）；尾斜杠必须带，不带是 404。
   2. **需要登录**：全部 `/api/elements/` 端点均需 Bearer 令牌，无公开路径。
   3. 无请求字段。
   `apps/element_locator/urls.py` · `views_projects_drf.py`
2. **业务规则**
   1. **读时 seed** —— 列表读操作会顺带兜底建出缺失的系统项目，因此库里没有项目行也能拉到。
   2. **只有一个项目** —— 系统项目清单是 `(("android", "Android"),)`；已存在但名字被改过时会回写成「Android」。
   3. **只读** —— 项目不可新建 / 改名 / 删除，三个写方法一律 405。
   4. `locked` 恒为 `true`；`file_count` 取**全库**非目录页面数（不做项目过滤）。
   `api_projects.py`（`ensure_system_projects` · `serialize_project`）
3. **返回**
   1. `200` `{status: true, data}`，`data` 是恰好一项的数组；每项 `{id, code, name, description, file_count, created_at, updated_at, locked}`。
   2. `POST projects/` → `405`「系统项目不可新建」。
   3. `PATCH projects/{code}/` → `405`「系统项目不可改名」。
   4. `DELETE projects/{code}/` → `405`「系统项目不可删除」。
   5. `GET projects/{code}/` 的 `code` 不在 `android|web|api` 正则内 → 框架 404；在正则内但项目不存在（如 `web`）→ `404`「项目不存在」。
   6. 统一信封 `{status, data}` / `{status, message}`（router 端点走 `EnvelopeJSONRenderer`）。
4. **校验** —— 无字段级校验；`405` 与 `404` 是仅有的两个判定。

#### 数据表单

无表单。`el_locator_projects` 的列（本模块五张表之一）：

| 列 | 类型 | 长度 | 约束 / 说明 |
|---|---|---|---|
| `id` | BigAutoField | — | 主键 · 唯一 · 非空 |
| `code` | CharField | 20 | **唯一**；choices 只剩 `android`（迁移 0015 收窄） |
| `name` | CharField | 100 | 显示名；读时若与系统名不一致会被回写 |
| `description` | TextField | — | 默认空串 |
| `created_at` / `updated_at` | DateTimeField | — | 自动时间戳 |

> 迁移 0015 删除了 `web` / `api` 两个项目行，其目录经外键级联一并清除；页面因 `SET_NULL` 保留。

### 项目目录树工作台

#### UI交互

1. **模版** —— 一页目录树工作台（路由 `/elements/projects/:code`）：
   1. 页头 —— 标题取项目名（加载前显示「元素项目」），副标题「目录树 · 点击文件进入详情查看元素」。
   2. 面包屑 —— 「返回项目列表」+「元素定位」+ 当前项目。
   3. 树工具栏 —— 「+ 目录」与「+ 页面」（后者为主色键）；另有「批量选择」开关，开启后显示勾选计数与「移动到…」「删除」两个批量动作。
   4. 树 —— 目录可展开 / 收起，顶层目录默认全展开；行内含图标（📁 / 📂 / 📄）、名称、目录显示子节点数、文件显示「进入 ›」。
   5. 右键菜单 —— 目录节点：「+ 新建子目录」·「+ 新建页面」·「重命名」· 分隔线 ·「删除目录」；文件节点：「删除文件」。
   6. 新建 / 重命名弹窗 —— 宽 400px，单行输入（maxlength 200），回车即提交；标题按动作切「新建目录 / 重命名目录 / 新建页面」。
   `ProjectWorkspace.vue` · `components/LocatorTree.vue`
2. **业务逻辑**
   1. 进页面（或路由 code 变化）即拉项目树；code 不是已知项目 → 直接置错误「未知项目」，不发请求。
   2. **新建目录** —— 传 `project_code` + 名称 + 可选父目录；成功提示「目录已创建」并重新拉树。
   3. **新建页面** —— 传 `label` + 可选 `directory_id`；成功提示「文件已创建」，重新拉树后**直接跳进该页详情**。
   4. **重命名目录 / 删除目录 / 删除文件** —— 各自成功后提示「目录已更新」/「目录已删除」/「文件已删除」并重新拉树。
   5. **名称门槛** —— 弹窗确认时名称为空只提示「请输入目录名称」/「请输入名称」，不发请求。
   6. **删除都要二次确认** —— 删目录问「删除目录将同时删除其下全部内容，是否继续？」；删文件问「确认删除「name」？」；取消（含 ESC）不发请求。
   7. **信封兼容** —— 新建页面同时兼容 router 标准信封（`data.id`）与 legacy 平铺信封（`page.id`），两种都能取到新文件 id。
   8. 树加载失败且树为空时显示错误条 +「重试」。
   `composables/useLocatorTree.ts` · `components/LocatorTree.vue`
3. **样式** —— 以实际代码为准。本地按键 `.ex-btn` 为墨线硬边小键；树行是硬边卡片，目录行与文件行按类型区分，选中行加浅色底 + 硬阴影。
   `components/LocatorTree.vue`
4. **校验** —— 仅「名称非空」一道（前端 trim 后就地拦截）；层级、重名、循环移动等判定全在后端。
5. **出口**
   1. `GET /api/elements/projects/{code}/tree/`
   2. `POST /api/elements/directories/` · `PATCH /api/elements/directories/{id}/` · `DELETE /api/elements/directories/{id}/`
   3. `POST /api/elements/pages/create/` · `DELETE /api/elements/pages/{id}/`
   `api.ts`

#### API契约

项目树接口：GET api/elements/projects/{code}/tree/

1. **入口** —— `GET api/elements/projects/{code}/tree/`（router action），需登录，无请求字段。
2. **业务规则**
   1. 目录按 `sort_order, id` 排序；每个目录节点的 `children` = 其子目录 + 挂在该目录下的文件。
   2. 不在任何目录下的文件挂项目根；只收本项目的目录，其它项目目录下的文件不出现。
   3. 项目不存在 → `404`「项目不存在」。
   `api_projects.py`（`get_project_tree`）
3. **返回** —— `200` `{status: true, data: {project, tree}}`；
   - 目录节点：`{type:'directory', id, name, sort_order, children:[目录…, 文件…]}`
   - 文件节点：`{type:'file', kind:'page', id, name, sort_order}`
4. **校验** —— 1 条：「项目不存在」。

目录写接口：POST / PATCH / DELETE api/elements/directories/…

1. **入口**
   1. `POST api/elements/directories/`，body `{project_code, name, parent_id?, sort_order?}` → `201`。
   2. `PATCH api/elements/directories/{id}/`，body `{name?, sort_order?}` → `200`。
   3. `DELETE api/elements/directories/{id}/` → `200` `{status:true, data:{id}}`。
   `views_projects_drf.py`
2. **业务规则**
   1. **层级不限** —— 项目目录树是无限层的，创建与移动都不做深度校验，只做**循环**校验。
   2. **同级唯一** —— 数据库唯一约束 `(project, parent, name)`；撞约束翻成 `409`「同级目录名称已存在」。
   3. **名称非空** —— 去空白后为空 → `400`「目录名称不能为空」。
   4. **归属校验** —— 父目录不属于该项目 → `409`「父目录不属于该项目」；父目录不存在 → `404`「目录不存在」。
   5. **删除级联** —— 删目录会连带删除其**整棵子树**：子目录（外键级联）与其下的**页面文件、页面元素**一并删除。页面**不会**浮回项目根（`Page.directory` 虽是 `SET_NULL`，但删除前已由 api 层显式删除子树内页面，元素随 `Element.page` 的 CASCADE 删除）；整批在单个事务内完成。
   `api_directories.py` · `models.py`
3. **返回**
   1. `201` / `200` 返回 `serialize_directory`：`{id, project_id, project_code, parent_id, name, sort_order, created_at, updated_at}`。
   2. `400` 目录名称不能为空。
   3. `404` 目录不存在 / 项目不存在。
   4. `409` 同级目录名称已存在 / 父目录不属于该项目。
   5. 统一信封。
4. **校验** —— 这个端点会给出的提示：
   1.「目录名称不能为空」
   2.「项目不存在」
   3.「目录不存在」
   4.「父目录不属于该项目」
   5.「同级目录名称已存在」

移动与批量删除接口：POST api/elements/move/ · POST api/elements/batch-move/ · POST api/elements/batch-delete/ · POST api/elements/files/batch-delete/

1. **入口**
   1. `POST api/elements/move/`，body `{kind, id, parent_directory_id?, sort_order?}`（也接受 `parent_id` 作别名）。
   2. `POST api/elements/batch-move/`，body `{items:[{kind,id}], parent_directory_id?}`；目录与页面可混合，祖先已在本批集合中的后代被去重。
   3. `POST api/elements/batch-delete/`，body `{items:[{kind,id}]}`；目录与页面可混合，删除目录即删除整棵子树。
   4. `POST api/elements/files/batch-delete/`，body `{kind, ids}`（legacy，只支持 `kind=page`，当前无调用方）。
   `views_projects_drf.py`
2. **业务规则（move）**
   1. `kind='directory'`：不能移到自身 → `409`「不能将目录移动到自身」；不能移到自己的后代 → `409`「不能将目录移动到其子目录下」；跨项目 → `409`「不能跨项目移动」；同级重名 → `409`「同级目录名称已存在」；目标目录为空值即移回项目根。
   2. `kind='page'`：页面不存在 → `404`「页面不存在」；只改 `directory`，**忽略 `sort_order`**。
   3. 其它 `kind` → `400`「kind 必须是 directory / page」。
3. **业务规则（batch-move / batch-delete）**
   1. 两者都**原子**：任一节点非法则整批不落库。集合为空或 `kind` 非法 → `400`；目标目录 / 节点不存在 → `404`；非法移动（移入自身或子孙、跨项目、同级重名）→ `409`。
   2. `batch-move` 只改目录归属，不做同级排序；`batch-delete` 删除目录时连同其下子目录、页面与元素一并删除。
   3. 祖先已在本批集合中的后代被去重：已在祖先移动/删除范围内，不再单独处理。
4. **业务规则（files/batch-delete，legacy）**
   1. `ids` 为空 → `400`「ids 不能为空」；`kind` 不是 `page` → `400`「kind 必须是 page」（不支持批量删目录）。
   2. 只删非目录页面；返回的 `deleted` 是 ORM 级联删除的**对象总数**（页面 + 其下元素），不是页面条数。
5. **返回** —— `move` 回移动后的目录 JSON 或 `{kind:'page', id, directory_id}`；`batch-move` 回 `{moved, skipped}`；`batch-delete` 回 `{deleted(顶层节点数), pages(实际删除页面数), elements(实际删除元素数)}`；`files/batch-delete` 回 `{kind, deleted}`；失败为上面的 400 / 404 / 409 + 统一信封。

> **前端调用方** —— `batch-move/` 与 `batch-delete/` 已由元素定位前端（拖动、批量移动、批量删除）消费；`move/` 与 `files/batch-delete/` 仍零引用，见文末附录第 8 条。

#### 数据表单

| 表单 | 字段 | 类型 | 必填 | 约束 | 落到哪一列 |
|---|---|---|---|---|---|
| 新建目录 | `name` | 字符串 | 必填 | trim 后非空；同项目同父级下不可重名 | `el_locator_directories.name` |
| 新建目录 | `parent_id` | int | 否 | 空 = 项目根；必须属于同项目且是目录 | `el_locator_directories.parent_id` |
| 新建页面 | `label` | 字符串 | 必填 | trim 后非空；同目录下不可重名 | `el_pages.label` |
| 新建页面 | `directory_id` | int | 否 | 空 = 项目根；必须是本项目目录 | `el_pages.directory_id` |
| 重命名目录 | `name` | 字符串 | 否 | trim 后非空 | `el_locator_directories.name` |

`el_locator_directories` 的列：

| 列 | 类型 | 长度 | 约束 / 说明 |
|---|---|---|---|
| `id` | BigAutoField | — | 主键 |
| `project_id` | ForeignKey(`LocatorProject`) | — | 非空；`CASCADE` |
| `name` | CharField | 200 | 目录名 |
| `parent_id` | ForeignKey(self) | — | 可空；`CASCADE`（删父连带删子目录） |
| `sort_order` | IntegerField | — | 默认 0；与 id 一起决定排序 |
| `created_at` / `updated_at` | DateTimeField | — | 自动时间戳 |

唯一约束 `uq_el_directory_project_parent_name` = `(project, parent, name)`；索引 `idx_el_dir_proj_parent` = `(project, parent, sort_order)`。

### 页面文件详情（元素表）

#### UI交互

1. **模版** —— 一页元素表（路由 `/elements/projects/:code/files/:fileId`）：
   1. 页头 —— 标题取文件（页面）名，副标题「项目名 · 元素详情」。
   2. 面包屑 —— 元素定位 / 当前项目 / 当前文件。
   3. 面板头 —— 右上角一个「删除」键（危险色）。
   4. 元素工作台 —— 工具条「共 N 个元素」+「+ 新增一行」+「删除选中」；下面一张全宽表，列固定七项：**缩略图 · 元素名称 · 序号 · 文本 · 主定位 · 交互标注 · 测试点**；每页固定 10 行（变更 `element-locator-element-table-editing`），行勾选可整批删除。
   5. 空态 —— 「该页面暂无元素 / 可从设备检查器导入快照」。
   `LocatorFileView.vue` · `components/LocatorFilePanel.vue` · `components/PageElementsWorkbench.vue`
2. **业务逻辑**
   1. **页面元信息从项目树推导** —— 进页面先拉项目树，在树里找到该 fileId 拿到文件名与类型。
   2. **树里找不到就兜底** —— 用「文件 #id」作为临时名继续渲染，面板仍会按 id 拉元素，不因树与文件的瞬时不一致而白屏。
   3. **地址非法直接拦下** —— fileId 非正数或 code 不是已知项目 → 显示「无效的文件地址」，不发请求。
   4. **只有四个字段可改** —— 元素名称、文本、主定位（单元格双击进入编辑，Enter 提交 / Esc 或失焦取消）与测试点（行内开关）；缩略图、序号与交互标注是采集产物，保持只读（变更 `rework-save-to-elements`）。
   5. **改完就地更新** —— 保存成功后只改本行数据，不整表重载，不清空滚动位置与选中。
   6. **主定位是一等字段** —— 「主定位」列直接取元素的 `primary_xpath`（保存时按开放规格选出的那一条），页面**不再**从候选列表里另挑；手工填写的主定位落库时标记为不稳定。
   7. **不带筛选** —— 元素表**恒拉全部已保存元素**（单次上限 500），页面上没有「可点击 / 有文本 / 测试点」分段筛选，也没有截图圈选面板。
   8. 加载失败显示错误条 +「重试」；加载成功但该页没元素显示空态。
   `components/PageElementsWorkbench.vue`
3. **样式** —— 以实际代码为准。删除键与表内 EP 按键走 `.file-view` 作用域的硬边皮肤（2px 墨线 + 2px 近直角 + 2px 偏移硬阴影），删除键为危险红底 + 浅色字；元素表用共享 `AppTable` 的 SketchTable 表纸，强调色 `--c-element`、实线描边，**不外套 `el-card`**。
   `LocatorFileView.vue` · `components/PageElementsWorkbench.vue`
4. **校验** —— 与后端 `element_fields.py` 同口径：字符串列宽（元素名称 500 / 文本 2000 / 主定位 2000）、主定位非空、坐标格式 `[x1,y1][x2,y2]`；非法输入就地提示并恢复原值，不写库。
5. **出口**
   1. `GET /api/elements/pages/{page_id}/items/`
   2. `PUT /api/elements/items/{el_id}/`
   `api.ts`（`apiPageItems` · `apiUpdateElement`）

#### API契约

页面元素列表接口：GET api/elements/pages/{page_id}/items/

1. **入口**
   1. 方法与路径：`GET api/elements/pages/{page_id}/items/`；**手写路由**（无 router 对应），尾斜杠必须带。
   2. **需要登录**。
   3. 查询参数：`filter`（`all` / `clickable` / `text` / `testpoint`，其它值等同 all）、`offset`（默认 0）、`limit`（默认 100，钳制到 1–500）。
   `views_page_elements.py`
2. **业务规则**
   1. **分页参数容错不报错** —— `offset` / `limit` 非整数时**静默回退**到 0 / 100，而不是返回错误。
   2. 元素按 `id` 升序返回。
   3. 页面不存在 → `404`，文案为英文 `page not found`。
   4. 响应**不再**返回页面 `screenshot_path`，也不再返回候选 XPath 列表（元素定位不保存也不关联截图，变更 `rework-save-to-elements`）。
   `views_page_elements.py`（`page_elements`）
3. **返回** —— `200` **平铺信封** `{status: true, elements, total}`；每个元素含收敛字段：`id` · `page_id` · `alias`（元素名称） · `seq`（序号） · `text_val` · `primary_xpath` · `primary_stable` · `thumbnail_path` · 七项交互标志（`clickable` / `long_clickable` / `scrollable` / `checkable` / `checked` / `enabled` / `focusable`） · `is_test_point` · `notes` · `created_at`，以及去重键 `resource_id` · `bounds`（不呈现）。
4. **校验** —— 无字段级校验；只有「页面不存在」一条 404。

元素更新接口：PUT api/elements/items/{el_id}/

1. **入口** —— `PUT api/elements/items/{el_id}/`，需登录，body 只取传入字段。
2. **业务规则**
   1. **白名单四字段**（变更 `rework-save-to-elements`）—— 只认 `alias`（元素名称） / `text_val` / `primary_xpath` / `is_test_point`；`is_test_point` 强转布尔值，主定位写入时覆盖为单条表达式并把 `primary_stable` 置假。
   2. **越界字段被拒** —— 白名单外字段（含 `class_name` / `content_desc` / `resource_id` / `bounds` / `xpath_candidates`）回 `400`「不支持修改字段 <key>」，不再静默忽略。
   3. **存在性校验** —— 元素不存在 → `404`「元素不存在」；body 非法 JSON → `400`「无效的 JSON 请求体」。
   `views_page_elements.py`（`update_element`）· `api.py`（`update_element`）
3. **返回** —— `200` 平铺 `{status: true}`（无 data）。
4. **校验** —— 列宽（`alias` 500 / `text_val` 2000 / `primary_xpath` 2000）与主定位非空。

手动添加元素 / 批量添加元素接口：POST api/elements/pages/{page_id}/elements/ · …/elements/batch/

1. **入口** —— 两条 `POST` 手写路由，需登录；前者接单个元素，后者接 `elements` 数组。
2. **业务规则**
   1. **upsert 口径** —— 按 `(page, resource_id, bounds)` 去重：命中即更新，否则新增；新增后重算页面 `element_count`。
   2. **字段口径收敛**（变更 `rework-save-to-elements`）—— 只接受 `alias` / `text_val` / `primary_xpath` / `notes` / `is_test_point` 与去重键 `resource_id` / `bounds`；越界字段（类名、content-desc、候选列表等）按同一规整口径被拒（批量接口把该条计入 `errors` 并跳过）。
   3. **页面校验** —— 页面不存在时单条接口回 `404`「页面不存在」，批量接口回 **`400`**（同一条件两种状态码）；目录节点回 `400`「目录节点不能添加元素」。
   4. **别名必填** —— 别名为空时单条接口回 **`200`** + `{status:false, message:"元素名称(alias)必填"}`；批量接口则把该条计入 `skipped` 继续处理其余条目。
   5. 批量接口逐条 try/except，单条失败不中断整批，错误信息截断保留 5 条。
   `views_page_elements.py` · `views_page_element_batch.py`
3. **返回** —— 单条：`{status:true, updated, element}`；批量：`{status:true, saved, updated, skipped, errors?}`；均为平铺信封。
4. **校验** —— 提示共 5 条：「页面不存在」·「目录节点不能添加元素，请选择子页面」·「元素名称(alias)必填」·「elements 不能为空」·「保存元素失败，请稍后重试」。

> **前端无调用方** —— 这两条添加路径当前没有 UI 入口；页面元素的实际来源是设备检查器的快照导入，见文末附录第 8 条。

#### 数据表单

| 表单 | 字段 | 类型 | 必填 | 约束 | 落到哪一列 |
|---|---|---|---|---|---|
| 元素表 · 元素名称 | `alias` | 字符串 | 否（新增接口必填） | 列宽 500；允许空串 | `el_elements.alias` |
| 元素表 · 文本 | `text_val` | 字符串 | 否 | 列宽 2000 | `el_elements.text_val` |
| 元素表 · 主定位 | `primary_xpath` | 字符串 | 否 | 列宽 2000；非空校验；写入即 `primary_stable=false` | `el_elements.primary_xpath` · `primary_stable` |
| 元素表 · 测试点 | `is_test_point` | 布尔 | 否 | 受影响的行会被打上标记并建索引 | `el_elements.is_test_point` |
| 新增一行 · 去重键 | `resource_id` · `bounds` | 字符串 | 二者至少一个 | `bounds` 须为 `[x1,y1][x2,y2]`；与 page 组成唯一键 | `el_elements.resource_id` · `bounds`（+ 解析出的坐标分量） |
| 新增一行 · 备注 | `notes` | 字符串 | 否 | 无长度约束 | `el_elements.notes` |

`el_elements` 的列（★ 是元素表 UI 真正读写的列）：

| 列 | 类型 | 长度 | 约束 / 说明 |
|---|---|---|---|
| ★ `id` | BigAutoField | — | 主键 |
| `page_id` | ForeignKey(`Page`) | — | 非空；`CASCADE` |
| `class_name` | CharField | 500 | 默认空串；**不在呈现口径内**（检查器保存不再写入） |
| ★ `text_val` | CharField | 2000 | 默认空串；**注意与快照侧的 `text` 不同名** |
| `content_desc` | CharField | 2000 | 默认空串；不在呈现口径内 |
| `resource_id` | CharField | 500 | 默认空串；去重键之一（不呈现） |
| `bounds` | CharField | 200 | 默认空串；去重键之一（不呈现） |
| `xpath_candidates` | TextField | — | 默认 `"[]"`；已被 `primary_xpath` 取代，检查器保存不再写入 |
| ★ `primary_xpath` | CharField | 2000 | 默认空串；主定位表达式（表格列「主定位」） |
| ★ `primary_stable` | BooleanField | — | 默认 False；主定位是否稳定（人工写入恒为 False） |
| ★ `seq` | IntegerField | — | 默认 0；快照内坐标顺序序号（表格列「序号」；手工新增为 0） |
| 坐标四件套 `x` / `y` / `width` / `height` | IntegerField | — | 默认 0；检查器保存不再写入（手工新增按 bounds 解析） |
| `depth` | IntegerField | — | 默认 0；不在呈现口径内 |
| `index` | CharField | 50 | 默认空串；父内序号，不在呈现口径内 |
| ★ `clickable` / `enabled` / `scrollable` / `checked` | BooleanField | — | 默认 False；交互标注四项（表格列「交互标注」） |
| ★ `long_clickable` / `checkable` / `focusable` | BooleanField | — | 默认 False；交互标注补齐的三项 |
| ★ `thumbnail_path` | CharField | 1000 | 默认空串；元素缩略图副本路径（表格列「缩略图」） |
| ★ `alias` | CharField | 500 | 默认空串；**表格列「元素名称」** |
| `tags` | CharField | 500 | 默认空串；不呈现，仅接口预留 |
| ★ `is_test_point` | BooleanField | — | 默认 False；建索引（表格列「测试点」） |
| `notes` | TextField | — | 默认空串；不呈现列（新增表单可填） |
| `created_at` | DateTimeField | — | `auto_now_add` |

唯一约束 `uq_el_element_page_attrs` = `(page, resource_id, bounds)`。
> 原设计是 `(page, resource_id, text_val, bounds)` 四列组合，因 MySQL utf8mb4 下单索引上限 3072 字节而超限（`text_val` 是长文本），已裁到三列 —— 代码里有明确注释。

### 页面跳转流

#### UI交互

1. **模版** —— **无界面**。元素定位前端没有任何画布或流列表；页面流画布住在工作流模块，且它消费的是**页面素材**而不是流记录。
2. **业务逻辑** —— 后端提供完整的流 CRUD（列表 / 创建 / 详情 / 删除），但**产品内目前没有触发点**：前端不调，后端 `api.get_flows` / `get_or_create_flow` / `create_flow` / `delete_flow` 也全仓零调用。
3. **样式** —— 无。
4. **校验** —— 无字段级校验（除序列化器要求的两个外键必填）。
5. **出口** —— `GET|POST /api/elements/flows/` · `GET|DELETE /api/elements/flows/{id}/`。

#### API契约

页面跳转流接口：api/elements/flows/

1. **入口**
   1. `GET api/elements/flows/` 列表 · `POST api/elements/flows/` 创建 · `GET api/elements/flows/{id}/` 详情 · `DELETE api/elements/flows/{id}/` 删除。
   2. 全部需登录；`PUT` / `PATCH` 被 `http_method_names` 挡下返回 405。
   `apps/element_locator/urls.py` · `views_drf.py`
2. **业务规则**
   1. 创建走 DRF `ModelSerializer`，必填 `from_page_id` 与 `to_page_id`，可选 `trigger_element_id` 与 `trigger_action`（默认 `click`）。
   2. 列表按创建时间**倒序**，并预取起止页面与触发元素。
   3. 只读标注字段由序列化器补出：`from_label` · `to_label` · `trigger_text`。
   `serializers.py`（`PageFlowSerializer`）
3. **返回**
   1. `200` / `201` 流对象；列表为数组。
   2. `DELETE` 成功是 `204 No Content`（**无响应体**）。
   3. 缺失必填外键 → `400`，文案由 DRF 中文包产出。
4. **校验** —— 无自定义文案；DRF 序列化器错误经信封取首个字段错误作为 `message`。

#### 数据表单

| 表单 | 字段 | 类型 | 必填 | 约束 | 落到哪一列 |
|---|---|---|---|---|---|
| 页面流 | `from_page_id` | int | 必填 | 必须是存在的页面 | `el_page_flows.from_page_id` |
| 页面流 | `to_page_id` | int | 必填 | 必须是存在的页面 | `el_page_flows.to_page_id` |
| 页面流 | `trigger_element_id` | int | 否 | 元素删除后置空 | `el_page_flows.trigger_element_id` |
| 页面流 | `trigger_action` | 字符串 | 否 | 默认 `click` | `el_page_flows.trigger_action` |

`el_page_flows` 的列：`id` · `from_page_id`（CASCADE）· `to_page_id`（CASCADE）· `trigger_element_id`（SET_NULL，可空）· `trigger_action`（50，默认 click）· `created_at`。

> 页面的出向 / 入向流数量由页面列表接口用聚合算出（`flow_out` / `flow_in`），供 legacy 页面列表消费。

### 快照导入（无界面）

#### UI交互

1. **模版** —— **无界面**。真实入口在设备检查器的「保存到元素定位」弹窗，走的是检查器自己的端点；元素定位侧只暴露同进程写口与一条 HTTP 兜底路径。
2. **业务逻辑**
   1. 检查器把勾选的元素（按**坐标顺序序号**）与目标（已有页面 id 或新页面名 + 目录路径）交给 `element_locator.api.import_snapshot_page`；缩略图在检查器侧按元素 bounds 从快照截图裁好后随元素传入。
   2. 页面级 OCR 不再落库 —— 调用方恒传 `ocr_json=None`，叠加数据迁移 0014 的清空动作，`el_pages.ocr_json` 对新数据恒为空。
   3. 元素逐个按 `(page, resource_id, bounds)` upsert，别名兜底顺序 `alias` → `text` → `resource_id`；只写入收敛后的六项（缩略图 / 元素名称 / 序号 / 文本 / 主定位 / 交互标注）+ 去重键，最后重算 `element_count`。
   4. **不保存也不关联整屏截图** —— 页面 `screenshot_path` 恒为空；缩略图复制到元素定位自有目录，源缩略图缺失时该元素缩略图留空 + 告警（导入仍成功）。
3. **样式** —— 无。
4. **校验** —— 见下方契约的提示清单。
5. **出口** —— HTTP 上是 `POST /api/elements/pages/import-snapshot/`；实际调用方走同进程 `element_locator.api`。

#### API契约

快照导入接口：POST api/elements/pages/import-snapshot/

1. **入口**
   1. 方法与路径：`POST api/elements/pages/import-snapshot/`；手写路由但**采用标准 `{status, data}` 信封**（新端点新契约）。
   2. **需要登录**；`@csrf_exempt`。
   3. 请求字段：`page_label` / `folder_path` / `package` / `activity` / `ocr_json` / `snapshot_id` / `elements`（**不再接受 `screenshot_path`**，变更 `rework-save-to-elements`）。
   `views_snapshot.py` · `api_snapshot.py`
2. **业务规则**
   1. **两种模式** —— 有 `page_id` 即写入已有页面（元素 upsert 追加）；否则按 `page_label` + `folder_path` 新建页面。
   2. **目录按路径解析** —— `folder_path` 以 `/` 切段，逐级在 `android` 项目下查找或创建目录；层级上限 `MAX_DEPTH = 20`，超出 → `409`。
   3. **已有页面补全不覆盖** —— 目标页面的 OCR / `snapshot_id` 仅在自身为空时补上（截图不再参与）。
   4. **新建页面查重** —— 同级已有同名非目录页面 → `409`「同级页面「label」已存在」，由数据库唯一性裁决。
   5. **元素去重** —— 按 `(page, resource_id, bounds)` upsert，命中即更新。
   6. **不写页面级 OCR** —— `ocr_json` 传空则页面 `ocr_json` 保持空。
   `api_snapshot.py`（`import_snapshot_page` · `_resolve_folder`）
3. **返回**
   1. `200` `{status: true, data: {saved, updated, skipped, page_id}}`。
   2. `400` 无效的 JSON 请求体 / 页面名称不能为空 / 元素数据不能为空 / 目标页面不存在。
   3. `409` 同级页面已存在 / 目录最多嵌套 20 层 / Android 项目不存在 / 目标目录不存在。
   4. `500`「导入失败」（已记日志）。
4. **校验** —— 这个端点会给出的提示（按源码顺序）：
   1.「无效的 JSON 请求体」
   2.「页面名称不能为空」
   3.「元素数据不能为空」
   4.「目标页面不存在」
   5.「同级页面「{page_label}」已存在」
   6.「目录最多嵌套 20 层」
   7.「Android 项目不存在」
   8.「目标目录不存在」
   9.「导入失败」

> 接口文档把目录层级写成「5 层」（取自 `page_tree.MAX_PAGE_TREE_DEPTH`），与本法实际执行的 20 层不符 —— 本 PRD 以**代码**为准，见文末附录第 1 条。

#### 数据表单

| 表单 | 字段 | 类型 | 必填 | 约束 | 落到哪一列 |
|---|---|---|---|---|---|
| 快照导入 | `page_label` | 字符串 | 新建模式必填 | trim 后非空；同级不可重名 | `el_pages.label` |
| 快照导入 | `folder_path` | 字符串 | 否 | 按 `/` 逐段查找或创建；最多 20 层 | `el_locator_directories` |
| 快照导入 | `snapshot_id` | int | 否 | 来源检查器快照 ID，用于溯源 | `el_pages.snapshot_id` |
| 快照导入 | `elements`（数组） | 数组 | 必填（非空） | 每项含 `seq` / `alias` / `text` / `primary_xpath` / `primary_stable` / `flags`（七项交互标志）/ `resource_id` / `bounds` / `thumbnail_path` | `el_elements` |

`el_pages` 的列（★ 是元素定位 UI 真正读写的列）：

| 列 | 类型 | 长度 | 约束 / 说明 |
|---|---|---|---|
| ★ `id` | BigAutoField | — | 主键 |
| `device_id` | ForeignKey(`device_pool.Device`) | — | 可空；`SET_NULL` |
| ★ `directory_id` | ForeignKey(`LocatorDirectory`) | — | 可空；`SET_NULL`（删目录不删页面） |
| `parent_id` | ForeignKey(self) | — | 可空；`CASCADE`；**legacy 树**，新入口不再写 |
| `is_folder` | BooleanField | — | 默认 False；建索引；legacy 树遗留 |
| ★ `label` | CharField | 500 | 默认空串；建索引；页面显示名 |
| `package` / `activity` | CharField | 500 | 默认空串 |
| `screenshot_path` | CharField | 1000 | 默认空串；**新导入恒为空**（元素定位不保存也不关联截图；历史存量可能仍有值） |
| `ocr_json` | JSONField | — | 默认 `{}`；页面级 OCR **已下线**（迁移 0014 清空，新数据恒空） |
| `snapshot_id` | IntegerField | — | 可空；来源快照溯源 |
| ★ `element_count` | IntegerField | — | 默认 0；写元素后重算 |
| `created_at` | DateTimeField | — | `auto_now_add` |

索引 `idx_el_pages_parent_label` = `(parent_id, label)`。

### 跨模块消费：工作流与仪表盘读页面素材

#### UI交互

1. **模版** —— 消费发生在**别的模块的界面**上：页面流画布从元素定位取「页面素材」，仪表盘取页面/元素计数出 KPI。
2. **业务逻辑**
   1. 工作流在前端用自己的封装直调元素定位的**平铺页面接口**，拉页面列表与某页元素，用于画布的页面节点与元素列表。
   2. 仪表盘在后端**直接读模型**（跨 App 读放开）出计数，不经过 `element_locator.api`。
   3. 设备检查器**只写不读**：写经 `api.import_snapshot_page`，不直写 `el_` 表（读口 `get_page_full` 已随检查器的「已保存页面」回看功能一并删除）。
3. **样式** —— 无（消费方各自的皮肤）。
4. **校验** —— 无；沿用被调端点自身的校验。
5. **出口**
   1. `GET /api/elements/pages/` · `GET /api/elements/pages/{id}/items/`（工作流前端直调）
   2. `apps.element_locator.api.import_snapshot_page`（同进程白名单）
   `frontend/src/modules/workflow/api.ts` · `apps/dashboard/views.py` · `apps/device_inspector/api.py`

#### API契约

页面平铺列表接口：GET api/elements/pages/

1. **入口** —— `GET api/elements/pages/`，需登录，无请求字段（注释提到的 `offset/limit` 未实现）。
2. **业务规则**
   1. 一次返回**全部**页面与目录节点（`is_folder` 参与排序），不做分页。
   2. 每行用单查询父级映射算出 `depth`，避免 N+1；并聚合出 `flow_out` / `flow_in`。
   3. 排序：`is_folder` → `label` → `created_at` 倒序。
   4. **无项目 / 用户过滤** —— 返回全库页面。
   `views_pages.py`（`list_pages` · `_page_payload`）
3. **返回** —— `200` 平铺 `{status: true, pages: [...], max_depth: 5}`；每行含 `id` · `device_id` · `parent_id` · `is_folder` · `depth` · `label` · `package` · `activity` · `screenshot_path` · `ocr_json` · `snapshot_id` · `element_count` · `created_at` · `flow_out` · `flow_in`。
4. **校验** —— 无。

#### 数据表单

无表单、不写库；只读 `el_pages` / `el_elements`。跨模块消费面共三处（工作流前端、仪表盘、检查器）。

### 失败呈现与重试

> 这一节不是端点，是「页面上的每次请求失败怎么被看见、怎么被重发」，横跨上面各功能。

#### UI交互

1. **模版** —— 三个页面各自渲染共享的 `ErrorState` 错误条（含「重试」键）；写操作则走 `ElMessage` 轻提示。
2. **业务逻辑**
   1. **读失败上错误条** —— 项目列表、目录树、文件详情的加载失败都显示错误条 + 重试，重试就是重发对应的那一个请求。
   2. **写失败只弹提示** —— 建 / 改 / 删目录与文件、改别名与测试点，失败只弹一条 `ElMessage.error`，不挂常驻错误条、不提供重试键（重试入口就是用户手里的那个按钮）。
   3. **文案口径** —— 信封失败取 `data.message`，为空时用兜底语（「创建目录失败」/「更新失败」/「删除失败」/「创建文件失败」等）；抛出异常过共享净化 `formatApiError`。
   4. **列表页失败即清空** —— 项目列表与页面元素加载失败时会把已有数据清成空数组，只保留错误提示。
   `composables/useLocatorProjects.ts` · `composables/useLocatorTree.ts` · `components/PageElementsWorkbench.vue` · `LocatorFileView.vue`
3. **样式** —— 以实际代码为准（共享件，本模块不改其外观）。
4. **校验** —— 无。
5. **出口** —— 按失败点重发对应的 `api.ts` 函数。

#### API契约

本节不新增端点；约束落在各端点的 `message` 质量与前端 `formatApiError` 的净化口径上。

#### 数据表单

错误状态只存在前端组件内（`error` 字符串 ref），不持久化。

---

## 测试

> 本模块各功能的测试资产按功能分节登记；逐条用例文档见 `dev_docs/DEV_TEST/`。
> **现状**：本模块的自动化由**灰盒结构性门禁 + 前端 API 契约表**两层构成，**接口层（`tests/api`）与端到端层均为 0**，且灰盒用例**没有一条断言业务行为**。

### 项目列表

1. **业务场景** —— 从功能出发；每条末尾的【】标出它覆盖了哪一项。

   **UI交互侧**
   - 单项目卡片【模版 2 · 业务逻辑 4】—— WHEN 打开 `/elements` → THEN 只出现一张 android 项目卡，点它进入该项目工作台
   - 描述回退【业务逻辑 3】—— WHEN 项目描述为空 → THEN 卡片显示「Android 页面与控件定位库」
   - 加载中 / 失败 / 空态【业务逻辑 2】—— WHEN 加载中 → 骨架卡；WHEN 失败 → 错误条 + 重试；WHEN 成功但为空 → 「暂无元素项目」

   **业务功能侧**
   - 读时 seed【业务规则 1】—— WHEN 库里没有项目行 → THEN 列表读操作自动建出 android 项目并返回
   - 单项目【业务规则 2】—— WHEN 请求项目列表 → THEN 恰好返回一项，code 为 android
   - 不可变【业务规则 3】—— WHEN 对项目发 POST / PATCH / DELETE → THEN 一律 `405` 且文案为中文

   > **对应规格**：`openspec/specs/element-locator-projects`（System locator projects · 两个 Scenario）

2. **测试用例** —— 接口层**无自动化**（`tests/api` 下没有本模块的用例文件与 YAML）。

3. **自动化覆盖的测试用例**
   - `tests/graybox/unit/test_element_locator_views_split.py` —— `ROUTER_ROUTES` 逐条解析 `projects/` · `directories/` · `flows/` 断言仍由对应 ViewSet 处理（**路由契约**，非行为）
   - `frontend/tests/element-locator/p0/api.spec.ts` —— `listLocatorProjects` 断言 `GET /elements/projects/` 且恰好调用一次
   - **缺口：405 的文案、读时 seed、空库行为、卡片渲染全部零覆盖。**

### 项目目录树工作台

1. **业务场景**

   **UI交互侧**
   - 树与面包屑【模版 2 · 3】—— WHEN 打开 `/elements/projects/android` → THEN 页头显示项目名、面包屑可回项目列表、树渲染目录与页面
   - 新建目录【业务逻辑 2】—— WHEN 从工具栏「+ 目录」输入名称确认 → THEN 提示「目录已创建」且树里出现该目录
   - 新建页面并直达【业务逻辑 3】—— WHEN 从右键「+ 新建页面」输入名称确认 → THEN 提示「文件已创建」并跳进该页详情
   - 重命名 / 删除目录【业务逻辑 4 · 6】—— WHEN 右键重命名或删除 → THEN 前者弹单行输入、后者先弹二次确认；取消不发请求
   - 名称门槛【业务逻辑 5】—— WHEN 弹窗里名称留空点确定 → THEN 只提示「请输入目录名称」/「请输入名称」，不发请求
   - 空态【模版】—— WHEN 项目下还没有任何目录与文件 → THEN 树区显示「暂无目录或文件 / 点击上方按钮开始组织定位资产」
   - 未知项目【业务逻辑 1】—— WHEN 路由 code 不是已知项目 → THEN 显示「未知项目」，不发请求

   **业务功能侧**
   - 无限层目录【业务规则 1】—— WHEN 连续建多层子目录 → THEN 都成功，不受深度限制
   - 同级唯一【业务规则 2】—— WHEN 同项目同父级下建同名目录 → THEN `409`「同级目录名称已存在」
   - 名称非空【业务规则 3】—— WHEN 名称只有空白 → THEN `400`「目录名称不能为空」
   - 归属校验【业务规则 4】—— WHEN 父目录不属于该项目 → `409`；父目录不存在 → `404`
   - 循环移动【业务规则（move）2】—— WHEN 把目录移到自己的后代下 → THEN `409`「不能将目录移动到其子目录下」
   - 删除级联边界【业务规则 5】—— WHEN 删除一个含子目录与页面的目录 → THEN 子目录与其下页面、元素一并被删除，页面**不浮回项目根**
   - 批量删除【业务规则（batch-delete）】—— WHEN 勾选多个目录与页面并确认删除 → THEN 整批原子删除，删除目录连同其下内容，成功后清空勾选

   > **对应规格**：`element-locator-projects`（Project workspace tree · 两个 Scenario，另加拖拽移动 / 批量勾选移动 / 批量勾选删除 / 删除目录级联 / 批量删除接口契约五条新增需求）

2. **测试用例** —— 接口层**无自动化**。

3. **自动化覆盖的测试用例**
   - `tests/graybox/unit/test_element_locator_views_split.py` —— 12 条 legacy 路由与 4 条 router 路由解析、视图模块行数预算（≤300）、单文件 `views.py` 已删（**结构性门禁**）
   - `tests/graybox/unit/test_element_locator_group_writes_removed.py` —— 4 个已删视图模块不存在、8 个 api 原语不在白名单、7 条退役路径与 4 条原「分组写」路径一律 404（**结构性门禁**）
   - `frontend/tests/element-locator/p0/api.spec.ts` —— 目录增删改三个封装的 URL / 方法 / 调用次数
   - **缺口：重名 409、循环移动 409、名称非空 400、「删目录不删页面」这条关键边界，以及目录树组件的所有渲染/交互，全部零覆盖。**

### 页面文件详情（元素表）

1. **业务场景**

   **UI交互侧**
   - 只展示元素表【模版 4 · 业务逻辑 7】—— WHEN 打开一个页面文件 → THEN 主区只有元素表，无截图圈选面板、无「全部 / 可点击 / 有文本 / 测试点」分段筛选
   - 列齐全【模版 4】—— WHEN 表渲染 → THEN 六列同时存在：别名 / 文本 / resource-id / XPath / 坐标 / 测试点
   - 全量不筛【业务逻辑 7】—— WHEN 该页含不可点击、无文本、未标测试点的元素 → THEN 它们同样出现在表里，工具条计数与行数一致
   - 别名可改可持久【业务逻辑 4 · 5】—— WHEN 改某行别名且请求成功 → THEN 该行立即显示新值，刷新后仍是新值
   - 测试点可切换【业务逻辑 4 · 5】—— WHEN 切换某行测试点开关 → THEN 立即生效并落库
   - 只读字段【业务逻辑 4】—— WHEN 查看文本 / resource-id / XPath / 坐标 → THEN 均不可编辑
   - XPath 取首个候选【业务逻辑 6】—— WHEN 元素有多个 XPath 候选 → THEN 只展示第一条；无候选显示「—」
   - 树兜底不白屏【业务逻辑 2】—— WHEN 项目树里暂时找不到该文件 → THEN 用「文件 #id」占位继续拉元素
   - 地址非法【业务逻辑 3】—— WHEN fileId 非正数或 code 未知 → THEN 显示「无效的文件地址」，不发请求
   - 加载失败可重试【业务逻辑 8】—— WHEN 元素列表请求失败 → THEN 显示中文错误 + 重试，**不静默清空后假装成功**
   - 空态【模版 5】—— WHEN 该页没有元素 → THEN 显示「该页面暂无元素 / 可从设备检查器导入快照」

   **业务功能侧**
   - 列表全量返回【业务规则 1 · 2】—— WHEN 请求某页元素 → THEN 按 id 升序返回该页全部元素（受 limit 上限约束）并带 `total`
   - 分页容错【业务规则 1】—— WHEN `offset` / `limit` 传非整数 → THEN 静默回退 0 / 100，不报错
   - limit 钳制【入口 3】—— WHEN `limit=9999` → THEN 实际最多返回 500 条
   - 白名单更新【业务规则（PUT）1】—— WHEN 传 `alias` / `is_test_point` → THEN 落库；传白名单外字段 → THEN 被忽略、不报错
   - 页面不存在【业务规则（列表）3】—— WHEN page_id 不存在 → THEN `404`，文案为英文 `page not found`

   > **对应规格**：`element-locator-page-workbench`（全宽元素表 · 字段可编辑 · 加载失败可见 · 硬边皮肤与表纸）

2. **测试用例** —— 接口层**无自动化**。

3. **自动化覆盖的测试用例**
   - `frontend/tests/element-locator/p0/api.spec.ts` —— 2 条：`apiPageItems` 的 `GET /elements/pages/1/items/`、`apiUpdateElement` 的 `PUT /elements/items/1/`
   - `tests/graybox/unit/test_element_locator_drf_writes.py` —— 1 条：`views_drf` 内不得出现 `serializer.save()`（**写库收敛**，与本页无关）
   - **缺口：列渲染、行内编辑与落库、XPath 首候选、无筛选、加载失败可见、limit 钳制、白名单更新全部零覆盖。**

### 页面跳转流

1. **业务场景**

   **业务功能侧**
   - 建流【业务规则（创建）1】—— WHEN 传两个存在的页面 id → THEN 建出一条流并返回 201
   - 列表倒序【业务规则（列表）2】—— WHEN 请求列表 → THEN 按创建时间倒序，且带 `from_label` / `to_label` / `trigger_text`
   - 删流【返回 2】—— WHEN 删除一条流 → THEN `204 No Content`（无响应体）
   - 方法限制【入口 2】—— WHEN 对 `flows/{id}/` 发 `PUT` / `PATCH` → THEN `405`

2. **测试用例** —— 接口层**无自动化**。

3. **自动化覆盖的测试用例**
   - `tests/graybox/unit/test_element_locator_views_split.py` —— `flows/` 与 `flows/1/` 仍由 `PageFlowViewSet` 处理（路由护栏，注释明写「删 legacy 没删掉能力」）
   - **缺口：建流 / 列表倒序 / 204 无体 / 方法限制零覆盖；且该能力本身无产品消费方（见附录第 8 条）。**

### 快照导入

1. **业务场景**

   **业务功能侧**
   - 新建页面并写元素【业务规则 1 · 5】—— WHEN 传新页面名与一批元素 → THEN 建出页面与其元素，返回 `{saved, updated, skipped, page_id}`
   - 写入已有页面【业务规则 3】—— WHEN 传 `page_id` → THEN 元素 upsert 追加，页面截图 / OCR / `snapshot_id` 仅在为空时补全
   - 目录按路径建【业务规则 2】—— WHEN `folder_path` 是多层且目录不存在 → THEN 逐级创建后挂接
   - 目录层级超限【业务规则 2】—— WHEN 路径超过 20 层 → THEN `409`「目录最多嵌套 20 层」
   - 同级重名【业务规则 4】—— WHEN 新建模式下同级已有同名页面 → THEN `409`「同级页面「label」已存在」
   - 页面级 OCR 不落库【业务规则 6】—— WHEN 用历史含 OCR 的快照导入 → THEN 目标页面 `ocr_json` 为空
   - 元素去重【业务规则 5】—— WHEN 同 `(page, resource_id, bounds)` 再次导入 → THEN 更新而非新增
   - body 非法【校验 1】—— WHEN 请求体不是合法 JSON → THEN `400`「无效的 JSON 请求体」

   > **对应规格**：本能力由 `element-locator-projects` 的「Leaf identity preserved on migration」间接约束（迁移后页面 id 与其元素仍可读）。

2. **测试用例** —— 接口层**无自动化**（`tests/api` 既没有 `elements.yaml`，也没有驱动脚本）。

3. **自动化覆盖的测试用例**
   - 无直接覆盖。**缺口：整个导入链路的 9 条文案与「目录 20 层 vs 文档 5 层」的口径差异都没有断言。**
   - 唯一的间接守护是设备检查器侧的 TC-INS-060（保存到元素定位时快照不存在 → `400`），它只走到检查器的入口校验就返回了，**没有进入 `import_snapshot_page`**。

### 跨模块消费：工作流与仪表盘读页面素材

1. **业务场景**

   **业务功能侧**
   - 工作流取页面素材【业务逻辑 1】—— WHEN 页面流画布需要页面列表 → THEN 直调页面平铺接口拿到全量页面
   - 工作流取某页元素【业务逻辑 1】—— WHEN 需要某页元素 → THEN 直调该页 items 接口
   - 仪表盘出计数【业务逻辑 2】—— WHEN 渲染 KPI → THEN 直接读 `Page` / `Element` 模型，不经 api 白名单
   - 检查器写库收敛【业务逻辑 3】—— WHEN 检查器要写元素 → THEN 只经 `element_locator.api.import_snapshot_page`

2. **测试用例** —— 无专有自动化。

3. **自动化覆盖的测试用例**
   - `frontend/tests/element-locator/p0/api.spec.ts` —— 覆盖 `apiGetPages` 的 `GET /elements/pages/`（**注意：该封装本身在本模块内也没有 UI 调用方**）
   - **缺口：工作流前端自己的两个封装、仪表盘计数、检查器读写收敛均无专有断言。**

### 失败呈现与重试

1. **业务场景**

   **UI交互侧**
   - 读失败有错误条【业务逻辑 1】—— WHEN 项目列表 / 目录树 / 文件详情加载失败 → THEN 出现错误条与「重试」，点重试重发该请求
   - 写失败只弹提示【业务逻辑 2】—— WHEN 建目录 / 改名 / 删目录 / 建文件 / 删文件 / 改别名 / 改测试点失败 → THEN 只弹一条提示，不挂常驻错误条
   - 文案取后端【业务逻辑 3】—— WHEN 后端信封带 `message` → THEN 原样呈现；没有则用兜底语
   - 列表失败即清空【业务逻辑 4】—— WHEN 项目列表请求失败 → THEN 卡片区清空，只留错误提示

2. **测试用例** —— 无。

3. **自动化覆盖的测试用例**
   - 无。**缺口：本模块的错误呈现与重试没有任何自动化断言**（对比设备检查器有专门的 P0 用例守这一面）。

### 怎么跑这些测试

```
python -m pytest tests/graybox/unit/test_element_locator_views_split.py tests/graybox/unit/test_element_locator_group_writes_removed.py tests/graybox/unit/test_element_locator_drf_writes.py -q   # 本模块灰盒门禁（3 文件 / 42 条）
python -m pytest tests/graybox/unit -q                    # 灰盒单元层全量
python -m pytest tests/arch/test_view_write_convergence.py -q   # 写库收敛（Element 也在守护面内）
cd frontend && node tests/run.mjs module element-locator  # 前端元素定位 P0（1 个文件 / 10 条）
```

> **接口层与端到端层对本模块零覆盖**：`tests/api` 没有元素定位的脚本与 YAML，`tests/e2e` 只有登录模块的用例。

---

## 附录：已知缺口

1. **接口文档严重滞后，且不止是「几处反了」** —— `dev_docs/DEV_TEST/接口文档/API-元素定位.md` 共 1277 行，其中 **117 处**仍在描述已整体下线的 Web / API 两域（`web-groups` / `api-endpoints` / `web-flows` / `/api/elements/web/` / 「三项目」）。文档抬头写「系统三项目（Android / Web / API）」、「分组写 → 410」，而代码里这些路由**根本不存在**（子路径一律 404，不是 410）。文档还引用了失效路径 `dev_docs/05-开发与测试/设计方案与报告/设计方案-元素定位项目化重构.md`。本 PRD 以**代码**为准。

2. **接口文档两处状态码与代码相反** —— 文档的 legacy 页面错误表写「`400` 名称(label)必填」（`:808`）、元素表写「`400` 元素名称(alias)必填」（`:1049`），但两处代码都**没传 status**，实际返回的是 **HTTP 200** + `{status:false, message:...}`（`views_pages.py:109`、`views_page_elements.py:65`）。

3. **目录层级上限有三个不同数字，且分属三条链路** ——
   1. 项目目录树（`LocatorDirectory`）：**无上限**，只查循环 —— 对应规格里的「unlimited-depth」。
   2. 快照导入的目录路径解析：`api_snapshot.MAX_DEPTH = 20`，文案「目录最多嵌套 20 层」。
   3. legacy 页面树（`Page.parent`）：`page_tree.MAX_PAGE_TREE_DEPTH = 5`，文案「目录最多嵌套 5 层」。
   接口文档只写了 5 层并把它挂在导入路径上，与实际执行路径不符。

4. **legacy 5 层限制在新建路径上不可达** —— `validate_parent_and_depth` 只在 `is_folder=True` 时校验深度，而 `create_page` 的 legacy 分支在 `is_folder=True` 时早已返回 `410`「请改用项目目录 API 新建目录」，走到校验那一步时 `is_folder` 恒为 `False`。即该限制只在**移动 legacy 目录节点**时生效。

5. ~~**删除目录的确认文案与实际行为不符**~~ —— **已由变更 `element-locator-drag-move` 修复**：`delete_directory` 改为显式子树级联（先删子树内页面与元素，再删子树目录，单事务），删除目录确实会一并删除其下全部内容，确认文案与行为一致。

6. **同一资源的不存在语义不统一** —— `POST pages/{id}/elements/` 对页面不存在回 `404`，而 `POST pages/{id}/elements/batch/` 对同一条件回 **`400`**（`views_page_element_batch.py:28`）；`GET pages/{id}/items/` 的 404 文案还是**英文** `page not found`（`views_page_elements.py:133`），同模块其它端点均为中文。

7. **两个写端点没有存在性校验** —— `PUT items/{el_id}/` 与 `DELETE pages/{id}/` 对不存在的 id 一律返回 `{status:true}`，前端无从分辨「删掉了」与「本来就没有」。

8. **零消费的端点、函数与模型** ——
   - 端点：`POST /api/elements/move/`、`POST /api/elements/files/batch-delete/`、`flows/` 的 4 条 —— 共 **6 条端点**仍无任何调用方（前端无 UI，后端 `api` 层也无人经它们写入）。新增的 `batch-move/` 与 `batch-delete/` 已由元素定位前端消费（变更 `element-locator-drag-move`）。
   - api 函数：`get_flows` / `get_test_points` / `create_flow` / `get_or_create_flow` / `delete_flow` —— 全仓零调用。
   - 模型：`PageFlow` 没有任何产品消费方；页面的 `flow_out` / `flow_in` 聚合只喂给 legacy 页面列表，而该字段在当前 UI 里不展示。
   - 字段：`Element.tags` 接口可读可写，但元素定位前端不展示、不提交。

9. **`pages/clear/` 是全库清空且无防护** —— 该端点一次性删除 `el_elements` / `el_page_flows` / `el_pages` **全表**，不按用户、不按项目过滤，也没有二次确认或权限校验；前端没有入口，但只要拿着合法令牌调一次就不可恢复。

10. **`projects` 的 `lookup_value_regex` 仍含已下线的 `web|api`** —— `views_projects_drf.py:45`。它使 `/projects/web/` 能进视图再报「项目不存在」，而不是在 URL 层直接 404；正则与「只剩 android」的现状不一致。

11. **`file_count` 名不符实** —— `serialize_project` 的 `file_count` 取的是**全库**非目录页面数（`Page.objects.filter(is_folder=False).count()`），不做项目归属过滤。单项目下暂时看不出问题，但它不是「该项目下的文件数」。

12. **`files/batch-delete` 的 `deleted` 不是页面数** —— 取的是 Django `delete()` 的级联对象总数（页面 + 其下元素）。删 1 个含 5 个元素的页面会返回 `deleted: 6`。

13. **测试覆盖非常薄，且方向偏结构而非行为** ——
   1. **接口层为 0** —— `tests/api` 没有元素定位的 YAML 与驱动脚本，26 条路由没有一条被黑盒验证过。
   2. **灰盒 3 文件 / 42 条全是结构性门禁** —— 路由契约（`resolve()` 断言）、视图模块行数预算、写库收敛、退役路径 404。它们守住「拆分没拆坏」「死代码没回来」，但**没有一条断言业务行为**（重名 409、循环移动、别名落库、upsert 去重、层级上限）。
   3. **前端只有 1 个表驱动文件 / 10 条** —— 只断言 `api.ts` 各封装的 URL / 方法 / 调用一次，**没有任何组件或 composable 测试**：目录树的增删改交互、元素表的行内编辑与落库、错误条与重试都无断言。
   4. **端到端层为 0** —— 端到端套件只覆盖登录模块。
   5. **P2 登记为空** —— `frontend/tests/element-locator/p2/README.md` 只写了一句「真后端页面/元素联调 → 依赖设备与网络 → E2E」，而没有真的 E2E 用例接住它。
