## Why

`frontend/src/shared/animations.ts` 共 302 行、35 个顶层声明，是全站唯一的 JS 动效工具库。按「**真实代码 import 的可达闭包**」计算（扫描范围：`frontend/src` + `frontend/tests` + `frontend` 根 + `.agents` + `dev_docs`），只有 **6 个导出**被引用，另有 2 个内部 helper 被这些导出依赖；**其余 27 个声明没有任何调用路径**，死占比约 77%。

它们既误导后来者以为「这里有现成动画能力」，又把 `prefers-reduced-motion` 的维护面凭空放大（`align-frontend-motion` 曾为 14 个函数逐个接线，其中多数正是这批死函数）。

## What Changes

- **保留 6 个在用导出**：`countUpFormatted` · `sidebarNavEnter` · `staggerReveal` · `selectPop` · `iconBounce` · `loadingDots`；**保留 2 个内部 helper**：`runMotion` · `prefersReducedMotion`
- **删除 27 个不可达声明**：`countUp` · `pulse` · `buttonPress` · `hoverFloat` · `blobParallax` · `sparkleIn` · `shake` · `bounceItem` · `rippleEffect` · `glowPulse` · `cardTilt` · `progressFill` · `ringProgress` · `bannerSlideIn` · `particleBurst` · `typewriter` · `sequentialHighlight` · `skeletonShimmer` · `svgDraw` · `animeSetDashoffset`（内部 helper）· `fadeSwap` · `bounceBadge` · `slideIn` · `iconWiggle` · `loadingSpin` · `contentSwap` · `pressFeedback`
- 随之移除已无使用的 animejs 具名导入 `createTimeline`（仅被 `sequentialHighlight` / `fadeSwap` 使用）
- 同步 `frontend/AGENTS.md` L0 §⑤：删除 `shared/animations.ts:158（particleBurst）` 这一条 L0 运行时写入行（写入方将不再存在）
- **BREAKING**：无。删除项在代码中 0 调用 → **无可见行为变化**
- 按 schema 约定设 `skip_specs: true`（不产生需求级变化）

## 关联文档

- 前端口径：`frontend/AGENTS.md` L0 速查 §⑤（运行时写入 L0 的现状表）
- 前置变更：`openspec/changes/archive/2026-09-12-align-frontend-motion`（为动效接入 reduced-motion；本次收敛其作用面）
- 说明：`dev_docs/文档编号对照表.md` 不存在，本变更无对应编号文档；属死导出清理

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改任何 Requirement 文本，故无 delta）

## Impact

- 前端：`frontend/src/shared/animations.ts`（302 行 → 约 70 行）
- 文档：`frontend/AGENTS.md` L0 §⑤（删 `particleBurst` 行）
- 验证：`npm run typecheck` + `npx vite build --mode development` + `vue-frontend-check` + 可达性静态证明
- 不影响：路由、API、鉴权、任何页面的实际动效（在用 6 个函数行为不变）
