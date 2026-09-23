## Context

动机见 `proposal.md` Why。现状：`ActivityTimeline.vue` 列表 `flex:1` 随父级伸缩，条目少时只剩标题；`GET /api/dashboard/activities/` 无查询参数、代码只取 3 条智能体更新再 `[:10]`，与接口文档中的 `TestRunRecord` 5+3 口径不一致（该模型已随执行引擎表删除）。主屏与历史共用同一只读端点。

## Goals / Non-Goals

**Goals:**

- 用 CSS 固定十条槽位高度，主屏默认 `limit=10`
- 标题行 `DoodleBtn` + 本页 `el-dialog` 翻历史（`offset=10` 起）
- 活动聚合改为 `AITask` + `AIAgent`，窗口内内存切片分页

**Non-Goals:**

- 不新建活动表、不写库、不新增 URL
- 不改 KPI / 趋势图 / `dashboard-chapter-boards` 章节壳
- 不恢复 `TestRunRecord`
- 不做实时推送（仍靠页头「刷新」）

## Decisions

1. **十条槽位用固定 `min-height`，不用假数据填满。** 槽高按「单行标题 + 时间」（约一条 `.timeline-item` 的压缩高度）×10，令牌化在仪表盘样式里。详情/标签超出槽位时在 `.timeline__list` 内滚动，主屏 DOM 仍最多 10 个条目。  
   **备选：** 用 10 个骨架占位填满 — 空态会被假行干扰，驳回。

2. **历史用本页弹层，不新开路由。** 用户要的是按键看更早记录，不是新模块。弹层复用时间线条目结构；「加载更多」在 `data.length === limit` 时继续 `offset += limit`。  
   **备选：** 抽屉 / 独立 `/dashboard/activity` — 过重，驳回。

3. **分页保持 `data` 为数组，加 `limit`/`offset`。** 避免 **BREAKING** 把数组改成 `{items,total}`。`limit` 默认 10、最大 50；非法值 400。窗口上限 100：各源最多取 100，合并排序后截 100，再切片。  
   **备选：** `page`/`page_size` — 与本仓多数列表不一致且本次无统一分页组件需求；数组+offset 足够。

4. **`run` 语义改为助手任务卡。** `ai_usage.py` 已用 `AITask` 填仪表盘执行图；活动时间线与之同源。`type=run` 保留以便现有 `timeline-item--run` 样式继续工作。智能体更新仍 `type=agent`，来源从 `[:3]` 放开到窗口上限。  
   **备选：** 只扩智能体条数 — 历史几乎为空，驳回。

5. **按键放在 `timeline__title` 同行右侧，使用 `DoodleBtn` `tone="paper"`。** 仪表盘页头「刷新」已是 `wb-btn--sunset`；活动区用共享硬边键，避免再发明一种按钮。弹层走 `el-dialog`，关闭按钮沿用 Element Plus 默认，不另做第三套皮肤。

## 模块防火墙自检

- 跨 App import：`apps/dashboard` 继续只读 `AIAgent`，新增只读 `AITask`（与现有 `ai_usage.py` 相同层级）；用户可见范围继续走 `apps.ai_assistant.api.filter_agents_for_user`，不 import service/runner/consumer
- 无 INSERT/UPDATE/DELETE
- 前端只经 `dashboard/api.ts` → `djangoClient`；不直连库
- 不新增跨模块写路径

## Risks / Trade-offs

- [合并窗口 100 条之外的更早记录不可见] → 仪表盘本就不是审计库；需要全量历史时应走助手任务列表 / 智能体列表，不在本 change 扩表
- [各源先截 100 再合并，极端情况下某一源更早条目被挤出窗口] → 可接受；两源都按时间倒序截取，主屏永远是全局最新 10 条
- [槽位高度与带 detail 的条目不一致导致看不见十条标题] → 主屏条目以标题行为准压缩，detail 允许在槽内滚动；单测断言槽 `min-height` 与条目数上限
- [接口文档仍写 TestRunRecord] → 实现任务同步 `API-仪表盘.md` 口径（编号见 PRD-需求总纲，路径按仓库文档约定）
