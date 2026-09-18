# 设计：门禁加固

## Context

门禁 `frontend/tests/check-style-gates.mjs` 此前已有的批次：批 1（字号下限，告警）、批 2（T0 主 token 唯一性与引用完整性）、批 3（载体边界解析）。前三个批次覆盖了颜色与令牌引用，但**真实样式代码本身**不在扫描范围内，且阴影模糊、圆角字面量、动效时长三类没有校验。

本轮先做**探测**再定规则：先用只报告不阻断的临时逻辑统计三类几何字面量的真实存量（137 处命中），据此区分「已登记的合法例外」与「待修违规」，再写白名单与硬门禁。避免先写规则、再猜存量。

## Goals / Non-Goals

- Goals：让门禁覆盖全部样式载体；让阴影模糊 / 圆角 / 动效时长有可阻断的自动校验；让门禁的「存量清单」都是只降不增的上限。
- Non-Goals：不改设计令牌的取值与刻度；不做间距与边框宽度门禁（「第二套间距尺度」与 5 种边框宽度尚无登记清单，属另一变更）；不重构第三方（Element Plus）覆盖策略。

## Decisions

### D1 引用完整性必须扫描 `.css` 全文与 `.vue` 的 `<style>` 块

原实现有两处豁免：`carrierRefs` 对 `.css` 直接 `return []`，并把 `.vue` 的 `<style>` 块整体替换为空格；调用方 `walk(SRC, CARRIER_EXTS)` 的 `CARRIER_EXTS` 也不含 `.css`。两处叠加的净效果是**真实样式代码零覆盖**。

**选择**：删除类型豁免，逐行扫描；载体遍历扩为 `.vue/.css/.ts/.js`。

**理由**：样式表正是令牌引用的主战场，恰恰最需要完整性检查。历史上的悬空令牌正是活在这个盲区里。

**代价**：载体引用基数从 2661 升至 3909 处，门禁运行时间略增（整脚本仍在秒级）。

### D2 运行时注入按**边界**汇集，而不是按文件

改为全量扫描后立刻出现 8 处悬空 + 4 处跨边界。逐一核实后确认它们**全部是误报**：项目把样式拆到同目录的 `X.style.css`，注入点在 `.vue`、消费点在 `.css`。

- `--mod-color`：`shared/components/AppSidebar.vue` 注入 → `AppSidebar.style.css` 消费
- `--mc-color`：`modules/ai-assistant/components/ToolboxPanel.vue` 注入 → `ToolboxPanel.style.css` 消费
- `--device-table-min-width` / `--device-table-body-rows`：`modules/device-pool/index.vue` 注入 → `DevicePoolView.style.css` 消费
- `--ac-accent` / `--ac-tilt`：`shared/components/AppCard.vue` 注入 → `shared/styles/workbench-theme.css` 消费

**选择**：注入名按 `boundaryOf(rel)` 汇集。

**理由**：批 3 的其余判定本就是边界口径（`sites.has('t0') || sites.has(boundary)`），注入沿用同一口径才自洽；同时不会让 A 模块的注入去正当化 B 模块的引用。仅「按目录」不够——`AppCard.vue`（`shared/components/`）与 `workbench-theme.css`（`shared/styles/`）不同目录却同边界。

**已知近似**：同一边界内任一 `.vue` 的注入都会让该边界内同名引用合法。残差被限制在单个边界内，且注入本就是运行时值，门禁无法静态验证其取值。

### D3 几何尺度用白名单 + 已登记例外，而不是「一律禁止字面量」

137 处命中的绝大多数是**设计本身要求**的字面量：正圆 `50%`、细小构件 `1px/2px/3px/5px`、清零 `0`、非对称纸张角 `0 3px 3px 0` 等。若一律禁止，门禁会立刻产生大量无法消除的噪音，最后被迫放宽——反而失去意义。

**选择**：分两张表——`RADIUS_FIGURE`（图形量：`0`、`1px`、`2px`、`3px`、`5px`、`50%` 及其 `!important` 形式）与 `RADIUS_SHAPE`（独立造型：`0 3px 3px 0`、`0 4px 0 0`、`3px 5px`、`8px 16px 6px 14px`、`14px 20px`、`18px 26px`）。清单外的字面量一律阻断。

**等价四值展开单独判定**：`A B A B` 与 `A B` 渲染完全等价，是可删除的冗余，因此不进入白名单，折叠为两值后以两值形式登记。

### D4 动效时长例外只保留已登记的循环装饰动画

`1.4s`（骨架 shimmer）与 `1.5s`（实时脉冲）是无限循环装饰动画，且都已有 `prefers-reduced-motion` 降级，故登记为例外。其余裸时长必须取自 `--app-duration-*`。

**据此发现 3 处刻度外时长**：`RateBar` 的 `0.3s` ×2、`motion.css` 的 `0.22s` ×2，而时长刻度只有 `0.12s/0.15s/0.25s`。**均收敛到 `--app-duration-slow`（0.25s）**，属有意的视觉变更（详见 proposal 的视觉影响列）。此前它们被「值内含 `var(` 就整体跳过」的旧规则隐藏。

### D5 画布字号保留存量上限，不纳入 12px 硬下限

ECharts / VueFlow 的驼峰 `fontSize` 共 18 处（其中 7 处为 `10px`）。字号在这里是图形绘制参数（轴标签），不是排版字号，且已有独立的视觉基准。

**选择**：批 1b 记录总数上限 18、低于 12px 计数上限 7，超出即阻断；不阻断存量本身。

### D6 批 1 由告警改为阻断

存量已为 0，告警模式等价于不设防。`--strict` 开关随之删除（没有需要降级的批次）。

## Risks / Trade-offs

- **扫描基数增大**（2661 → 3909）意味着门禁更容易因跨边界引用而变红。这正是目的，但新增模块时需注意把令牌落在正确边界。
- **注入按边界汇集**存在前述近似残差（限于单一边界内）。
- **时长变更可感知**：`0.3s → 0.25s`、`0.22s → 0.25s` 会让进度条填充与卡片悬浮略快。这是把刻度外时长收敛回刻度的必然结果，已在 proposal 中列明。

## Verification

```
cd frontend
node tests/check-style-gates.mjs      # EXIT=0，批 1/1b/2/3/4 全通过
npm run lint:styles                   # LINT=0
npx vite build --mode development      # BUILD=0（34.21s）
```

加固后的门禁读数：批 3 载体 3909 处（悬空 0 / 跨边界 0 / 模块声明持字面量 0）；批 4 通过；批 1b 画布字号 18 处（< 12px 7 处）；批 1 通过。

### 反证测试（每条新规则都必须能被证明会咬）

用「插入 → 必须失败 → 精确移除 → 必须恢复全绿」的方式逐条验证，共 3 组：

| 探针 | 注入内容 | 期望 | 实测 |
| --- | --- | --- | --- |
| A | `.vue` 的 `<style>` 块内 `var(--gate-probe-a)` + `.css` 内 `var(--gate-probe-b)`（均全仓无声明） | 2 处 G5 阻断 | 2 处，行号准确（`ErrorState.vue:42`、`DashboardView.style.css:237`），EXIT=1 |
| B | `box-shadow: 0 0 4px var(--ink)` + `border-radius: 7px` + `transition: all 0.9s` | 3 处阻断（G12/G13/G14） | 3 处，EXIT=1 |
| C | 图表配置新增 `fontSize: 9` | 批 1b 超上限阻断 | 19 处 > 18、8 处 > 7，EXIT=1 |

探针 A 的**第一版曾证明盲区未修完**：`.vue` 的 `<style>` 块已被抓到，但 `.css` 那一条没有——因为调用方遍历仍用不含 `.css` 的 `CARRIER_EXTS`。修好后两条都被抓到。探针 A、B、C 移除后重跑恢复 EXIT=0，`grep gate-probe` 残留 0。
