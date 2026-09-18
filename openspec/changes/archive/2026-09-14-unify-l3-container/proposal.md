## Why

L3 现状复盘（`dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与L3现状复盘.html` §五 · §六 步骤 ②）实测出容器层三处未收敛：**6 处模块自绘点阵**与「点阵只由 PaperDoodles 提供」的 L0 口径冲突，而 L2 速查 §③ 又允许「主体增量：背景点阵」——**规则自相矛盾**；全局 `.doc-body` 水平内边距 32px 与页头 24px 不一致，策略① 的 report 三详情页靠模块裸覆写才对齐；**5 处裸 `.doc-body` 覆写**未按 L2 口径经模块 modifier 限定。画布页 `.wb-body` 已裁决保留为例外，但缺一条可检查的登记。

## What Changes

- 去掉 6 处模块自绘点阵：`.doc-page` ×2（`device-inspector/index.vue:170`、`dashboard/DashboardView.style.css:12`）与 `.doc-body` ×4（`case-manager/ProjectWorkspace.vue:119`、`element-locator/ProjectWorkspace.vue:109`、`element-locator/ProjectList.vue:75`、`element-locator/LocatorFileView.vue:147`），纸面统一为暖白实色 + 主区 `PaperDoodles`
- 统一点阵口径：L0 与 `.doc-body` 均不得自绘点阵；同步修正 `frontend/AGENTS.md` L2 速查 §③「主体增量」条款（移除「背景点阵」）
- 全局 `.doc-body` 水平内边距由 `--app-space-xl`(32px) 对齐到 `--app-space-lg`(24px)，与 `.wb-header` 同值（`style.css:190`）
- 5 处裸 `.doc-body` 覆写（`report-generator` ×4 + `device-inspector` ×1）收敛为 `.<模块modifier> .doc-body`，或在对齐后删除已无必要的覆写
- 把 `workflow/index.vue` 的 `.wb-body` **登记为 L3 容器例外**（保留、不并入骨架），并在 spec 中给出例外判据
- 实施后 `--app-paper-dot` 消费方归零（本变更只登记为退役候选，不删令牌）
- **BREAKING**：无接口 / 数据 / 鉴权变更；**有可见观感变化**（6 处点阵消失）

## 关联文档

- L3 现状复盘：`dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与L3现状复盘.html`（§五 第 1/2/3/6/7 条 · §六 步骤 ②）
- L2 行为契约：`openspec/specs/frontend-l2-page-region/spec.md`（「L2 page roots reuse the shared page skeleton」需增补画布页例外）
- 前端口径：`frontend/AGENTS.md`（L0 速查 ④.3 点阵禁令 · L2 速查 ③.3 主体增量 · ④.2 不自建等价骨架）
- 说明：`dev_docs/文档编号对照表.md` 不存在，本变更无对应编号文档

## Capabilities

### New Capabilities

- `frontend-l3-container`: L3 内容容器的可见行为契约 —— 纸面不含模块自绘点阵、`.doc-body` 水平内边距与页头同值、容器覆写必须经模块 modifier 限定、画布类页面主体为登记例外

### Modified Capabilities

- `frontend-l2-page-region`: 现行「L2 page roots reuse the shared page skeleton」要求主体容器 SHALL 复用 `.doc-body`，与画布页既有事实冲突；本次为该要求增补画布类页面的例外判定与登记义务（含 Scenario）

## Impact

- 前端样式：`frontend/src/style.css`（`.doc-body` 内边距）· 6 个模块样式文件（删点阵）· 5 处裸覆写收敛
- 文档：`frontend/AGENTS.md`（L2 速查 §③ 点阵条款、§④ 覆写口径）
- 令牌：`--app-paper-dot` 消费方归零（退役候选，本变更不删）
- 验证：6 个受影响页面 × 768 / 1024 / 1280 三档浏览器核验（观感变化需人眼确认）+ `npm run typecheck` + 构建 + `vue-frontend-check`
- 不影响：路由、API、鉴权、模块业务逻辑
