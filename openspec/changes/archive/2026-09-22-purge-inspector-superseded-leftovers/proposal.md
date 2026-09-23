## Why

对设备检查器前端做了一次「需求变更后被替代的代码有没有删掉」的系统排查（工具：`temps/fe_dead_code_scan{,2,3,4}.py`，静态取证 + 真浏览器复核）。JS 层是干净的（ESLint 的 `@typescript-eslint/no-unused-vars` 已开启，模块内 0 未使用变量），但**三处被需求变更替代的代码留在原地**：

| # | 位置 | 曾服务 | 现状证据 |
|---|---|---|---|
| 1 | `StructureAnalysisPanel.css:147-150` + `:156-164`（`.sap-label-hit` 与其 `td:has()` 规则） | **第一代「标识」列**的整格双击命中区（注释原文：「标识文字只有一行高，双击落在格子上下空白时也要打到这一格」） | 全仓（含 `frontend/tests`）只命中这两处 CSS 自身，**没有任何模板/脚本加这个类**；当前 15 列与 15 个 `#cell-*` 插槽一一对应，它是 CSS 里唯一「模板从不出现」的 `sap-*` 类 |
| 2 | `tokens.css:13` `--insp-pad-filter`；`:25-26` `--insp-pad-hint` / `--insp-hint-gap` | 前两者是**已删除的筛选栏**（8 个页签 + 搜索框）的内边距；后两者是**第一代面板顶部提示**（WebView / 结构分析提示）的内边距 | 全仓 `var(--insp-pad-filter\|--insp-pad-hint\|--insp-hint-gap)` 命中 **0**，只有声明处各一处 |
| 3 | `ScreenshotView.vue:38-39`（`visibleRectCalls`）、`:332/341/352/354`（`rectCalls` 计数）、`:429-430`（`defineExpose`） | 「可见层单次绘制矩形数」的**测试自检钩子** | 全仓引用只有这 5 处，**零消费者**：没有测试或组件读过 `visibleRectCalls`（对应走查在 `rework-inspector-layers-view` 里未执行） |

成因一致：这些代码在各自那一轮是活的，随后列集合 / 筛选栏 / 提示 / 走查被替代，**载体删了、附属物没删**。

## What Changes

1. 删除 `.sap-label-hit` 的整块样式（含 `td:has(.sap-label-hit)` 定位基准规则与它的注释）；**保留**紧邻的 `td:has(.sap-thumb-cell)` 规则（那条仍在用）。
2. 删除三个零引用令牌（`--insp-pad-filter` / `--insp-pad-hint` / `--insp-hint-gap`），并同步 `--insp-gap-row` 上方那句已不成立的消费点枚举（「工具条 / 筛选栏 / 分页栏」→「工具条 / 分页栏 / 快照抽屉」）。
3. 删除 `ScreenshotView` 的 `visibleRectCalls` 自检面：`ref` 声明、`rectCalls` 计数（`let rectCalls = 0` 与两处 `+= 2`）、`defineExpose`。

**运行时行为零变化**：第 1 项的类从未被任何元素挂上（删的是永不匹配的选择器）；第 2 项无 `var()` 消费；第 3 项从被读取过。删除只让代码变短，不改任何可见行为。

## 关联文档

- PRD-03（设备检查器）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无；本变更为**纯清理**，不改变任何需求级行为，`.openspec.yaml` 已声明 `skip_specs: true`）

## Impact

- 前端 3 个文件：`frontend/src/modules/device-inspector/components/StructureAnalysisPanel.css`、`frontend/src/modules/device-inspector/tokens.css`、`frontend/src/modules/device-inspector/components/ScreenshotView.vue`
- 测试：无新增/删除（三处均无任何用例覆盖，删除后既有 50 个文件 / 256 个用例应保持全绿）
- 不涉及：后端、接口、规格、其它模块、共享件

## 明确移出本变更范围（排查中同时发现，本次不动）

- **命名漂移**：`.sap-sections` / `.sap-sections-title` / `.sap-sections-empty` 三个类名仍是「分区（sections）」时代的名字，现在内容是「元素分组」（在用、名不符）。
- **冻结链路**：「保存到元素定位」与「已保存页面」入口灰键导致的 UI 不可达链路 —— `store.ts:36-44` 的注释写明是**故意冻结 + 解冻步骤**，且规格明文要求「已保存页面入口的既有代码路径 MUST 保留」。
- **其它模块的既有死令牌**：`ai-assistant/tokens.css` 19 个 `--ai-status-*`、`workflow/tokens.css` 20 个 `--ac-*`（与本轮需求变更无关）。
- **共享图标库 45 导出 / 26 未引用**：已用 `git grep HEAD` 核实它们在 HEAD 就未被引用，非本轮造成，且属共享资产。
- **规格死指针**：`openspec/specs/frontend-l0-design-tokens/spec.md:22` 仍指向已删除的 `PageElementsPanel.vue`（需 spec delta，属另一单）。
