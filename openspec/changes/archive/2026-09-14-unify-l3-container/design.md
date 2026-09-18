## Context

动机见 `proposal.md` - Why。现状（已核对）：

- 点阵 6 处：`.doc-page` ×2（`device-inspector/index.vue:170`、`dashboard/DashboardView.style.css:12`）· `.doc-body` ×4（`case-manager/ProjectWorkspace.vue:119`、`element-locator/ProjectWorkspace.vue:109`、`element-locator/ProjectList.vue:75`、`element-locator/LocatorFileView.vue:147`）。范围外：`views/LoginView.style.css:8`（登录页，非 L3 页面）与 `device-inspector/components/ScreenshotView.css:20`（pushpin 径向渐变，非点阵）。
- `style.css:190` 基座 `.doc-body` 为 `padding: 24px 32px 60px`；`style.css:239` `.doc-page--fixed .doc-body` 为 `16px 24px 28px`；`.wb-header` 为 `8px 24px`（水平 24px）→ 基座水平 32px 与页头不一致。
- `.doc-body` 覆写 13 处：7 处 modifier 限定（合规）、5 处裸写法（`report-generator` ×4 + `device-inspector` ×1）、1 处仅注释。
- `.wb-body` 全仓仅 `workflow/index.vue` 一处（资源态目录树 / 绘制态 VueFlow）。
- `--app-paper-dot` 的消费方正是上述 2 处 `.doc-page` 点阵；`--doodle-bg` 另有 7 处消费方（不在本次收敛范围）。

约束：不改模块业务逻辑；点阵消失属**可见观感变化**，需三档浏览器核验。

## Goals / Non-Goals

**Goals:**

- 点阵单一来源（只由 `PaperDoodles` 提供）
- `.doc-body` 水平内边距与 `.wb-header` 同值，消除 C 类页面靠覆写对齐的隐式依赖
- 容器覆写统一为 `.<模块modifier> .doc-body` 限定写法
- 画布页 `.wb-body` 成为可静态检查的登记例外

**Non-Goals:**

- 不删 `--app-paper-dot` / `--doodle-bg` 令牌（退役另议）
- 不合并分栏面板命名（`.workspace` / `.page-workbench__split`）
- 不动 L4（表格 / 卡片网格 / 表单）与 L5（覆盖层）
- 不动登录页 `LoginView` 的独立视觉

## Decisions

### 1. 点阵唯一来源 = `PaperDoodles`

- **选择**：删除 6 处自绘点阵，`.doc-page` / `.doc-body` 一律透明或纯纸色；同步删除 `frontend/AGENTS.md` L2 速查 §③ 的「背景点阵」许可
- **理由**：L0 速查已写「禁止在 L0/`doc-body` 再叠点阵」，冲突根源是 L2 速查又开了口子；只改一处文档即可让规则自洽
- **备选**：保留模块点阵、改 L0 措辞使其合法 —— 与「暖白实色纸面 + 主区涂鸦」的目标观感相反，已否决

### 2. `.doc-body` 水平内边距取 24px（改基座，不改页头）

- **选择**：`style.css:190` 的 `var(--app-space-xl)`(32px) → `var(--app-space-lg)`(24px)，竖直方向保持 `24px … 60px`
- **理由**：`.wb-header` 与 `.doc-page--fixed .doc-body` 已是 24px；改基座即三处同值，策略① / ② 口径统一
- **备选**：把页头改成 32px —— 影响 19 个页头且与 L2 已归档契约「页头与内容同取 24px」冲突，否决

### 3. 裸覆写按「先删、再限定」处理

- **选择**：逐处判定 —— 覆写内容与全局 / 策略② 变体**等价**（`display:flex`、`gap`、`overflow-y:auto`、同值 `padding`）则整条删除；含本页**真实增量**（分隔线、`overflow:hidden`、页宽约束）则改为 `.<模块modifier> .doc-body`
- **已知落点**：`report-generator/index.vue:370` 含 `overflow-y:auto!important`，而该页页面根当前**没有 modifier** → 需为页面根补 modifier（如 `report-workbench`）或删除该条；`TaskReport` / `ReportDetail` / `CaseBreakdown` / `device-inspector` 逐处判定
- **理由**：不为「写法整齐」保留无信息量的声明；同时保证残留覆写都有作用域
- **验收**：裸选择器 `.doc-body {` 命中数为 0

### 4. 画布例外的登记方式

- **选择**：例外判据（主体为自由布局画布 / 图形编辑器）写入 spec 与 `frontend/AGENTS.md`；在 `workflow/index.vue` 例外处加一行注释指向登记
- **理由**：可静态检查（`.wb-body` 恒为 1 处），避免例外被复制

### 5. 令牌不顺手删

- **选择**：`--app-paper-dot` 消费方归零后只登记为「退役候选」，本变更不删
- **理由**：令牌退役牵动 `tokens.css` 分层与 L0 段规则，属独立事项，避免范围蔓延

## 覆写收敛记录（apply 阶段）

| # | 文件 | 原覆写内容 | 处置 | 等价性说明 |
|---|------|-----------|------|-----------|
| 1 | `device-inspector/index.vue:174` | `flex/min-height/width/max-width/margin/padding:0/overflow:hidden` | 保留增量 + 页面根补 `inspector-workbench` | `padding:0`（全出血工作区）与 `overflow:hidden` 全局没有 → **不可删** |
| 2 | `report-generator/index.vue:370` | `overflow-y:auto!important` + `padding:16/24/32` + `gap:14px` | 保留 + 页面根补 `report-workbench` | 竖直 32px / gap 14px 与全局（60px / gap 24px）不等价 |
| 3 | `report-generator/TaskReport.vue:337` | `padding:16/24/48` + `gap:16` + `display/width` | 保留 + 页面根补 `task-report-page`（**两个页面根都补**） | 竖直 16/48 与全局 24/60 不等价 |
| 4 | `report-generator/ReportDetail.vue:439` | 同上 | 保留 + 页面根补 `report-detail-page` | 同上 |
| 5 | `report-generator/CaseBreakdown.vue:414` | 同上 | 保留 + 页面根补 `case-breakdown-page` | 同上 |

**结论：5 处均含全局没有的真实增量 → 全部按决策 3 的「改限定写法」处理，无一处可整条删除。**
收敛后裸选择器 `.doc-body {` 在 `frontend/src/modules` 命中数为 0。

## 模块防火墙自检

- 跨 App import：不涉及（纯前端样式与文档）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 所有 INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无写操作）
- 前端不直连数据库；仪表盘不做写操作：不涉及

## Risks / Trade-offs

- [6 处点阵消失属可见变化] → 三档浏览器核验（768 / 1024 / 1280）+ 与 L3 报告基线逐页对照；必要时保留回滚点
- [基座内边距 32→24 使策略① 页面内容右移 8px] → 影响面为 C 类 3 页与其他未覆写的策略① 页；三档核验覆盖
- [删除覆写可能改变竖直 gap / padding] → 每处删除前做等价性比对（与全局 / 策略② 变体逐属性对照），不等价则改限定写法
- [本环境无登录态、无法自测三档] → 与 `remove-frontend-dead-code` 4.4 同口径：由用户在已登录浏览器代验，或提供测试账号；未核验前不得关单

## Migration Plan

1. 复核 6 处点阵 + 13 处覆写清单，记录三档基线
2. 改 `style.css` 基座内边距；删 6 处点阵
3. 收敛 5 处裸覆写（删除或加 modifier）
4. 同步 `frontend/AGENTS.md`（L2 §③ / §④）与 `workflow/index.vue` 例外注释
5. `npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check`
6. 三档浏览器核验 6 个受影响页面
7. 回滚：`git checkout` 涉改文件即可，无数据迁移
