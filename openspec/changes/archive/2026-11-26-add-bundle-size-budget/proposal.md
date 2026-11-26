# Proposal: add-bundle-size-budget

## Why

2026-11-24 的性能实测发现首屏传输 1.99 MB（`/login`）/ 2.35 MB（`/dashboard`），而仓库此前**没有任何体积门禁**：
`vite build` 只打一行 `chunkSizeWarningLimit: 1500` 的提示，没人拦；`tests/perf` 只覆盖「跑起来之后的时间与传输」，
既需要浏览器又需要服务。结果是一个 `import * as echarts from "echarts"` 就能悄悄多带 334 KB gzip。

本变更给构建产物装一道**离线、秒级、可进 CI** 的体积闸：入口 JS / 入口 CSS / 最大单块 / JS 总量四条 gzip 上限，
超限即红。它是 `tests/perf` 的廉价前置防线：体积是原因，加载时间是结果。

## What Changes

- 新增 `frontend/bundle-budgets.json`：四条上限（gzip KB），当前基线取 2026-11-25 实测值 × 1.1 留余量
- 新增 `utils/check_bundle_budget.py`：解析 `frontend/dist`（缺失时先跑一次 `vite build`），
  算 gzip 体积并与预算比对，超限时列出「指标 / 实测 / 预算 / 差多少」
- `utils/check_gates.py` 注册 blocking gate `bundle-budget`（排在 `vite-build` 之后，复用同一次构建产物）
- `.github/workflows/ci-phase1.yml` 的 frontend job 加上该 gate
- 不改任何页面代码；不改 `tests/perf` 的阈值

## Capabilities

### New Capabilities

- `frontend-bundle-budget`：构建产物体积预算——四条指标的口径、基线来源、超限失败、缺产物时的构建前置

### Modified Capabilities

（无）

## Impact

- 代码：2 个新文件 + 2 处注册（`check_gates.py`、CI YAML）
- 运行时：+15 s（dist 已存在时 < 1 s；只在跑完整 `run.py check` 且 dist 过期时触发构建）
- CI：frontend job 增一条 gate；失败信息含实际值与预算，能直接定位是哪一类体积涨了
- 回退：删 gate 注册与两个新文件，单 commit `git revert`
