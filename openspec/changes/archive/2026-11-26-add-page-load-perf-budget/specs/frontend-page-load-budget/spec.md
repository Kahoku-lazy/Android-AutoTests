## Purpose

给前端页面建立可复跑的加载时间与传输预算：用真实浏览器取 Navigation Timing / Paint / LCP / 资源体积，
按环境分档登记阈值，超预算即失败。它补上「后端接口预算」之外缺的那半：用户真正感觉到的是首屏多久可用，
而这件事只有真实浏览器能回答。

## ADDED Requirements

### Requirement: 页面加载时间必须由真实浏览器采集

加载指标 SHALL 来自真实浏览器（Playwright），MUST NOT 用 jsdom 或构建产物体积代替。
每轮测量 MUST 使用独立的浏览器上下文（冷缓存），MUST 采集以下值：`ttfb`、`fcp`、`lcp`、`dcl`、`load`、
资源请求数、传输字节数、`cls`，以及页面渲染字符数（`renderedChars`）。

LCP SHALL 通过 `PerformanceObserver` 的 `largest-contentful-paint`（`buffered: true`）在页面脚本执行前注册采集，
MUST NOT 只在 `load` 之后读一次快照。

#### Scenario: 冷缓存上下文逐轮独立

- **WHEN** 对同一路径连续测量 3 轮
- **THEN** 每轮使用新建的浏览器上下文，且各轮明细（时间、请求数、传输量）分别保留可追溯

#### Scenario: LCP 在 load 之后仍能取到

- **WHEN** 页面首屏大图或图表在 `load` 之后才出现
- **THEN** 报告中的 `lcp` 反映该元素出现时刻，而不是 `null` 或 `load` 时刻

### Requirement: 加载预算按环境分档并在超限时失败

阈值 SHALL 登记在 `tests/perf/budgets.json`，至少区分 `dev`（未打包 dev server）与 `preview`（生产构建）两档，
每档按路径登记 `lcp_ms`、`load_ms`、`transfer_kb`、`requests` 四项上限。

单次测量 SHALL 取多轮中位数与预算比较；任一指标超限 MUST 判定失败，失败信息 MUST 包含路径、指标名、
实际值、预算值与所用 profile，并 MUST 指向明细报告路径。

#### Scenario: 超预算失败且信息可定位

- **WHEN** `/login` 的 `lcp` 中位数超过该 profile 的 `lcp_ms`
- **THEN** 用例失败，信息含 `lcp`、实际值、预算值、profile 名与报告文件路径

#### Scenario: 未登记路径不误判

- **WHEN** 某 profile 未登记某路径的预算
- **THEN** 该路径用例被跳过并说明原因，而不是按空预算通过

### Requirement: 空壳页面必须判失败

测量 SHALL 记录页面渲染字符数；当所有轮次的渲染字符数为 0 时，用例 MUST 失败并提示可能原因，
MUST NOT 以「加载很快」通过。

#### Scenario: 白屏不被记成高性能

- **WHEN** dev server 因依赖预构建失效导致全站 504、页面无任何文本
- **THEN** 用例失败并输出页面异常信息，而不是报告一个很小的 `load` 值

### Requirement: 性能测试默认不参与常规测试

性能测试 MUST 以独立 marker 登记，并且在未显式开启（未设置 `PERF_RUN=1` 或 `PERF_BASE_URL`）时跳过，
MUST NOT 让 `python -m pytest -c tests/pytest.ini` 的默认结果、CI 的测试收集门禁或本地全量回归因缺少前端服务而失败。

#### Scenario: 默认套件不执行性能用例

- **WHEN** 在未设置 `PERF_RUN` 与 `PERF_BASE_URL` 的环境中运行全量 pytest
- **THEN** 性能用例显示为跳过，其余用例结果与引入本能力前一致

#### Scenario: 显式开启后按预算校验

- **WHEN** 设置 `PERF_RUN=1` 且前端在线，运行 `-m perf`
- **THEN** 每条已登记路径各自产出一份明细报告并接受预算断言

### Requirement: 报告落盘且不污染版本控制

每次运行 SHALL 把明细写入 `tests/reports/perf/`，内容至少含 profile、预算、汇总统计与逐轮原始数据。
该目录 MUST 已被版本控制忽略。

#### Scenario: 明细可复查

- **WHEN** 查看 `tests/reports/perf/page-load-dashboard.json`
- **THEN** 能读到 profile、四项预算、汇总的 median/min/max 与每一轮的原始采集值
