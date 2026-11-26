# Design: add-page-load-perf-budget

## Context

见 `proposal.md`（Why）。现状约束与实测事实：

- 采集只能来自真实浏览器：vitest 跑 jsdom（`css: false`），`vite build` 只给体积；指标来源必须是
  Navigation Timing / Paint / `PerformanceObserver`
- 项目已有 Playwright（Python `playwright` 1.65 + `pytest-playwright`），`tests/e2e` 已在用真实浏览器
- 本机 Playwright 默认 `mkdtemp` 落在 `%TEMP%` 被沙箱拒绝（EPERM）；Python playwright 要求的
  `chromium_headless_shell-1255` 未安装，只有 1228/1234 → 必须 `channel="chrome"` 或显式 executable 回退
- dev（5173，未打包 ESM）与 preview（4173，dist）数值差 3–4 倍，**同一套阈值不能通吃**

## Goals / Non-Goals

**Goals**

- 一条命令可重跑：`PERF_RUN=1 python -m pytest -c tests/pytest.ini -m perf`
- 超预算时失败信息能直接定位：哪个页面、哪个指标、实际值、预算、profile、明细路径
- 默认不拖累常规套件与 CI

**Non-Goals**

- 不做 CI 阻塞门禁（本地抖动大：同一条 LCP 在 420–940 ms 间波动；先积累数据）
- 不做 Lighthouse 综合分、不做弱网模拟（`Network.emulateNetworkConditions` 另开一单）
- 不改任何页面代码、不改体积（体积优化是后续单）

## Decisions

### D1 放 `tests/perf/`，作为第四类测试

塞进 `tests/<module>/e2e/` 会被 b2b 的定义（断言用户可见的提示词/弹窗/列表变化）绑死，而本测试断言的是数字；
塞进 `tests/arch/unit` 违反「零 I/O」。独立一层最诚实，代价是要改 `tests/AGENTS.md` 准入清单（见 proposal 变更申请）。

### D2 预算按 profile 分档，写在 `budgets.json`

`dev`（5173）与 `preview`（4173）各一份阈值；profile 由 `PERF_PROFILE` 指定，未指定时按端口推断。
理由：dev 有 74–100 个请求、7–10 MB 传输，preview 只有 12–24 个请求、2 MB 级 —— 合成一档必然误报。
首版口径为「时间类宽、传输类紧」（`lcp_ms` 2500 / `load_ms` 8000 为回归护栏，`transfer_kb` 贴近实测 ×1.1 抓膨胀）；
2026-11-26 因字体变更只重标定 `transfer_kb`，见 D7。

### D3 默认 skip，必须显式开启

`PERF_RUN=1` 或 `PERF_BASE_URL` 才执行，否则跳过并给出原因。理由：CI 无前端服务、本地无服务时全量套件不应因缺环境红；
同时避免每次全量回归多等 30 秒。

### D4 空壳页 = 失败，不是「很快」

`renderedChars == 0` 直接失败。实测踩过：dev server 504 `Outdated Optimize Dep` 时页面全白，
`load` 只有 266 ms —— 若不判空壳，会把「崩了」记成「性能很好」。

### D5 浏览器启动走 `channel=chrome` + 回退链

`launch_browser` 依次尝试 `channel`、`ms-playwright/chromium-*/chrome-win64/chrome.exe`、playwright 自带；
全失败才抛错。理由见 Context：Python playwright 与已装浏览器版本不匹配是常态。

### D6 明细写 `tests/reports/perf/`

与仓库既有「报告输出到 `reports/`」口径一致；`tests/reports/` 已被 `.gitignore` 忽略，不污染提交。

### D7 传输预算含中文字体，字体缺失则 skip（2026-11-26）

`switch-ui-font-to-harmonyos-sans`（2026-11-25 归档）把 UI 字体换成 24.1 MB 本地原始 TTF，
`transfer_kb` 从 1.2/1.4 MB 跳到 28.3/28.6 MB（preview）与 34.0/34.3 MB（dev）。需求方 2026-11-26 裁决：
**按当前字体口径放宽传输预算，并把依据写进 `budgets.json` 的 `basis`；不做字体子集化/woff2/裁剪。**

两个次生决定：
1. **`lcp_ms` / `load_ms` 不动** —— 字体是 `font-display: swap`，LCP 实测 320–564 ms 未受影响；
   抬传输预算不等于承认「首屏变慢」，只承认「首屏变胖」。
2. **字体未就位就 skip，不判通过** —— 字体二进制不入库（见 `.gitignore` 与后续字体取用单），
   缺失时服务端 404、传输只剩约 2 MB，宽预算会把「量不到」变成假绿。`conftest.py` 用
   `GET /fonts/harmonyos-sans/HarmonyOS_SansSC_Regular.ttf` 探测，非 200 即带原因 skip。

## Risks / Trade-offs

- [本地抖动导致误红] → 3 轮取中位数 + 阈值留 40% 余量；真抖动频繁再做「取 p75 或 5 轮」
- [preview 无 `/api` 代理导致 console 报错] → 判据不用 console error，用 `renderedChars` 与 `page_errors`
- [沙箱内 TEMP 不可写] → README/报告记录 `TEMP=temps\.tmp` 约定；失败信息里会带 `page_errors`
- [第四类测试让 `tests/` 分类变复杂] → 只在 `tests/perf/` 一个目录，且默认不跑，认知负担有限

## Migration Plan

1. 落 `tests/perf/` 五个文件与 `pytest.ini` marker（本变更，可回退）
2. 申请并修改 `tests/AGENTS.md` 准入清单（**先批后改**）
3. 后续单：按 `budgets.json` 驱动体积优化（echarts 模块化、element-plus CSS 按需、去掉远端字体）

**Rollback**：删目录 + 回退 marker/文档，单 commit，无数据迁移。

## Open Questions

- 阈值是否要按机器型号分档（换 CI runner 后需要重测基线）——本单先只区分 dev/preview
- 是否把「体积门禁」（gzip 上限）并入同一变更——本单只做时间，体积另开（需要 `vite build` 参与，性质不同）
