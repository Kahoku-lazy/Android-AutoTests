# [P2] 默认不写 Vitest

本目录**故意不放 `.spec.ts`**。与登录模块一致：P2 只登记、不测。

## 仪表盘模块 P2 清单（跳过 Vitest）

| 项 | 原因 | 去向 |
|----|------|------|
| `index.vue` 整页 mount | 9 个子组件 + el-card/el-button 拼装，mock 多、收益低 | E2E 或人工点验 |
| `TrendBarChart` 图表渲染 | `useECharts` → echarts Canvas 绘制，jsdom 无真实画布 | 不测 |
| `StatsCard` countUp 数字滚动 | animejs 视觉动画，无业务分支价值 | 不测 |
| `ModuleNavigator` / `ActivityTimeline` 入场动画效果 | staggerReveal 视觉时序 | 不测 |
| 真后端 `/dashboard/stats/` 与 `/dashboard/activities/` 联调 | 依赖服务与网络 | E2E |
| 路由守卫 + 真登录进仪表盘 | 全链路鉴权 | E2E |
| 刷新按钮真后端刷新 | 依赖服务 | E2E |

优先级约定见：`../../PRIORITY_TEMPLATE.md`
