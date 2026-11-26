# Proposal: add-page-load-perf-budget

## Why

平台没有任何「页面加载时间」信号：`vite build` 只报产物体积，vitest 跑在 jsdom 里测不到加载，
`platform-load-budget` / `dashboard-load-performance` 两份规格守的全是后端指标（SQL 条数、接口进程内耗时、缓存 TTL）。
结果是首屏传输 1.99 MB（`/login`）/ 2.35 MB（`/dashboard`）没人拦，LCP 从 500 ms 涨到 2 s 也不会红。

2026-11-24 用临时探针实测（`temps/perf_probe.py`，证据在 `temps/perf-probe/REPORT.md`）：
生产构建下 `/login` LCP 676 ms、`/dashboard` LCP 568 ms，ttfb 仅 4 ms —— 时间全花在 JS 体积与执行上。
本变更把该探针**收编为 `tests/` 里的常驻性能测试**，让「加载变慢」可度量、可回归、可追责。

### 预算重标定（2026-11-26，需求方裁决）

2026-11-25 归档的 `switch-ui-font-to-harmonyos-sans` 把全站 UI 字体改为**本地原始 TTF**
（`HarmonyOS_SansSC_Regular/Semibold/Bold`，合计 24.1 MB，随服务同源分发、不做切片与转码）。它使
「首屏传输 1.99 MB」这个旧基线**结构性作废**：冷缓存首屏会把三档字重全部拉下来，`transfer_kb` 量级从 MB 级跳到 25 MB 级。

需求方裁决（2026-11-26）：
**按当前字体口径使用，放宽 `tests/perf` 的 `transfer_kb` 预算并把「为什么是这个数」写清，不为字体引入子集化/woff2/裁剪。**

重标定依据（本机实测，Windows 11 / Chrome stable headless / 冷缓存上下文 1 轮预热 + 3 轮取中位数）：

| profile | 路径 | 实测 `transfer_kb` 中位数 | 旧预算 | 新预算（×1.1 向上取整到 100） |
|---|---|---:|---:|---:|
| preview（`vite build` + `vite preview`） | `/login` | 25 699 | 1 200 | **28 300** |
| preview | `/dashboard` | 25 912 | 1 400 | **28 600** |
| dev（`vite --host` 未打包） | `/login` | 30 853 | 8 000 | **34 000** |
| dev | `/dashboard` | 31 115 | 11 000 | **34 300** |

`lcp_ms`（实测 320–564 ms）/ `load_ms`（443–705 ms）/ `requests`（18–107）三档**沿用原值不改**：
字体走 `font-display: swap`，首屏绘制不被 24 MB 阻塞；本机 loopback 带宽下 `load` 仍是百毫秒级。
因此本预算守的是**「又变胖」的回归**，不是「广域网首屏 25 MB 要 20 秒」这件事——
后者需要字体子集化才能解，属于需求方明确排除的方向，已在 `budgets.json` 的 `basis` 里写明。

配套口径：字体二进制**不入库**（缺失时服务端 404、传输只剩约 2 MB，宽预算就变成假绿），
因此 `tests/perf` 在字体未就位时**显式 skip 并说明原因**，不把「量不到」当通过。

## What Changes

- 新增 `tests/perf/`：`page_load.py`（采集引擎）、`conftest.py`（会话夹具与可达性判定）、
  `budgets.json`（按 `dev` / `preview` 两档登记阈值）、`test_page_load_budget.py`（2 条用例：`/login`、`/dashboard`）
- `tests/pytest.ini` 增加 marker：`perf: 页面加载性能预算 — 真实浏览器取 Navigation Timing / LCP（需运行中的前端，PERF_RUN=1 显式开启）`
- 默认**不参与**常规测试与 CI 收集语义：未设置 `PERF_RUN=1` 或 `PERF_BASE_URL` 时用例 `skip`，
  `python -m pytest -c tests/pytest.ini` 的默认结果不变（只多收集这 2 条、执行 0 条；2026-11-26 实测全量收集 587 条）
- 运行方式：`PERF_RUN=1 python -m pytest -c tests/pytest.ini -m perf`；需要前端已启动
- 每次运行把明细写入 `tests/reports/perf/page-load-{login,dashboard}.json`（该目录已被 `.gitignore` 忽略）

**判据（一次测量内）**：至少 3 轮冷缓存上下文 → 取中位数 → 对 `lcp_ms` / `load_ms` / `transfer_kb` / `requests`
逐项与预算比较；空壳页（`renderedChars == 0`）直接判失败。

## 变更申请（AGENTS 准入清单，按根 `AGENTS.md` 第 4 条：先批后改）

`tests/AGENTS.md` 的红线 1 是「**只收三类**：功能灰盒 / 浏览器 b2b / 落库校验」。性能测试是第四类，
必须改这条准入清单才能与代码一致。

| 项 | 内容 |
|---|---|
| **改什么** | `tests/AGENTS.md` 红线 1 由「只收三类」改为「只收四类：功能灰盒 / 浏览器 b2b / 落库校验 / 页面加载性能预算（`tests/perf/`，默认不跑）」；「三类测试怎么落地」表加一行 `perf`；`pytest.ini` 的 marker 说明同步 |
| **为什么必须改** | 不改则代码里多出第四类用例，红线却写「只收三类」；后来者要么删掉性能测试、要么按旧红线拒绝维护，口径直接冲突 |
| **影响面** | 所有读 `tests/AGENTS.md` 的 AI/人；CI 不受影响（perf 默认 skip，不进 `pytest-collect` 的执行面）；默认套件只多收集 2 条 perf 用例 |
| **怎么回退** | 删 `tests/perf/`、回退 `pytest.ini` 的 `perf` marker、回退 `tests/AGENTS.md` 那一条；单 commit `git revert` 即可 |

> **未获批准前：`tests/perf/` 代码与 marker 已落（可运行、可单独跑），`tests/AGENTS.md` 一字未改。**

## Capabilities

### New Capabilities

- `frontend-page-load-budget`：前端页面的加载时间与传输预算——采集口径、预算分档、超预算失败、空壳判定、
  默认不参与常规测试

### Modified Capabilities

（无 —— 本变更只新增前端加载预算，不改 `platform-load-budget` / `dashboard-load-performance` 两份后端口径）

## Impact

- 测试资产：+5 个文件（`tests/perf/{__init__,page_load,conftest,test_page_load_budget}.py` + `budgets.json`）
- 配置：`tests/pytest.ini` 一个 marker
- 运行环境：需要 Playwright 浏览器（`channel=chrome`；沙箱内需把 `TEMP` 指到可写目录）、运行中的前端
- 默认门禁：`python -m run check` 的 `pytest-collect` 仍绿（perf 只收集不执行，默认全绿靠的是自动 skip）
- 不引入新依赖：`playwright` / `requests` 已在 `requirements.txt`
