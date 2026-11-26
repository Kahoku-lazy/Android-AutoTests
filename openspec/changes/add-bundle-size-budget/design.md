# Design: add-bundle-size-budget

## Context

见 `proposal.md`（Why）。关键事实（2026-11-25 实测，preview 构建）：

- 入口 JS `index-*.js` gzip 44.4 KB；入口 CSS gzip 55.4 KB；最大单块 `useECharts` gzip 194.4 KB；JS 总量 gzip 570.3 KB（59 个文件）
- 体积与加载时间强相关但不相等：`tests/perf` 已覆盖「时间 + 传输」，但它要浏览器与服务，进不了每次提交
- `utils/check_gates.py` 已有 `vite-build` gate（`npx vite build`），本 gate 可以直接复用它的产物

## Goals / Non-Goals

**Goals**

- 提交前 1 秒内回答「这次改动有没有让首屏变胖」
- 失败信息能区分是「入口变胖」（用户首屏）还是「某个懒加载块变胖」（局部页面）
- 不引入新依赖（只用标准库 `gzip` / `json` / `re`）

**Non-Goals**

- 不做时间断言（那是 `tests/perf` 的事）
- 不做逐模块归属统计、不做历史趋势
- 不卡死阈值到「不能加任何东西」——预算按基线 × 1.1，留正常迭代余量

## Decisions

### D1 四条指标：入口 JS / 入口 CSS / 最大单块 / JS 总量

入口两项读 `dist/index.html` 的 `script[src]` 与 `link[href]`——它们决定用户首屏必须下载什么；
最大单块盯「某个功能吞掉一个 chunk」；总量盯「零散膨胀」。四者互补，任一超限即失败。

### D2 预算写在 `frontend/bundle-budgets.json`

与构建配置同目录，改阈值只动一个 JSON；文件里同时写 `baseline` 字段（当前实测值）与 `budget`，
这样「为什么是这个数」有据可查，不靠口头约定。

### D3 dist 缺失才构建，存在则直接量

`vite-build` gate 已确保产物新鲜；本 gate 只在 `--only bundle-budget` 或单独运行时才自己补一次构建，
避免每次 `run.py check` 多花 15 秒。

### D4 统计口径用 gzip level 9 复算，不信 vite 的打印

vite 打印的 gzip 与服务器实际压缩比可能不同；统一用 `gzip.compress(data, 9)` 复算，保证跨机器可比。

## Risks / Trade-offs

- [阈值定得太紧，正常迭代频繁红] → 基线 × 1.1，且 baseline 与 budget 同文件可见，调阈值需附理由
- [构建产物哈希变化导致文件识别失败] → 只按 `index.html` 的引用识别入口，不依赖哈希命名；缺引用时 gate 报错而不是静默通过
- [CI 里 dist 不存在] → 脚本自带一次构建兜底

### D5 入口口径修正：预载块必须计入（2026-11-26）

首版实现只读 `<script src>`，而 Vite 会把首屏要用的 chunk 写成 `<link rel="modulepreload">`。
后果实测：`element-plus` 手工分块产生的 296.7KB（gzip）**一直在首屏被下载**，却从未被 `entry_js_kb` 计过——
只要把大块「做成预载」，指标立刻显得漂亮。design D1 原文写的是「读 `script[src]` 与 `link[href]`」，
是实现漏读了预载链接，属实现偏离设计。

修正后同一份产物两种分块策略的实测（Windows 11 / `npx vite build` / 脚本复算 gzip level 9）：

| 分块策略 | entry_js（新口径） | 其中脚本 | 其中预载 | entry_css | largest | total | 首屏请求 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A 保留 element-plus 手工分块 | **386.3** | 12.9 | 76.3 + 296.7 | 55.4 | 296.7 | 706.1 | 15 |
| B 去掉该手工分块（本单采纳） | **133.5** | 57.2 | 76.3 | 55.4 | 194.4 | 573.9 | 18 |

B 把 Element Plus 交回按路由拆分：入口脚本变大（12.9 → 57.2），但首屏必载 JS 少 **252.8KB（−65%）**。

时间侧对照（`tests/perf`，preview，冷缓存 3 轮中位数）：

| 页面 | 变体 | LCP | load | transfer_kb | requests |
|---|---|---:|---:|---:|---:|
| /login | A | 396 | 574.7 | 25 946 | 15 |
| /login | B | 360 | 520.6 | 25 699 | 18 |
| /dashboard | A | 452 | 735.8 | 26 161 | 27 |
| /dashboard | B | 340 | 685.2 | 25 912 | 29 |

时间与传输都没有被牺牲（transfer 少约 250KB 正是那块预载；总传输仍被 24MB 字体主导）。

## Migration Plan

1. 落 `bundle-budgets.json` + `utils/check_bundle_budget.py`
2. 注册 gate（`check_gates.py`）与 CI
3. 验收：`python utils/check_gates.py --only bundle-budget` 绿；把某条预算临时调小后应红

**Rollback**：删两个文件与两处注册，单 commit。

## Open Questions

- 是否要按路由归属拆分统计（例如「登录页首屏」单列）——本单不做，等出现长期争议再加
