## Why

`/cases/projects/:id` 这张项目用例表上线后，功能已经齐了，但**视觉与交互没有接设计系统**：`ProjectSheet.vue` 里 12 个交互元素全是浏览器原生 `<select>` / `<input>` / `<button>`，全文件只给它们写过一条 `.sheet-toolbar { display:flex }`；`style.css` 里也没有任何针对裸元素的规则，所以整页呈现的是系统默认外观。

具体代价有三个：

1. **「列显示」被摊成 8 个同形按钮**（隐藏编号 / 隐藏优先级 / …），状态只靠文案前缀区分，视觉上是一排文本框，且随列数增长而线性变长。
2. **每个单元格都是常驻编辑控件**：优先级 / 系统 / 业务是 `<select>`，标题 / 模块是 `<input>`，12 行 × 5 个控件 ≈ 60 个框；表纸退化成表单矩阵，行高被控件撑高、视线没有落点。
3. **行内自带「保存 / 删除」并直接 PATCH / DELETE**，与 `case-manager-case-form` 既有的「步骤编辑面板」要求冲突（面板内不单独提交、行要标记未保存变更、由页面级保存落库），而旧的 `CaseStepDrawer.vue` 已随文件模型一起删除，这条要求当前**没有落点**。

同一批问题里还夹着两个可核对的缺陷：`updated_at` 直接渲染 ISO 字符串并被列宽截断成 `2026-11-17T19:12…`；加载中没有任何骨架（`loading` 没有接到表格上）。

## What Changes

- 控制区改用共享件：分组 → `FilterTabs`；优先级 / 业务筛选 → `.sketch-kit` 作用域内的 `el-select`；新增 / 导入 → `DoodleBtn`；计数 → 等宽 chip。**页面内不再出现裸 `<select>` / `<input>` / `<button>`**（导入用的隐藏 file input 除外，它不可见）。
- 「列显示」从 8 个按钮收成**一个「列 n/8」按钮 + 复选清单**（`el-popover`），勾选即显隐，计数随可见列变化。
- 表内改成**只读排版**：优先级 / 系统 / 业务 / 步骤用 chip，编号用等宽，更新时间用相对时间（`title` 给绝对时间），组头条用合并行。**单元格内不再有可聚焦输入件**。
- 行内「保存 / 删除」撤掉，改为**行抽屉**（`el-drawer`）：8 字段 + 步骤序列（新增 / 删除 / 上下移）+ 前置条件；抽屉内改动只落草稿，`应用改动` 后该行标为**未保存**，由页面级「保存」逐行 `PATCH`。
- 删除改到抽屉底部，走 `ElMessageBox` 确认。
- 补三态：加载 `SkeletonCard`、失败 `ErrorState`、空 `EmptyState`；加载期间不渲染空态。
- 把 `ProjectSheet.vue` 拆成 4 个私有组件 + 1 个样式文件（当前单文件已超 500 行红线）。

## 关联文档

- 视觉与版式来源：`temps/case-sheet-redesign-proto.html`（本轮已审阅的方案与可点原型）。
- 控件与表纸口径：`doodle-craft` skill（`references/components/data-display.md` §1.1 表格字号三档、`sketched-ui-kit.md`、`general.md` §4 标签）。
- 先行案例：`openspec/changes/archive/2026-11-17-bug-controls-sketched-kit`（控制区排布与 kit 皮肤）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `case-project-sheet`：新增「项目表控制区与行编辑模型」一条要求——控制区只用共享控件、列显示收成菜单、单元格读态化、行编辑经独立面板并带未保存标记与页面级保存、删除需确认。

## Impact

- 前端：`frontend/src/modules/case-manager/` 内 `ProjectSheet.vue` 重写并拆件，新增 `components/SheetToolbar.vue` / `SheetColumnMenu.vue` / `SheetRowDrawer.vue` / `SheetGroupCell.vue` / `CaseChip.vue`、`helpers/sheet.ts`、`ProjectSheet.style.css`；新增共享 `shared/helpers/datetime.ts`。
- 不动：后端、路由、视图存储协议（`hidden_columns / filters / sort / group_by` 四字段）、`AppTable`、`.sketch-kit`、`tokens.css`、`bug-manager` 与 `device-pool` 的时间格式化实现（收敛为 P2）。
- 无数据迁移；无新增依赖。
