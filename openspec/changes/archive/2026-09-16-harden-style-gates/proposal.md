# 门禁加固：覆盖全部样式载体 + 几何尺度只降不增

## Why

`frontend/tests/check-style-gates.mjs` 是前端样式一致性的唯一自动门禁（`npm run lint:styles`），但它在两处存在缺口，使《前端UI风格一致性分析-2026-09》记录的问题可以绕过门禁长期存活：

1. **检查盲区**：引用完整性检查（G5/G6）曾对 `.css` 文件直接返回空、并把 `.vue` 的 `<style>` 块整体替换为空格，且载体遍历只覆盖 `.vue/.ts/.js`。结果是**全部真实 CSS 与 `<style>` 块从未被扫描**——纳入扫描的载体引用只有 2661 处，真实为 3909 处。
2. **缺门禁类别**：阴影模糊半径、圆角字面量、动效时长三类完全没有自动校验，只能靠人工巡检发现（前三个批次的同类问题都是这样被发现的）。
3. **批 1 未阻断**：字号下限门禁默认只告警，需 `--strict` 才阻断，CI 中等于不设防。

## What Changes

- 引用完整性改为**逐行扫描全部样式载体**：`.css` 全文、`.vue` 的模板/脚本与 `<style>` 块；载体遍历扩展为 `.vue/.css/.ts/.js`。载体引用覆盖 2661 → 3909 处。
- 运行时注入的自定义属性名（`:style="{ '--x': v }"`）改为**按边界汇集**后参与判定。样式常被拆到同目录的 `X.style.css`，注入点与消费点不在同一文件（例如 `shared/components/AppCard.vue` 注入 `--ac-accent`/`--ac-tilt`，由 `shared/styles/workbench-theme.css` 消费）。按边界汇集与批 3 其余判定同口径，也避免 A 模块的注入去正当化 B 模块的引用。
- 新增批 4「几何尺度」硬门禁：`box-shadow` 模糊半径必须为 0；`border-radius` 字面量必须属于图形量白名单或已登记造型；`transition`/`animation` 简写中的裸时长必须取自 `--app-duration-*`（例外：已登记的循环装饰动画 `1.4s`/`1.5s`）。
- 批 1 由告警改为硬门禁；新增批 1b 画布字号存量上限（ECharts/VueFlow 的驼峰 `fontSize` 共 18 处，其中 < 12px 7 处），只降不增、不阻断。
- 修复门禁新捕获的既有违规，见 Impact。

## Impact

门禁捕获并修复的既有违规：

| 位置 | 违规 | 处置 | 视觉影响 |
| --- | --- | --- | --- |
| `TaskAttemptCard.vue` ×4 | `var(--ai-warm-border, var(--app-border))`、`var(--ai-sticky-bg, var(--app-bg-muted))` 的兜底令牌全仓无声明 | 删除死兜底，与本模块同侪写法一致 | 无（兜底从未生效） |
| `LoginView.style.css:152` | `18px 26px 18px 26px` 等价四值展开 | 折叠为 `18px 26px` | 无（CSS 展开等价） |
| `LoginView.style.css:185` | `14px 20px 14px 20px` 等价四值展开 | 折叠为 `14px 20px` | 无（CSS 展开等价） |
| `SkeletonCard.vue:51` | `3px 5px 3px 5px` 等价四值展开 | 折叠为 `3px 5px` | 无（CSS 展开等价） |
| `RateBar.vue:54/60` | `width 0.3s` 刻度外时长 | `var(--app-duration-slow)`（0.25s） | 有：0.3s → 0.25s |
| `motion.css:74` | `0.22s` ×2 刻度外时长 | `var(--app-duration-slow)`（0.25s） | 有：0.22s → 0.25s |

- 仅前端样式层与测试脚本；无后端、无 API、无依赖变更。
- `check-style-gates.mjs` 的 `--strict` 开关被移除：批次均为硬门禁，不再需要降级选项。
- 圆角字面量白名单（图形量 `0/1px/2px/3px/5px/50%`、已登记造型 `0 3px 3px 0`、`0 4px 0 0`、`3px 5px`、`8px 16px 6px 14px`、`14px 20px`、`18px 26px`）成为门禁的一部分：新增字面量必须显式登记。
