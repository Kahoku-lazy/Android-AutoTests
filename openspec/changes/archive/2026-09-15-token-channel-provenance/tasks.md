## 1. 分类复核

- [x] 1.1 复核 `temps/c2-inventory.json` 的 310 处分类，逐文件确认通道④（prop 传色 51 处 = `color` 35 + `icon-gradient` 16，跨 17 个文件）归属；验证：`模板其它` 归零、310 处均有明确属性名、无「归属不明」项（三处判据修正见 design.md 与备注）

## 2. 通道① SVG 元素属性（99）

- [x] 2.1 `shared/**` 的 SVG 属性引用改为 T0/`--comp-*`；验证：shared 内引用均可在 T0 解析
- [x] 2.2 `modules/**` + `views/**` 的 SVG 属性引用改为该边界 T1；验证：值等价校验（规范化色）通过

## 3. 通道② 模板内联 style（80）

- [x] 3.1 按边界改写模板内联 `style` 中的令牌引用；验证：值等价校验通过 + `npm run lint:styles` exit 0（D4 裁决豁免通用值后实测**需改写 0 处**：80 处全部落在「该边界 T1」34 处或「T0 通用语义与刻度」46 处）

## 4. 通道③ script 字符串（78 + 2）

- [x] 4.1 改写 script 侧令牌字符串引用（含 `.ts` 常量）；验证：值等价校验通过（D4 后实测**需改写 0 处**：78 处（另有 2 处是 JSDoc 注释里的 `var(--c-*)` 示例、非引用）全部落在「T0 通用模块色/状态色/刻度」69 处、「本模块 T1」2 处、「shared 组件载体 → `--comp-*`」7 处）
- [x] 4.2 移除脚本侧 `var(--x, #字面量)` 兜底；验证：全仓该模式命中 = 0（**实测 23 处、11 个文件**，全在 `<style>` 块与 `workbench-theme.css`；涉及 12 个被引用令牌逐个核验均已在 `:root` 登记 → 兜底不可达，零视觉变化）

## 5. 通道④ prop 传色（51）

- [x] 5.1 逐文件确认并改写 prop 传色引用（`color` 35 + `icon-gradient` 16，17 个文件）；验证：值等价校验通过 + 无跨模块 T1 借用（D4 后实测**需改写 0 处**：通用值 40 处 · 本模块 T1 2 处 · 组件载体 9 处（载体值均为 T0 原子）；跨边界借用复扫 = 0）

## 6. 门禁与关单

- [x] 6.1 `check-style-gates.mjs` 新增「非样式表载体按边界可解析」检查；验证：注入反例（跨模块 T1 引用 / 悬空引用）时 exit 非 0（新增批 3 硬门禁 G5 悬空 / G6 跨边界 / G7 模块声明持字面量；反例注入实测 exit **1** 且逐条报出，清理后 exit **0**）
- [x] 6.2 回归：`npx vue-tsc --noEmit`（基线 34 条 = tests 27 + src 7，src 7 条在本变更未触碰的文件中，改动前后一致）+ `temps/verify-colors.ps1`（裸值 0/0）
- [x] 6.3 `openspec validate token-channel-provenance --strict` 通过后归档

## 备注

### 通道① 实施记录（2026-09-15）

- 通道① 实测 **99 处 / 3 个文件**（分类修正见 design.md「通道分布」下说明）。其中 **36 处**（`shared/components/PaperDoodles.vue` 23 · `shared/components/AnimatedMascot.vue` 13）已经是合规形态：SVG 属性引用组件根类载体，载体取值指向 T0 的 `--comp-*`。**实际改动 4 行**：
  - `shared/components/PaperDoodles.vue:13` `var(--ink)` → `var(--color-ink-15)`（共享层必须引用 T0 原子或 `--comp-*`；`--ink` 是兼容别名）
  - `views/components/AnimalFace.vue:123-125` 组件根类载体 `--af-face` / `--af-ink` / `--af-blush` 的取值由 `--app-*` 别名改为 T0 原子（`--color-white` / `--color-ink-35` / `--color-red-85-s100`），满足主 spec「组件级载体同样引用原子」
  - `AnimalFace` 的 `--af-color` 无声明，由父级 `LoginView` 经 `color` prop 注入（`var(--c-*)`）→ 归通道④
- 核验：值等价 4/4 OK · `npm run lint:styles` exit 0（声明 394 · 颜色原子 198 · 复合值 3 · 存量别名 48）· `temps/verify-colors.ps1` → `hex_bare=0` / `rgba_bare=0` / `decl_lines=626` · `npm run typecheck` 34 条（tests 27 + src 7）
- 顺带修正自有诊断脚本缺陷：`temps/verify-colors.ps1` 的 `APP_CODE_ERRORS` 过滤模式用反斜杠匹配 `modules\\`，而 vue-tsc 输出为正斜杠路径，导致该计数恒为 0（此前记录的「应用 0」基线由此而来）；已改为 `modules[/\\]`，实测为 7。
- 后续通道见下方各节记录。

### 通道② 实施记录（2026-09-15，已完成）

- 分类修正后通道② 实测 **80 处 / 7 个文件 / 4 个边界**：ai-assistant 57 · report-generator 18 · shared 3 · workflow 2。
- 引用档位实测（逐处归类，无跨边界借用）：
  1. `--ai-*` 模块家族 **31 处**（`--ai-warm-bg` 6 · `--ai-ink-subtle` 9 · `--ai-ink-muted` 8 · `--ai-ink-soft` 6 · `--ai-warm-border` 2）——声明在 `modules/ai-assistant/tokens.css`，**已是规范要求的形态，无需改动**
  2. 同文件 scoped 组件载体 **3 处**（`--rg-status-pass-bg` / `--rg-status-fail-bg`，T1′，形态合规）
  3. T0 通用语义与刻度 `--app-*` **39 处**（字号 `--app-size-sm/xs` 25 · 状态与文本色 12 · `--app-space-md` 1 · `--app-bg-card` 1）
  4. 模块色别名 `--c-workflow` **5 处**（`AppSidebar` 3 · `EvaluatorTab` 1 · `TaskReport` 1）· `--app-error` 1 处
- **已完成（独立于口径的缺陷修复）**：`modules/report-generator/ReportDetail.vue:316,372` 的**自引用兜底** `var(--app-status-danger-text, var(--app-status-danger-text))` → `var(--app-status-danger-text)`。HEAD 原值是 `var(…, #a03030)`，该畸形是本方变更 C 的脚本文本替换字面量时产生的（`git diff` 可证，属「清理自己造成的混乱」）；全仓复扫该模式 **= 0**。
- **口径冲突已裁决（D4，2026-09-15）**：通用语义与刻度（状态色 / 文本层级 / 字号 / 基础量 / 模块色 `--c-*`）豁免「必须落本模块 T1」，任何边界可直取 T0；规格已加「例外」条款与 Scenario「通用语义与刻度直取 T0」。据此那 44 处**保持原样**，3.1 以「需改写 0 处」关单。
- 核验：`npm run lint:styles` exit 0 · `temps/verify-colors.ps1` → `hex_bare=0` / `rgba_bare=0` · `npm run typecheck` 34 条（tests 27 + src 7，与基线一致）
- **顺带登记的观察（不归通道②）**：`modules/report-generator/TaskReport.vue:339` 的 `--rg-status-fail-bg:rgba(232,95,95,0.12)` 属「模块前缀声明持字面量」，违反主 spec「模块令牌值引用主 token」；门禁 G3 漏检它的原因见 6.1 记录（**批 2 的声明扫描只作用于 `tokens.css`**，并非「行中声明」问题；此前那条判断是误判，已在 6.1 记录中纠正）。同类的还有 `--rg-shadow-soft:rgba(0,0,0,0.04)`（`index.vue:371` / `ReportDetail.vue:437`）。这些在 `<style>` 块内，留作任务 6.1 门禁升级的输入。

### 通道③ + 通道④ 实施记录（2026-09-15，已完成）

- 通道③（script 侧）实测 **80 处 / 16 个文件**：`.vue` 的 `<script>` 55 处 · `.ts` 25 处。其中 2 处是 JSDoc 注释里举例的 `var(--c-*)`（`AppCard.vue:16` / `SketchCard.vue:17`），不是引用。78 处引用的档位：T0 通用 69（模块色 `--c-*` 59 · `--app-*` 8 · `--app-status-*` 2）· 本模块 T1 2（`--ai-teal` / `--ai-teal-hover`）· shared 组件载体 7（`--ss-type-*` 6 → `--comp-ss-type-*` · `--wb-icon-gradient-end` 1 → `--comp-wb-icon-gradient-end`）。**需改写 0 处。**
- 通道④（prop 传色）实测 **51 处 / 17 个文件**：`color` 35 · `icon-gradient` 16。档位：T0 通用 40（模块色 `--c-*` 39 · `--app-status-purple` 1）· 本模块 T1 2 · 组件载体 9（`--case-icon-accent` 3 · `--locator-header-icon-end` 3 · `--sv-icon-grad-end` / `--td-icon-grad-end` / `--wf-header-icon-end` 各 1，载体取值逐个核验均为 `var(--color-*)`）。跨边界借用复扫 = 0。**需改写 0 处。**
- 任务 4.2 的「全仓 `var(--x, #字面量)` = 0」口径下额外清理 **23 处、11 个文件**（全部在 `<style>` 块与 `workbench-theme.css`，非脚本/模板）：`device-inspector` 5 文件 · `shared/components` 5 文件（`DoodleBtn` / `KpiCard` / `RateBar` / `SketchCard` / `patterns/ErrorState`）· `shared/styles/workbench-theme.css`。**安全依据**：涉及的 12 个被引用令牌（`--app-highlight` / `--app-bg-card` / `--paper` / `--app-marker-red` / `--c-case` / `--app-live` / `--c-workflow` / `--app-error-bg` / `--c-device` / `--c-runner` / `--app-queue-text` / `--app-btn-hover-danger`）逐个核验均在 `shared/styles/tokens.css` 的 `:root` 有声明 → 兜底分支不可达，零视觉变化；复扫该模式 = 0。
- 核验：`npm run lint:styles` exit 0 · `temps/verify-colors.ps1` → `hex_bare=0` / `rgba_bare=0` / `decl_lines=626` · `npm run typecheck` 34 条（tests 27 + src 7，与基线一致）
- **新登记的观察（门禁盲区，留作 6.1 输入）**：`verify-colors.ps1` 的「已登记」判定是「该字面量字符串在 `tokens.css` 里出现过」→ 凡已登记过的字面量在**消费位置**再写一遍都不会被报（如 `KpiCard.vue:356` `background:#fff`、`AppSidebar.style.css:51/318` `background:#fff`、`dashboard/DashboardView.style.css:128-132` 的 `color-mix(…, #fff)`）；门禁 G2 只检查**自定义属性声明**，也不覆盖消费位置。实测样式块内非自定义属性声明处的裸色字面量 **33 处**（另 1 处命中的 `workflow/tokens.css:19` `#89CFF0` 在行尾注释里，属误报）。故「`hex_bare=0`」应读作「**未登记**字面量 = 0」，不等于「消费位置无字面量」。该清单已在任务 6.1 纳入门禁（只降不增，实测 33 处）。

### 任务 6.1 实施记录（2026-09-15，门禁升级）

- `frontend/tests/check-style-gates.mjs` 新增**批 3（硬门禁）**三组检查：
  1. **G5 悬空引用**：非样式表载体的 `var(--x)` 在全仓无任何声明
  2. **G6 跨边界借用**：`--x` 只声明在其它边界（其它模块 T1 / views / shared 组件载体），而调用点不在该边界
  3. **G7 模块前缀声明持字面量**：`--(ai|case|rg|di|wf|views)-*` 的声明值不以 `var(` 开头
- 载体口径：`<style>` 块之外的 `var(--…)` —— `.vue` 取 style 块之外（块内字符替为空格以保留行号）· `.ts/.js` 全文 · 跳过注释行（否则 JSDoc 里举例的 `var(--c-*)` 会误报 2 处）。边界判定：`modules/{m}` → m · `views` / `shared` 各自成界 · 其余归 root；T0 落点 = `shared/styles/**` 与 `src/style.css`。**运行时注入的载体**（`:style="{ '--x': v }"` / `style="--x: v"`）视为在本组件声明 —— 否则 `views/components/AnimalFace.vue` 的 18 处 `--af-color` 会被误报。
- **反例注入实测**（临时文件 `modules/report-generator/__gate-injection.vue`，跑完立即删除并 `Test-Path` 复核为 False，无残留）：exit **1**，逐条报出 G5（`var(--no-such-token)` → 全仓无声明）· G6（`var(--ai-warm-bg)` → 仅声明于 `[ai-assistant]`，越界借用）· G7（`--rg-injected-literal = #ff0000`）；清理后 exit **0**。
- 顺带把此前的观察**落地**并新增一条清单：
  - G7 的扫描范围由「仅 `tokens.css`」扩到**全仓** `.vue/.css` 的声明位置 → 暴露 3 处真实违规，已按**等值原子**修复（零视觉变化，原子值经规范化比对相等）：`TaskReport.vue:339` `--rg-status-fail-bg: rgba(232,95,95,0.12)` → `var(--color-red-65-s75-a12)` · `index.vue:371` 与 `ReportDetail.vue:437` 的 `--rg-shadow-soft: rgba(0,0,0,0.04)` → `var(--color-black-a04)`
  - 「消费位置裸色字面量」纳入**只降不增存量清单**（实测 **33 处**，如 `KpiCard.vue:356` / `AppSidebar.style.css:51,318` 的 `background:#fff`、`dashboard/DashboardView.style.css:128-132` 的 `color-mix(…, #fff)`）。**未阻断**：这 33 处需逐处改 `var(--color-*)`，超出本变更「非样式表载体」的 premise，留给后续变更；门禁现在会持续报出该计数。
- **纠正此前两处误判（实事求是）**：
  1. 通道② 记录曾写「门禁 G3 漏检是因为声明扫描器只认行首 `--name:`」——**错**。对 `scanDeclarations` 做单测确认：行中声明（`.case-status-text{--x:…;--y:…}`）**会被接受**；真实原因是 **批 2 的声明扫描只作用于 `tokens.css`**（`tokenDecls = scanDeclarations(tokensCss)`），全仓 `.vue` 此前只进批 1 的字号扫描。
  2. 因此「G7 扩到全仓」不是新增规则，而是把既有规则落到它本就该覆盖的文件上。
- 门禁当前输出：`批 3 · 非样式表载体 306 处：悬空引用 0 · 跨边界借用 0 · 模块声明持字面量 0` + `存量清单：消费位置裸色字面量 33 处（只降不增、未阻断）`。
- 回归：`npm run lint:styles` exit 0 · `temps/verify-colors.ps1` → `hex_bare=0` / `rgba_bare=0` / `decl_lines=626` · `npm run typecheck` 34 条（tests 27 + src 7，与基线逐条一致）
### 关单记录（2026-09-15）

| 验证项 | 结果 |
|---|---|
| 分类复核 | 310 处全部有明确属性名（3 次判据修正：「模板其它」50 → 25 → **0**） |
| 通道① SVG 属性 | 99 处 / 3 文件 · 需改写 4 行 · 档位解析 violations = 0 |
| 通道② 模板内联 style | 80 处 / 7 文件 · 需改写 0 处 · 修掉自引用兜底 2 处 |
| 通道③ script 侧 | 78 处引用 / 16 文件 · 需改写 0 处（另 2 处为 JSDoc 示例） |
| 通道④ prop 传色 | 51 处 / 17 文件 · 需改写 0 处 · 跨边界借用 = 0 |
| 字面量兜底 | 全仓 23 处 → **0**（11 文件；12 个被引用令牌均在 `:root` 登记 → 兜底不可达、零视觉变化） |
| 模块前缀声明持字面量 | 3 处 → 0（`--rg-status-fail-bg` / `--rg-shadow-soft` ×2，均改为**等值原子**） |
| 门禁 | 新增批 3 硬门禁 G5 悬空 / G6 跨边界 / G7 模块声明持字面量；反例注入 exit 1 且逐条报出，清理后 exit 0 |
| 门禁输出 | `批 3 · 非样式表载体 306 处：悬空引用 0 · 跨边界借用 0 · 模块声明持字面量 0` |
| 存量清单 | 消费位置裸色字面量 **33 处**（只降不增、未阻断；超出本变更 premise，留给后续变更） |
| 回归 | `npm run lint:styles` exit 0 · `verify-colors.ps1` hex_bare 0 / rgba_bare 0 / decl_lines 626 · `typecheck` 34 条（tests 27 + src 7，逐条与基线一致） |
| 规格同步 | 主 spec `frontend-l0-design-tokens` 12 → **14** 条（新增 `非样式表载体按边界溯源令牌` / `脚本侧令牌字符串不得携带字面量兜底`） |
| 构建 / 浏览器 | 未做（`vite build` 仍被沙箱拦 · 无浏览器）；以值等价 + 门禁 + `vue-tsc` 三重静态核验替代 |
| 自纠 | 2 处误判已纠正：①「门禁只认行首声明」实为批 2 只扫 `tokens.css`；②「`hex_bare=0`」实为「**未登记**字面量 = 0」 |
