# Frontend Vitest — 登录模块 + 仪表盘模块

优先级约定见 **[PRIORITY_TEMPLATE.md](./PRIORITY_TEMPLATE.md)**。

目录按模块 × 优先级分类：

```
tests/<module>/
  p0/   # 必测
  p1/   # 建议测
  p2/   # 默认不测（仅 README 登记）
```

## 覆盖范围

| 级别 | 路径 | 测什么 |
|------|------|--------|
| P0 | `login/p0/useLoginForm.spec.ts` | 登录/注册校验 |
| P0 | `login/p0/useSavedUsername.spec.ts` | 记住账号 |
| P0 | `login/p0/useViewStateMachine.spec.ts` | 三态切换 |
| P0 | `login/p0/useAuthFlow.spec.ts` | API 编排（mock） |
| P0 | `login/p0/useAuthPool.spec.ts` | 多账号 token 池 |
| P0 | `login/p0/apiAuthInterceptors.spec.ts` | 401 refresh 并发去重 / 重试 / 多账号失败 |
| P0 | `login/p0/LoginCard.spec.ts` | 提交/禁用/记住账号 |
| P0 | `login/p0/RegisterCard.spec.ts` | 提交/禁用/去登录 |
| P1 | `login/p1/LoginView.logic.spec.ts` | 切模式清表单 |
| P1 | `login/p1/AccountSwitchPrompt.spec.ts` | 切换/添加账号 emit |
| P1 | `login/p1/LoginErrorOverlay.spec.ts` | 展示/关闭/ESC |
| P2 | `login/p2/README.md` | 整页/插画/真后端 — 不写用例 |
| P0 | `dashboard/p0/useDashboardStats.spec.ts` | 数据获取编排 + mapStatsResponse 纯映射 |
| P0 | `dashboard/p0/StatsCard.spec.ts` | 数值展示/趋势文案/loading 骨架/跳转 |
| P1 | `dashboard/p1/DashboardView.logic.spec.ts` | 挂载自动加载 + 分项查询回退 |
| P1 | `dashboard/p1/TaskResultPanel.spec.ts` | 摘要 chip / 状态图标 / 任务跳转分支 |
| P1 | `dashboard/p1/ActivityTimeline.spec.ts` | 条目渲染/类型样式/空态/分隔线 |
| P1 | `dashboard/p1/ModuleNavigator.spec.ts` | 模块卡片渲染/统计注入/跳转 |
| P2 | `dashboard/p2/README.md` | 整页/ECharts 图表/动画/真后端 — 不写用例 |

## 命令

```bash
cd frontend
npm test                 # 全部（P0+P1）
npm run test:p0          # 只跑 P0
npm run test:p1          # 只跑 P1
npm run test:ui          # UI：左侧按 project 分 P0 / P1
npm run test:report
```

Vitest UI（`/__vitest__/`）会按 **project：P0 / P1** 分栏；套件名也带 `[P0]` / `[P1]` 前缀。P2 无用例，不出现在报告里。
