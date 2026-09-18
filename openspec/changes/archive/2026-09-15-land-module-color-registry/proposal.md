## Why

上一轮把 5 条 🟠 修掉后，「方向对齐 · 落地不齐」仍未解：模块内还有 **68 个未登记色值 / 117 次出现**（其中 CSS 侧 63 次），且真正的原因不是缺少令牌层次——实测**跨模块复用的色值只有 2 个**，其余 55 个都是单模块专用。缺的是**登记处**：模块遇到「一个还没被登记的颜色」时只能就近写字面量，于是令牌之外长期漂着一块平行色板。同时 `:root` 里躺着 37 个模块私有变量、94 处 `@deprecated` 别名仍在服役、`--doodle-*` 家族与新令牌并存。

## What Changes

**① 共享令牌层：让「登记处」存在且正确**

- `:root` 去模块化：`--ai-*`（35 个）迁入已存在的 `.ai-workbench` 作用域块；`--case-*`（2 个）迁入新增的 `.case-workbench` 模块作用域
  - 已排除风险：EP 2.7 `el-dialog` 的 Teleport 为 `disabled: !appendToBody`，且仓库 `append-to-body` 命中 0 → 弹层原地渲染，作用域变量可达（实测依据记入 design）
- 退役 `--doodle-*` 家族：`--doodle-bg`（=`--paper`）· `--doodle-ink`（→`--ink`）· 删除零使用的 `--doodle-radius` / `--doodle-shadow`
- 收敛 `@deprecated` 别名并删除其声明：`--app-ink-muted`→`--app-text-secondary`（同值 #999；初稿误写为 `--app-text-muted`，后者实为 #bbb）· `--app-ink`→`--ink` · `--app-accent-blue`→`--c-workflow` · `--app-green`→`--c-workflow` · `--app-blue`→`--c-element` · `--app-accent-purple`→`--app-status-purple`
- 修跨模块借用：`device-pool` 使用 `var(--ai-bg-neutral)` → `--app-bg-subtle`

**② 各模块色值登记（8 模块）**

- CSS 侧 63 处未登记字面量：按「值等于现有令牌 → 用令牌；否则 → 在消费组件自身根类上声明具名变量并引用」收敛，**不改任何色值**
- script/.ts 侧 38 处（图表系列色 / canvas 绘制色 / 节点色）：保留字面量（既有画布例外），但 MUST 集中到该模块的图表色表（`report-generator/constants.ts` 的 `CHART_COLORS`、workflow 节点色表）
- 别名替换与字面量登记同步在该模块内完成

**③ 规格与速查**

- `frontend-l0-design-tokens` 增 2 条需求：色值登记处归属 + 模块令牌家族作用域（含 Teleport 逃逸口）
- `frontend/AGENTS.md` L0 §③/④/⑤ 同步，修正 §④.3 与实现冲突的文字；L4 补图表色集中登记口径

## 关联文档

- `dev_docs/05-开发与测试/设计方案与报告/设计方案-前端L0-L5骨架层级图.html`：本轮实测数据的落盘处（复盘章节的「未收敛观察项」逐条收敛后需回写状态）
- `.agents/skills/vue-frontend-check/references/calibration.md` §2：上轮回写的 5 类量规（本变更按新量规执行，不再新增量规）
- `frontend/AGENTS.md`：L0 速查（令牌与 `:root` 口径）· L3「AppCard 外观仅在 `.wb-shell` 内生效」先例 · L4 图表色例外
- `openspec/specs/frontend-l0-design-tokens/spec.md`：上一变更新建的能力（本变更在其上追加需求）
- 说明：`dev_docs/文档编号对照表.md` 不存在；本变更为令牌登记机制落地，不改业务需求

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l0-design-tokens`: 追加「色值登记处归属」与「模块令牌家族作用域」两条需求（含图表色集中、跨模块借用禁止、Teleport 逃逸口场景）

## Impact

- 共享层：`frontend/src/shared/styles/tokens.css`（`:root` 结构重排 + 别名/家族退役）
- 模块层：8 个模块的 `.vue` / `.css`（CSS 字面量登记 + 别名替换）· `case-manager` 3 个页面根新增 `case-workbench` 类 · `report-generator/constants.ts` 与 workflow 节点色表（图表色集中）
- 文档：`frontend/AGENTS.md` · 上述 HTML 设计方案
- 门禁：因改 `:root`，需全量静态复核（模块内未登记 CSS 字面量归零、别名归零、`:root` 无模块私有变量）+ `vue-tsc`
