## Why

L3 现状复盘（`dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与L3现状复盘.html`）实测出两处**零消费方**的前端遗留：`shared/components/GroupTreePanel.vue`（269 行，原消费方已随 `remove-legacy-element-locator-managers` 删除）与 `style.css:56-103` 的 `.soft-icon*` 家族（8 组规则，L2 删除 `mark` emoji 回退后失去最后消费方）。两者都是死代码，既不参与运行，又会让接手者误以为仍在使用，并阻碍 L3「容器 / 块 / 分栏」口径收敛。

## What Changes

- 删除 `frontend/src/shared/components/GroupTreePanel.vue`（0 引用）
- 从 `frontend/src/style.css` 删除 `.soft-icon*` 家族（8 组规则，约 48 行，0 引用）
- 同步 `frontend/AGENTS.md` L2 速查 §⑥「已知缺口」中关于 `.soft-icon*` 的表述
- **BREAKING**：无。两处均零引用、零消费方，不改任何可见行为
- 不重构 `style.css` 其它段落、不动仍被消费的令牌、不处理 L3 的其它问题（点阵 / 内边距 / 块语言）

## 关联文档

- L3 现状复盘：`dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与L3现状复盘.html`（§四 清单 · §五 破约 · §六 三步建议之 ①）
- 前端 L2 口径：`frontend/AGENTS.md` L2 速查 §⑥（`.soft-icon*` 死代码登记处）
- 说明：`dev_docs/文档编号对照表.md` 不存在，本变更无对应 PRD/ARCH/UI 编号文档；属纯死代码清理，无行为变化

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 纯删除、无行为变化，按 schema 约定在 `.openspec.yaml` 设 `skip_specs: true`）

## Impact

- 前端：`frontend/src/shared/components/GroupTreePanel.vue`（删除）· `frontend/src/style.css`（删 8 组规则）
- 文档：`frontend/AGENTS.md`（L2 §⑥ 表述同步）
- 不影响：路由、API、鉴权、模块业务代码与页面观感
- 验证范围：`cd frontend && npm run typecheck` + 构建校验 + `vue-frontend-check` 门禁
