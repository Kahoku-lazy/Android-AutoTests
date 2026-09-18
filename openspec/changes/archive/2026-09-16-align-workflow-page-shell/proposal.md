## Why

`workflow/index.vue` 是全站 20 个页根中**唯一**同时缺 `.doc-page--fixed` 与 `.wb-shell` 的页面（同模块的 `PrototypeList.vue` 反而合规），既不符合 `frontend-l2-page-region` 的骨架要求，也让它拿不到共享皮肤。更深一层：共享样式 `workbench-theme.css` 消费了只声明在 `.workflow-workbench` 内的模块令牌 —— `--ac-font` / `--ac-ink` 在另外 20 个 `wb-shell` 页根上**全仓无声明**（声明静默失效），`--ac-pin-shadow` 更导致 `AppCard` 图钉在 dashboard / report-generator / ai-assistant 上**没有硬阴影**，而同一组件在 workflow 上有。另有 `workflow/tokens.css:36` 重复声明 `--ac-accent`（柠黄覆盖了第 19 行登记的工作流天蓝，与模块色登记不符）。

## What Changes

- `workflow/index.vue` 页根补 `doc-page--fixed` 与 `wb-shell`，与其余 19 个页根对齐；删除根上被 `App.vue` 高特异性规则覆盖的失效声明 `height:100%` / `overflow:hidden`
- **修正共享皮肤的模块令牌依赖**：`workbench-theme.css` 的 `font-family` / `color` 改用共享 `--app-font` / `--ink`，不再消费 `--ac-font` / `--ac-ink`
- **把图钉硬阴影提到共享层**：新增 `:root` 组件令牌 `--comp-ac-card-pin-shadow`，`workbench-theme.css` 的 `.ac-card__pin` 改用它，消除"同一共享组件在 workflow 有阴影、其他模块无阴影"的差异
- 删除因此归零消费方的模块令牌 `--ac-font` / `ac-ink` / `ac-pin-shadow`，以及重复的 `--ac-accent`
- 页内对话框按钮补 `wb-btn`（页根获得主题作用域后，按钮随之走共享皮肤）
- **BREAKING**：无

## 关联文档

- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §3.6 / §4.1 与 §八·批次 A（P0-4）
- `dev_docs/DEV_TEST/前端UI一致性整改计划.md` 阶段 1 · `align-workflow-page-shell`
- 既有要求：`openspec/specs/frontend-l2-page-region/spec.md`「Every L2 page root provides the workbench theme scope」「L2 page roots reuse the shared page skeleton」

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l0-design-tokens`：新增要求「共享皮肤不依赖模块作用域令牌」

## Impact

- `frontend/src/modules/workflow/index.vue`（页根类、失效声明、对话框按钮）
- `frontend/src/modules/workflow/tokens.css`（删 3 条归零令牌 + 1 条重复声明）
- `frontend/src/shared/styles/workbench-theme.css`（font/color 改共享 token、图钉影改共享组件令牌）
- `frontend/src/shared/styles/tokens.css`（新增 `--comp-ac-card-pin-shadow`）
- 观感变化：dashboard / report-generator / ai-assistant 的 `AppCard` 图钉**首次出现**硬阴影；workflow 编辑器页获得共享主题作用域
- 不影响：workflow 的 `.wb-body` 画布容器例外（已登记）、节点与浮层几何、接口与数据

## 登记为后续变更的输入（本变更不做）

- `workflow` 自建 4 套按钮与 `filterCount` 等圆角字面量 → 变更 10 / 15
- `workflow/tokens.css` 其余零消费令牌（`--ac-wood` / `--ac-shadow` 等 18 条）→ 变更 14 死代码清退