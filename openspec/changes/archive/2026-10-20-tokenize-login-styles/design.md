## Context

登录页样式由两块承载：`views/LoginView.style.css`（`<style scoped>`）与 `views/styles/auth-form-card.css`（非 scoped，被 `LoginCard` / `RegisterCard` 各自 `@import` 一次）。

现状中的三处问题，动机见 `proposal.md - Why`：

1. `LoginView.style.css` 的 `--login-dash: var(--comp-sidebar-dash)` —— 登录页的虚线由侧栏令牌代持。
2. 三处 `2.5px` 描边宽度字面量（`.hero-cta`、`.meeting-doodle` 经借用令牌、`.form-submit .el-button`）。
3. `auth-form-card.css` 的 `margin: -var(--app-space-sm) 0 0 28px` 是非法 CSS——`var()` 不能直接取负，整条声明被丢弃，负外边距从未生效。

已有约束：`tokens.css` 只登记了工作台实线的 `--size-border-width: 3px`，没有手绘 2.5px 描边的规格原子；`check-style-gates` 校验字号、调色板、令牌引用完整性与几何尺度（阴影 / 圆角 / 时长），**不校验线型**。

## Goals / Non-Goals

**Goals:**

- 登录页的线型与描边宽度由登录页自己持有，不再借用共享/侧栏令牌。
- 新增的 2.5px 描边原子成为下一步"全站虚线换铅笔实线"的唯一宽度来源。
- 除一处非法声明被修正外，`/login` 的可见外观零变化。

**Non-Goals:**

- 不做全站线型切换，不改侧栏、卡片、弹窗、表纸的线型。
- 不改阴影、圆角、字号、间距刻度。
- 不重命名 `--comp-sidebar-dash` / `--comp-sheet-border` / `--comp-dialog-border`。
- 不令牌化登录页的一次性装饰几何（胶带 72px、圆点 10px、横线本 31/32px、Hero 栅格 1120/520/420px）。
- 不处理 `auth-form-card.css` 被两个组件重复 `@import` 的重复注入。

## Decisions

### D1 新增 `--size-stroke-sketch: 2.5px`，而不是复用 `--size-border-width: 3px`

3px 是工作台卡片的实线边框，2.5px 是手绘描边，二者是两种规格而非同一个值的别名；合并会把现有卡片的描边改粗。

**备选**：直接在登录页本地声明 `--login-stroke-width: 2.5px`。否决——下一步全站切换时还要再提升为原子，等于同一改两遍。原子按 `--size-*` 命名，符合主 token 命名规则且不含模块前缀。

### D2 线型令牌只落在 `.login-page` 作用域，不引入全局 `--line-style`

本单的边界是"把登录页的决定搬回登录页"。全局 `--line-style` 属于下一步（全站默认实线、登录页覆盖回虚线），提前引入会让两个变更互相耦合，也让本单的"外观零变化"验收变模糊。

登录页先声明 `--login-line: dashed`；下一步只需在 `:root` 增加 `--line-style: solid`，把登录页的 `--login-line` 改为 `var(--line-style)` 再覆盖回 `dashed`，改动面仍在一处。

### D3 用组合令牌 `--login-border` 承载"宽度 + 线型 + 颜色"

`--login-border: var(--size-stroke-sketch) var(--login-line) var(--ink)`。虽然当前只有 `.meeting-doodle` 一处消费，但它把登录页描边的三个来源收在一条声明里：下一步调整任一来源时，登录页不需要逐处改。`border-style` 单独可写的地方（`.hero-cta--ghost`）只引用 `var(--login-line)`，不复制整条描边。

**备选**：消费处直接写 `var(--size-stroke-sketch) var(--login-line) var(--ink)`。否决——同一条三元组在多个规则里重复，正是本单要收敛的形态。

### D4 修正 `-var()` 为 `calc(-1 * var(--app-space-sm))`

`-var(...)` 不合法，浏览器丢弃整条 `margin` 声明。修正后 `field-error` 的 8px 上移会真正生效，这是本单**唯一**被接受的可见变化——它恢复的是作者原本的意图，而不是引入新设计。

**备选**：直接删除该负外边距。否决——删除会丢掉"错误文案贴近输入框"的排版意图，与相邻表单的间距语言不一致。

### D5 不动 `auth-form-card.css` 的双重 `@import`

两个组件各引一次导致样式重复注入，属于构建层问题，与本单的令牌收敛无关；在本单顺手改会把验收面扩大到组件加载行为。

## 模块防火墙自检

本设计是纯前端样式与令牌改动：

- 无跨 App import，无新增后端依赖。
- 无 ORM 读写、无数据库变更、无接口变更。
- 前端不直连数据库；本单不触及任何请求链路。

## Risks / Trade-offs

- [组合令牌只有一个消费点，可能被评审视为过度抽象] → 它承载的是边界级决定而非复用；下一步全站切换时即为第二个消费依据，届时若仍无第二个消费点，可降级为消费处内联。
- [修正 `-var()` 导致 `field-error` 上移 8px，与本单"外观零变化"口径冲突] → 在验收中以截图标注这一处为预期差异；若评审认为该负边距不该存在，回退方案是删除该声明而非保留 `calc()`。
- [`--comp-sidebar-dash` 的名字仍把"dash"写进标识符，与值耦合] → 下一步全站切换时随 `--line-style` 一并改名；本单刻意不动，以免把改动面扩到侧栏与 11 处引用。
- [门禁不校验线型，回归只能靠人眼与 spec] → 本单补的两条 spec 场景即为人工核对清单；后续全站切换时再加线型门禁。
