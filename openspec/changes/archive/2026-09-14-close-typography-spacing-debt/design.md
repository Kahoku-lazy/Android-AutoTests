## Context

动机与逐项判定见 `proposal.md` - Why。两项债都需用户裁决，已确认：

1. `gap:14px` ×6 → `--app-space-md`（12px）
2. 字号：删死声明 + 等值换令牌 + `11px` → 12px + 图形字号登记例外；`13px` → `--app-size-xs` · `15px` → `--app-size-md`

约束：等值替换必须**零视觉变化**；任何非等值替换都要在交付说明里标为「可见变化」并给浏览器核验点。

## Goals / Non-Goals

**Goals:**

- 关掉二.1（字号未走令牌）与二.7（裸 px 间距）两项门禁债
- 让「图形/展示级字号」例外有正式载体（令牌注释 + AGENTS 条款 + 门禁量规三处一致）

**Non-Goals:**

- 不为图形字号新增令牌家族（如 `--app-icon-size-*`）
- 不扩大扫描到 `padding` / `margin` / `width` 等其它裸 px（各自独立，不在本次请求内）
- 不改 `EmptyState.vue` 的 40px（图形字号，登记为例外）

## Decisions

### 1. 64px 是死声明 —— 用选择器权重证明后删除

- **选择**：删 `font-size:64px`，保留 `opacity:0.5` 与 `margin-bottom`
- **理由**：全仓只有 `shared/components/patterns/EmptyState.vue:3` 渲染该 class，而该组件 scoped 样式给选择器叠加了组件作用域属性（0,2,0），恒高于 `tokens.css` 的全局规则（0,1,0）→ 64px 永不生效
- **备选**：把 64px 改成令牌保留 —— 保留一个永不生效的声明，否决

### 2. 等值与不等值分开处理

- **等值（12px → `--app-size-xs`、14px → `--app-size-sm`）**：直接换，视觉恒等
- **不等值（11→12 · 13→12 · 15→16）**：按用户裁决换，标注可见变化
- **理由**：等值换令牌把 7 处字面量清零且零风险；不等值项只有用户能定方向

### 3. 间距取 `--app-space-md`

- **选择**：`gap:14px` → `var(--app-space-md)`（12px）
- **理由**：实测同文件相邻规则普遍是 12px（`report-generator/index.vue:379,390` · `ChatView.css:37` · `EvaluatorTab.vue:439`），模块内 gap 令牌用量也以 `--app-space-sm` / `--app-space-md` 为主；14→12 让同文件间距一致
- **备选**：`--app-space-lg`（16px）—— 与相邻 12px 规则不一致，全仓仅 2 处，否决

### 4. 图形/展示级字号例外（三处登记，口径一致）

- **选择**：`--app-size-*` 管**文本**字号；图形/展示级字号（树节点图标 18px · 空态 emoji 40px · 404 数字 96px）允许字面量
- **载体**：`tokens.css` 刻度注释（规则原位）· `frontend/AGENTS.md` 硬性规范第 14 条（项目口径）· `calibration.md` §2（门禁判罚）
- **理由**：这三处表达的是**图形尺寸**而非文本层级，硬塞进 6 档字号刻度会污染刻度语义；同时必须让门禁知道该判 ✅，否则每次体检都重复报同一条
- **顺带修正**：`calibration.md` 原写「见 `frontend/AGENTS.md` §2」—— 该文件并没有 §2 风格条款（字号规则实际在 `tokens.css` 注释里），一并改为指 AGENTS 第 14 条 + 刻度注释

### 5. 验证口径

- 零变化项：静态证明（值等值 / 权重恒压）
- 可见项：`vue-frontend-check` 静态扫描 + **用户浏览器核验**（间距 −2px ×6、字号 +1 / −1px ×4）
- 门禁：typecheck / 构建 / §7 扫描（改动范围内 `font-size:\s*\d+px` 与 `gap:\s*\d+px` 应为 0，登记的图形字号除外）

## 模块防火墙自检

- 跨 App import：不涉及（纯样式）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- 所有 INSERT/UPDATE/DELETE 收敛到 api.py：不涉及（无写操作）
- 前端不直连数据库；仪表盘不做写操作：不涉及

## Risks / Trade-offs

- [不可见的视觉回归] → 等值项以值相等证明；不等值项幅度 ≤ 2px 且逐条列核验点
- [例外口径被滥用] → 例外只覆盖「图形/展示级」，并写明判定语（表达图形尺寸而非文本层级）；文本字号仍必须走刻度
- [门禁与规则再次不一致] → 三处载体在同一次变更内同步（`tokens.css` / `AGENTS` / `calibration`）

## Migration Plan

1. 批量替换代码（等值换令牌 + 间距 + 不等值字号）
2. 登记例外：`tokens.css` 注释 → `frontend/AGENTS.md` 第 14 条 → `calibration.md` §2
3. 同步两份报告的 gap 条目与本变更记录
4. `npm run typecheck` + `npx vite build --mode development` + §7 扫描
5. 回滚：`git checkout` 9 个源码文件 + 3 个文档（两份报告被 gitignore，需手工回退）
