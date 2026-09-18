## Context

见 `proposal.md` Why。现网 `frontend/src/modules/dashboard/index.vue` 以六个透明 `.doc-section` 堆叠；`DashboardView.style.css` 仍标注「清新简洁风」。KPI 卡与趋势 `AppCard` 已是 doodle，章节层未对齐。已批准原型：`dev_docs/项目笔记/平台前端主题参考模版/dashboard-chapter-board-proto.html`（路线 B）。

## Goals / Non-Goals

**Goals:**
- 四章节钉板 IA + 章节头（方标 / eyebrow / marker）+ chip 摘要
- 用例 + 元素合并为「测试资产」双栏
- 样式令牌化（`var(--*)`），保持 L3：章节=`doc-section` 变体，数据块=`StatsCard`/`AppCard`

**Non-Goals:**
- 不改后端 API / DTO
- 不重画 StatsCard、AppCard、图表内部配色
- 不做双栏工作台（路线 C）
- 不改其他模块页面骨架

## Decisions

1. **章节容器**：在 `.doc-section` 上加 modifier（如 `.doc-section--board` + `ch-ops|ch-ai|ch-asset|ch-trend`），保留 L3 分区语义，避免用 AppCard 包一整章。
2. **摘要**：`doc-section__label` 多行灰字 → `.chip-row > .chip`；`roleBreakdown.today/total` 整串进 chip，不新增 API。
3. **资产双栏**：章内 `.asset-cols` + `.subhead`；小屏单列。
4. **趋势与动态**：原「趋势数据」+「最近动态」合并进第四章；页脚状态条保留在 `doc-body` 末。

**备选驳回：** 路线 A 边界仍弱；路线 C 与 L2 骨架冲突大。

## 模块防火墙自检

- 仅改 `frontend/src/modules/dashboard/` 视图与样式（至多 logic 展示辅助）
- 无跨 App import、无写库、无新 HTTP
- 仪表盘保持只读

## Risks / Trade-offs

- [章节变高] → 双栏与 chip 换行；窄屏单列验证
- [类名与 style 文件漂移] → 以磁盘 `index.vue` / `DashboardView.style.css` 为准再改
- [单测若快照旧 DOM] → 更新仪表盘相关前端测试断言
