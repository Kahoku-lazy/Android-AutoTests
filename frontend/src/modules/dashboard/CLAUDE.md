# dashboard 模块 CLAUDE.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../CLAUDE.md`；本文只写本模块增量，冲突以全局为准。改 UI 另读 `../../../../dev_docs/05-开发与测试/设计-仪表盘前端UI规范与checklist.md`。

## 红线（全局表 dashboard 行的展开）

| 只做 | 禁止 |
|------|------|
| 聚合展示（字段直映后端结果） | 写操作、计算（全平台唯一只读区） |

- 全平台唯一只读区：禁止任何写操作，禁止前端自行计算/推导指标，展示字段直映后端返回。

## 本模块契约

- 仅 2 端点：`GET /dashboard/stats/` · `GET /dashboard/activities/`；DTO 类型在 `@/shared/types/dashboard`

## 本模块特殊布局/样式

- 模块级样式落点：`DashboardView.style.css`；图表配置与色值归 `composables/useDashboardStats.ts` 与图表组件内（JS 画布例外）。

## 关单附加项（全局清单的 delta）

```
[ ] 零写操作；字段直映后端结果，无前端计算
[ ] 统计/活动接口经 api.ts 2 端点，无旁路
[ ] 改 UI 已对照 dev_docs/05 仪表盘规格
```
