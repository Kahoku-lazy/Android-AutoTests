## Context

见 `proposal.md` - Why。分类由 `temps/c2-inventory.mjs` 单一方法产出（脚本产物 `temps/c2-inventory.{md,json}`），口径：遍历 `frontend/src/**` 的 `.vue/.ts/.js`，排除 `<style>` 块内的 `var(--…)`，其余按「所在 SFC 块 + 所在属性名」归类。

### 通道分布（实测）

| 通道 | 出现次数 |
|---|---|
| SVG 元素属性 | 99 |
| 模板内联 style | 80 |
| script 字符串 | 78 |
| prop 传色（`color` / `icon-gradient`） | 51 |
| script 其它 | 2 |
| **合计** | **310** |

### 边界分布（实测）

| 边界 | 出现次数 |
|---|---|
| shared（通用层，引用 T0） | 95 |
| ai-assistant | 83 |
| views | 69 |
| report-generator | 33 |
| dashboard | 7 |
| case-manager / device-inspector / element-locator | 6 / 6 / 6 |
| workflow | 5 |

> **分类修正**（实施通道① 时发现，复算脚本 `temps/c2-inventory.mjs`）：
> ① 初版按「属性名启发式」归类，把组件标签上的 `color` 属性（27 处：`KpiCard` 22 + `AnimalFace` 5）误计入「SVG 元素属性」。判据补为「属性名 ∈ SVG 属性集 **且** 标签名 ∈ SVG 元素白名单」，SVG 通道 126 → 99、prop 传色 8 → 35。
> ② 初版把 `.ts` 文件（无 SFC 块结构）的令牌引用误计入「模板其它」，25 处改归 script 侧：script 字符串 53 → 78、模板其它 50 → 25。
> ③ 初版判定属性名时要求「值里不含引号」，含内层字符串的绑定形态（`:style="{ … 'var(--x)' … }"`）被误判进「模板其它」→ 改为「取该出现点之前最后一个 `attr=`」。25 处归位：9 处 `:style` 归通道②、16 处 prop 绑定（`:color` / `:icon-gradient`）归通道④，**「模板其它」归零**，310 处全部有明确属性名（无归属不明项）。
> 修正后计数：SVG 99 · 内联 style 80 · script 字符串 78 · script 其它 2 · prop 传色 51 = 310。

## Goals / Non-Goals

**Goals:** 310 处载体按边界引用正确层级的令牌 · 门禁可静态验证 · 零视觉变化。
**Non-Goals:** 不改令牌值/名 · 不新增令牌 · 不把非样式表载体改成样式表（介质保留，仅约束出处）· 不动业务逻辑。

## Decisions

### D1 · 介质保留、出处收敛
模板/属性/脚本是 Vue 给的合法出口，本变更**不消除**它们，只约束引用层级（与方案 §3.1 判定树一致）。

### D2 · 按通道分批，先低风险后高风险
顺序：① SVG 元素属性（99，纯静态属性值）→ ② 模板内联 style（71）→ ③ script 字符串（78 + 2）→ ④ prop 传色与模板其它（35 + 25）→ ⑤ 门禁。理由：前三类改写是纯文本替换且可静态验证；prop 类需判断「传的是令牌名还是语义 tone」，风险最高。

### D4 · 通用语义与刻度不落模块 T1（2026-09-15 裁决）

实施通道② 时发现字面口径与主 spec 第 1 条、`frontend/AGENTS.md` §④.3 冲突：若把状态色 / 文本层级 / 字号 / 基础量 / 模块色（`--c-*`）也按「模块内必须引用本模块 T1」处理，就要为 8 个模块各加一层**同值转写**令牌——通道② 一项即涉及 44 处引用、约 10 条新令牌，且 report-generator 需新建 `modules/report-generator/tokens.css`。

**裁决：豁免。** T1 只承载模块**专属**场景（`--ai-warm-bg` / `--ai-status-conn-text` 这类）；跨模块通用值在任何边界直取 T0。依据：

1. 主 spec 第 1 条已把 `--c-*` / `--app-status-*` / `--app-text-*` / `--app-size-*` 列为模块样式**应取**的已登记令牌；
2. `shared/components/AppSidebar.vue:172,187,200` 的 `var(--c-workflow)` 是 `frontend/AGENTS.md` §L1④.1 登记的 MOD_COLORS 兜底色，改裸原子会把「默认取 workflow 模块色」的语义改没；
3. 同值转写令牌违反主 spec「同值只登记一次」，且与「简单胜于复杂 / 不接受过度设计」相悖。

规格已按此修订：`specs/frontend-l0-design-tokens/spec.md` 的需求正文加「例外（跨模块通用值）」条款，并新增 Scenario「通用语义与刻度直取 T0」（含 MUST NOT 同值转写）。

### D3 · 引用层级判定
调用点在 `modules/{m}/**` 或 `views/**` → 该边界 T1（无对应场景则先在 T1 增一条，组合 T0）；调用点在 `shared/**` → T0 原子或 `--comp-*`；Teleport 目标 → 引用全局 T0（作用域可达性优先于层级）。

## 模块防火墙自检

| 红线 | 本变更 |
|------|--------|
| 跨 App import / 写库 / 前端直连数据库 | 不涉及（仅前端样式引用名与门禁脚本） |
| 新增依赖 | 无 |

## Risks / Trade-offs

- [310 处跨 37 文件，逐处改写易误改语义] → 按通道分批、每批独立校验；值等价（规范化色）作为硬门禁
- [将 T0 引用改成 T1 时，若某处实际在两个模块共用会引入跨模块借用] → 先在 T1 增条目并保持值来源为 T0；出现第二模块消费时回退为 T0/`--comp-*`
- [构建级验证缺失] → `vite build` 仍被沙箱拦（spawn EPERM）；以值等价 + 门禁 + `vue-tsc` 三重核验替代
- [大量模板改动无法在本环境做浏览器核验] → 分通道提交，每通道保留可回滚边界

## Migration Plan

1. 复核分类（`temps/c2-inventory.json`）；三次判据修正后 310 处均有明确属性名（「模板其它」归零）
2. 通道① SVG 元素属性 → 通道② 模板内联 style → 通道③ script 字符串 → 通道④ prop 传色（①②③④ 均已完成：① 改 4 行 · ② 修 1 个缺陷 · ③④ 需改写 0 处 · 4.2 另清 23 处字面量兜底）
3. 每个通道后跑：值等价校验 + `npm run lint:styles` + `npx vue-tsc --noEmit`
4. 门禁升级并归档
5. 回滚：按通道粒度 `git revert`

## Open Questions

- canvas/ECharts 图表色表（模块内字面量）是否纳入本变更或单列 —— 现状是 L4 已登记的例外（**仍未决**）
- ~~通道④ 的 prop 传色是否统一为「语义 tone 名」（需组件 props 口径一并调整）~~ —— **已由 D4 消解**：prop 传的是通用模块色（`--c-*`，39 处）或本模块/组件载体（11 处），均符合 D4；无需改组件 props API，故不再需要 tone 名化。