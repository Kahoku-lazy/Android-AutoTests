## Context

`/cases/projects/:projectId` 在变更 `2026-11-17-case-project-sheet` 里落地为「一个项目一张表」，spec 只定义了功能边界（999 上限、个人视图、YAML 追加导入、步骤编辑面板），没有一条视觉或控件形态要求。于是 `ProjectSheet.vue` 用裸 HTML 元素把功能拼齐就收工了。

现状约束（读代码得到，不是推测）：

- 表纸已经是统一件：`AppTable` + `accent="var(--c-case)"` → `.wb-shell .sketch-sheet`，全仓 10 处消费方共用，**不要动**。
- 表头 16 / 正文 14 / 次行 12 三档字号已在 `workbench-theme.css` 的 `.wb-shell .ac-table th` 全局生效，并注明「模块不得再覆写」。
- 控制区已有先行案例：`bug-manager/index.vue` 的 `.filter-bar.sketch-kit`（`FilterTabs` + kit `el-input` / `el-select` + `DoodleBtn`），本变更照同一排布法。
- 视图四字段 `hidden_columns / filters / sort / group_by` 由 `PUT /cases/projects/{id}/view/` 持久化，前端不得改协议。

## Goals / Non-Goals

**Goals:**

- 控制区、表内读态、行编辑三处全部用既有共享件表达，页面内不再出现裸表单元素。
- 编辑模型从「每格常驻控件 + 行内保存」改为「只读表纸 + 行抽屉 + 草稿 + 行级未保存 + 页面级保存」，与 `case-manager-case-form` 的步骤面板要求对齐。
- 单文件回到 500 行以内，逻辑下沉 helpers。

**Non-Goals:**

- 不做 Airtable 式逐格即时保存（表格内不出现可聚焦输入件）。
- 不做列宽拖拽、冻结列、行多选批量操作。
- 不做步骤里的 `anchor` / `log` 编辑器（执行提示只**保留**不**编辑**，见 D4）。
- 不改视图存储协议、不改后端字段、不改路由与导航。
- 不新增共享组件、不新增令牌、不加依赖。
- 不迁移 `device-pool` / `ops-console` / `report-generator` 三处重复的时间格式化（P2 单独立项）。

## Decisions

### D1 控制区三段式，全部复用既有件

第一行＝视图（分组 `FilterTabs` / 优先级与业务 `.sketch-kit` `el-select` / 「列」按钮），第二行＝写操作（新增标题 `el-input` + `DoodleBtn` 新增行 + `DoodleBtn` 导入 YAML + 计数 chip）与页级保存区（未保存计数 + 保存）。

备选：整页套 `.sketch-kit` 一行平铺。否决——写操作与视图混排后，8 个字段的筛选一旦扩展就会挤成两行半；`bug-manager` 已验证「视图在左、写操作在右」这一排布。

### D2 「列显示」收成一个菜单

`el-popover` + `el-checkbox` 列表，按钮上显示 `<可见列>/<总列数>`。隐藏列仍写 `view.hidden_columns`，协议不变。

备选：保留 8 个按钮但加选中态。否决——列数增长（如加入前置条件列）后按钮会继续变长，且同形按钮的本质问题是「一个概念一个控件」没有落实。

### D3 表内只读，编辑搬进行抽屉

chip 覆盖优先级 / 系统 / 业务 / 步骤；编号等宽；更新时间相对时间 + `title` 绝对时间。行抽屉（`el-drawer`，`size="min(520px, 92vw)"`，与 `BugDetailDrawer` 同口径）承载 8 字段与步骤序列。

备选：内联编辑。否决理由写进 proposal：两套控件皮肤 + 逐格保存状态机，且与既有 spec 的「面板内不单独提交」直接冲突；本平台没有任何一页这么做。

### D4 步骤只编辑动作与断言，执行提示原样保留

抽屉里步骤只暴露 `action` / `assertion`，新增 / 删除 / 上下移。既有步骤的 `anchor` / `log` 随草稿一起深拷贝，保存时原样回传；新增步骤不带执行提示。这样满足「执行提示随步骤保存与读回」，又不把锚点编辑器塞进本轮。

备选：抽屉里同时编辑 anchor / log。否决——字段多（page/entry/target + sku/port/keywords）且与本次视觉主题无关，属另一个变更。

### D5 分组用一张表 + 合并行，而不是每组一张表

现状是 `section v-for` 每组一个 `AppTable`，分组一开就出现多张表纸（多套边框与硬影）。改为**一个** `AppTable` + 哨兵行：数据里插入 `{ __group, __count }` 行，`span-method` 让首列跨满可见列、`row-class-name` 打 `is-case-group`。

备选 A：保留每组一张表但只给外层一个 `.sketch-sheet` 纸框。否决——表头会每组重复一次。
备选 B：不在表内放组头，改成表上方分段标题。否决——组头与行分离后无法表达「这行属于哪组」。

### D6 未保存状态是行级的

`dirty: Set<string>`（用例编号）→ 行首黄油笔边 + 工具栏「未保存 N 处」+ 保存按钮启用。点保存逐行 `PATCH`（只提交可编辑字段），全部成功后清 dirty 并重载。

备选：抽屉内即时 PATCH。否决——与 spec 的「面板内不单独提交」冲突，且新增行还没有编号可 PATCH。

### D7 `updated_at` 走共享相对时间

新建 `shared/helpers/datetime.ts`（`formatRelativeTime` / `formatDateTime`，语义与 `device-pool/helpers.ts` 一致），本页消费。`device-pool` / `ops-console` / `report-generator` 三处旧实现暂不动，避免一次变更横跨三个模块。

## Risks / Trade-offs

- [合并行的 `span-method` 与列隐藏耦合] → 组头内容渲染在「第一个可见列」的插槽里，8 个 cell 插槽都带 `row.__group` 守卫；任一列被隐藏都不会丢组头。验证：逐列隐藏后组头仍在。
- [草稿与列表不同步] → 抽屉只产出新行对象，父级按编号合并；抽屉关闭不写父级状态。验证：改字段后取消，表格不变。
- [逐行 PATCH 半途失败] → 顺序提交，失败即停并保留未保存标记，提示第几条失败；不整体回滚已成功行（重试幂等）。
- [拆分后行数仍超 500] → 样式一律进 `ProjectSheet.style.css` 与各组件 scoped 块，`ProjectSheet.vue` 目标 ≤ 240 行。
- [手稿控件虚线外溢] → 虚线只能来自 `sketched-kit.css`（`.sketch-kit` 作用域）；chip、组头条、抽屉外框一律实线。验证：`node tests/check-dashed-whitelist.mjs`。

## Migration Plan

1. 新增共享 `datetime` helper 与模块 `helpers/sheet.ts`（纯函数，先带单测）。
2. 新增 5 个私有组件。
3. 重写 `ProjectSheet.vue` 为壳，接线三态与保存流程。
4. 删除本页不再使用的行内控件与 `style scoped`，样式迁到 `ProjectSheet.style.css`。
5. 回滚：本变更只动前端渲染层，无库变更；回滚即还原上述文件。
