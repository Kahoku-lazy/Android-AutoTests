## Why

令牌分层与资产卫生已收敛（变更 A/B/C），但**非样式表载体**仍未按边界溯源：实测 **310 处** `var(--…)` 出现在 `<style>` 块之外（37 个文件），其中 shared 95 处、ai-assistant 83 处、views 69 处。它们目前各自就近引用（有的直接引用 T0 组件名、有的引用模块兼容别名），没有「模块内引用本模块 T1 / 通用层引用 T0」的统一口径，静态也查不出来。

## What Changes

- 为 310 处非样式表载体建立**唯一溯源口径**：调用点在 `modules/**` 或 `views/**` → 引用该边界的 T1 场景令牌；调用点在 `shared/**` → 引用 T0（颜色原子或 `--comp-*`）
- 按通道分批改写引用：SVG 元素属性 99 · 模板内联 style 71 · script 字符串 78 · script 其它 2 · prop 传色 35 · 模板其它 25
- script 侧返回的令牌字符串 MUST NOT 携带字面量兜底（`var(--x, #fff)`），与变更 C 的口径一致
- 门禁升级：新增「非样式表载体引用必须能在该边界解析」的静态检查（按边界 + T0 双层解析）
- 零视觉变化：只改引用名，不改任何色值/字号

## 关联文档

- 架构方案：`dev_docs/05-开发与测试/设计方案与报告/设计方案-前端设计令牌分层与数据链.md` §3.1 溯源判定树 / §5 现状映射
- 前置变更：`2026-09-15-atomize-shared-design-tokens` · `2026-09-15-module-token-files` · `2026-09-15-clean-style-asset-hygiene`
- 无 PRD/ARCH 编号：样式引用口径收敛，无功能与视觉变化。

## Capabilities

### New Capabilities

- （无）

### Modified Capabilities

- `frontend-l0-design-tokens`: **ADDED** 2 条需求——非样式表载体按边界溯源 · 脚本侧令牌字符串不得带字面量兜底。

## Impact

- 37 个文件（8 边界）；其中 shared 95 处与 views 69 处占比过半
- `frontend/tests/check-style-gates.mjs`（新增按边界解析检查）
- 不改令牌名与值；不改组件结构与模板语义