## Context

现状与动机见 `proposal.md`。约束：

- L0–L5 骨架已在 `frontend/AGENTS.md` 与 `frontend-l2-page-region` 等 spec 中冻结：页头唯一 `WorkbenchHeader`，表格唯一 `AppTable`，覆盖层唯一 EP。
- 原型 `module-subpages-doodle-proto.html` 的 SketchTable / DialogForm / 面包屑是**视觉名**，不能落成第二套表格或第二套 modal。
- 令牌唯一登记处：`frontend/src/shared/styles/tokens.css`（T0 颜色原子 + `--comp-*` + `--c-*` / `--app-*` 别名）。
- 用户确认范围：P0 共享件 + 设备/报告表纸；视觉 + 导航模版。Hub→台→叶的**导航接线**在本轮做；三级壳抽取与检查器/画布/评测换皮属 P1/P2。

## Goals / Non-Goals

**Goals:**

- 一个共享面包屑/返回零件，挂进现有页头，不改 L0/L1
- `AppTable` 增加表纸皮肤，设备与报告列表共用
- 把已有「← 返回」从正文挪进页头，并补祖先链（能指到的路由才列入）
- 新视觉值先登记 token 再引用

**Non-Goals:**

- 不改路由 path / 深度 / keep-alive
- 不抽 `HubProjectPage` / `TreeWorkbench` / `FileLeafPage` 三个页面壳
- 不换设备检查器分栏、页面流画布节点、评测中心、仪表盘钉板
- 不新增独立 `SketchTable.vue` / `DialogForm.vue` 作为 L4/L5 第二实现
- 不改后端 API 与下载协议

## Decisions

### 1. 导航零件挂在 WorkbenchHeader 槽，而不是第二套页头

- **选择**：新增 `WorkbenchCrumbs.vue`（返回芯片 + crumbs），由 `WorkbenchHeader` 增加 `#nav` 槽（品牌标题下方或左侧）消费；页面把祖先 `{label, to?}` 与可选 `backTo` 传入。
- **理由**：L2「页头唯一共享件」与原型「页头下方一条」同时满足；正文不再放 `.top-bar` / `.back-btn`。
- **备选**：只改各页 `actions` 里的 `el-button`——无法表达多级祖先，且报告详情现在把返回放在 `.doc-body`，与原型冲突。

### 2. SketchTable 是 AppTable 的 accent 皮肤，不是新组件

- **选择**：`AppTable` 增加可选 `accent`（CSS 色 / `var(--c-*)`），主题在 `.wb-shell .ac-table` 外套一层 `.sketch-sheet`（或根 class）画虚线纸 + `box-shadow: Npx Npx 0 0 var(--sketch-accent)`。设备、报告传入各自 `--c-*`。
- **理由**：`frontend-l4-data-surface` 禁止第二套通用表格；原型「表纸」只是外壳。
- **备选**：新建 `SketchTable.vue` 包一层 `AppTable`——命名对齐原型，但会造成「同层双实现」与 AGENTS 冲突。

### 3. 设备列表去掉 el-card，改用表纸或 AppCard

- **选择**：删除 `el-card.table-card`，表格外只留现有 wrapper（横向滚动仍由模块容器负责）。
- **理由**：`el-card` 是 EP 默认卡，与 doodle 表纸双层边框。
- **备选**：换成 `AppCard`——钉板图钉会干扰宽表；P0 表纸本身已是数据块外壳。

### 4. DialogForm 落成 EP 皮肤令牌，不落成新 overlay 组件

- **选择**：在 `tokens.css` 登记 `--comp-dialog-*`（若缺口），`style.css` 既有 `.el-dialog` 纸面补硬阴影/虚线（全局 L5 皮肤已规定单一落点）。设备两个 dialog 只改内容区字段，不改覆盖层实现。
- **理由**：`frontend-l5-overlay` 禁止自建 modal；原型 DialogForm 是表单态，不是新通道。
- **备选**：`shared/components/DialogForm.vue` 包 `el-dialog`——仅当出现第二个真实消费方且 API 稳定时再抽；P0 设备两处不足以上抽共享业务表单。

### 5. AI 四子项不改侧栏结构，只接线深链回退

- **选择**：`TaskDetailPage` → `/ai-assistant/agents`（任务看板所在子项）；`SkillViewerPage` → `/ai-assistant/toolbox`；`AgentDetail` → `/ai-assistant/agents`。去掉正文 `.back-btn`。
- **理由**：侧栏已是模版②；深链必须可见回到**子项**而不是笼统入口。
- **备选**：任务详情回到带 hash 的列表——当前无 hash 契约，不引入。

### 6. 令牌缺口只加 --comp-*，不把原型字面量拷进模块 CSS

- **选择**：原型 `--dash` / `--paper-card` / 波浪下划线色若与现役 `--comp-sidebar-dash` / `--paper` / `--c-case` 等价则复用；不等价则新增 `--comp-crumb-*` / `--comp-sheet-*`，值指向颜色原子。
- **理由**：`frontend-l0-design-tokens` 禁止模块直写字面量；`--ink` 在平台是 `#1e1e24` 别名，原型 `#2c2c2c` **不覆盖全站墨色**。
- **备选**：把 `--ink` 改成原型值——会牵动全站，超出 P0。

## 模块防火墙自检

- 跨 App import：不涉及后端 `apps/`，无跨 App import
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- INSERT/UPDATE/DELETE 收敛到 api.py：本变更无写库
- 前端不直连数据库；仪表盘不做写操作：本变更不改仪表盘写路径，HTTP 仍走各模块 `api.ts`

## Risks / Trade-offs

- [页头变高，与 `--app-topbar-h` 96px 对齐契约冲突] → 面包屑放在 subtitle 区并保持单行省略；窄屏允许页头 `min-height` 增高下推正文（既有 L2 契约已允许动作换行增高）
- [祖先标签与路由名不一致] → 文案取各模块页头现用 title，path 取现有 `router.push` 目标，不发明新路由
- [表纸硬阴影在横向滚动容器内被裁切] → 阴影画在滚动容器外框，不画在 `el-table` 内部
- [全局改 `.el-dialog` 影响所有弹层] → 只补已有纸面缺口（阴影/虚线），不改关闭策略与尺寸；视觉回归抽查登录错误框与 workflow 新建框
