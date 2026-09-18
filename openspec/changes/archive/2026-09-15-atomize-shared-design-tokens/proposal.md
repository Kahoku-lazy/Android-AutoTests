## Why

前端主 token（`frontend/src/shared/styles/tokens.css`）目前混装三种语义——原子色值、场景名（`--app-status-*` / `--app-pass-*`）、模块名（`--c-dashboard…`），同值重复 **22 组**（按色值归一化统计为 **35 组**），且 `--el-*` 覆盖直写同值。结果是：改一个色要改多处、同一个值有多个名字、无法回答「这个颜色属于谁」，模块层因此各自写死字面量（全仓颜色字面量声明 **252 条 / 唯一色值 199 个**）。

## What Changes

- 在共享层建立 **T0 主 token 四档**：颜色原子 `--color-*`（全部字面量色值的唯一登记处）· 排版原子 `--font-*` / `--font-size-*` · 基础量原子 `--space/--radius/--shadow/--duration/--ease/--size-*` · 通用组件配色 `--comp-<组件>-<场景>`
- 颜色原子命名规则：`--color-<色相>-<明度>[-s<饱和>][-a<透明度>]`，中性为 `--color-white` / `--color-black` / `--color-ink-<明度>`；**主 token 内 SHALL NOT 出现场景名或模块名**
- **BREAKING（仅对主 token 的写法，不影响视觉）**：`tokens.css` 现有场景名/模块名声明一律改为指向 T0 原子的 `var()` 别名，消费点与本轮引用零改动
- `--el-*` 覆盖（35 条）的值 MUST 改为 `var(--color-*)`，不再直写字面量
- 消除主 token 内同值重复（22 组；含 `#f7c948`×3 · `#6bcb77`×3 · `#ffb5a7`×3 · `#ffffff`×3 · `#999`×3 …）
- 新增静态门禁：G1 主 token 同值重复 = 0 · G5 新增原子名不得含模块前缀（`--el-*` 是 EP 框架名，本变更只改其值为 `var()`；遗留场景名别名由变更 B 归位）· G4 组件层裸色值 = 0（沿用）
- 零视觉变化：不改任何色值、字号、间距、圆角、阴影取值

## 关联文档

- 目标架构与数据链：`dev_docs/05-开发与测试/设计方案与报告/设计方案-前端设计令牌分层与数据链.md`（本轮新增，含 T0/T1/T2 边界、数据链、作用域表、门禁与变更切分）
- 口径真相源：`openspec/specs/frontend-l0-design-tokens/spec.md`
- 分层规范：`frontend/AGENTS.md` L0 §②（唯一令牌登记处）/ §④.3（模块家族令牌不在 `:root`）· skill `doodle-craft`
- 无对应 PRD/ARCH 编号：本变更为前端样式层的结构重构，不改变任何对外功能与视觉表现，故不涉及需求或架构变更。

## Capabilities

### New Capabilities

- （无）本变更不引入新能力，只补充既有能力的需求。

### Modified Capabilities

- `frontend-l0-design-tokens`: **ADDED** 4 条需求——颜色原子唯一登记 · 主 token 命名不含场景/模块 · 通用组件配色档 · EP 覆盖引用原子；不改动既有 3 条（模块令牌家族作用域于模块根）。

## Impact

- `frontend/src/shared/styles/tokens.css`（主战场：165 条声明 / 158 条字面量）
- `frontend/src/shared/styles/workbench-theme.css`（11 条字面量）· `frontend/src/shared/styles/motion.css`（7 条字面量）
- 40 个 `.vue` 的组件级载体声明（约 148 行）——本变更**只登记原子**，不改其引用（归变更 B）
- `frontend/tests/check-style-gates.mjs`（新增 G1/G5 门禁）
- 不受影响：后端 `apps/`、API 契约、路由、任何组件模板与视觉表现；消费点引用在本变更内保持可用（旧名 = 别名）
- 依赖关系：变更 B（模块 token 文件化）与 C（管道溯源）依赖本变更先产出原子；本变更不依赖其他变更