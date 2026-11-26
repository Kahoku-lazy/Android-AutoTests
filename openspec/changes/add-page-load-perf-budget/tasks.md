# Tasks: add-page-load-perf-budget

> 格式：**动作 → 完成判据**。0 组是硬门控（`tests/AGENTS.md` 红线），1–4 组已落地，5 组留给后续体积优化。

## 0. 前置（硬门控）

- [x] 0.1 `tests/perf/` 五件套与 `pytest.ini` marker 落地，`PERF_RUN=1` 下单跑通过。
  判据：`PERF_RUN=1 python -m pytest -c tests/pytest.ini -m perf -q` → `2 passed`。
- [x] 0.2 **变更申请获批**（2026-11-24 需求方「执行」）：proposal §变更申请 四要素经需求方确认后，才改 `tests/AGENTS.md` 的红线 1（只收三类 → 四类）。
  判据：批准记录（对话原话或 PR approve）——**未获批前该文件不动**。

## 1. 采集引擎

- [x] 1.1 `tests/perf/page_load.py`：`INIT_SCRIPT`（LCP/CLS observer、`buffered: true`）、`COLLECT_SCRIPT`
  （navigation / paint / resource / `renderedChars`）、`login_tokens`、`seed_script`、`launch_browser` 回退链。
  判据：`python -m pytest -c tests/pytest.ini --collect-only -q` 收集到 2 条 perf 用例且无 import 错误。
- [x] 1.2 `measure_path` 每轮新建 `browser.new_context()`（冷缓存），`goto(wait_until="load")` + `settle_ms` 后再取数。
  判据：`tests/reports/perf/page-load-login.json` 的 `rows` 里每轮都有独立 `run` 与 `transfer_kb`。

## 2. 用例与预算

- [x] 2.1 `budgets.json` 登记 `dev` / `preview` 两档，键为 `lcp_ms` / `load_ms` / `transfer_kb` / `requests`。
  判据：两档都能被 `load_budgets(profile)` 读出；`/login` 与 `/dashboard` 均有四项。
- [x] 2.2 `test_page_load_budget.py` 参数化 `/login` `/dashboard`：3 轮取中位数、逐项比对、失败信息含
  实际值 / 预算 / profile / 明细路径；`renderedChars == 0` 先失败。
  判据：把某档 `lcp_ms` 临时改小（如 1）后运行，断言失败信息含 `lcp` 与预算值；改回后 `2 passed`。

## 3. 默认行为与文档

- [x] 3.1 `tests/pytest.ini` 注册 `perf` marker（`--strict-markers` 下不报未知 marker）。
  判据：全量 `--collect-only -q` 无 `PytestUnknownMarkWarning`。
- [x] 3.2 未设 `PERF_RUN` / `PERF_BASE_URL` 时用例 skip。
  判据：不带环境变量运行 `-m perf` → `2 skipped`，且全量收集数为 543（= 541 + 2）。
- [x] 3.3 `tests/AGENTS.md` 准入清单加第四类 `perf`（依赖 0.2 获批）。
  判据：红线 1 含 `tests/perf/`，且「三类测试怎么落地」表出现 perf 行。

## 4. 验收

- [x] 4.1 实测跑通：`PERF_RUN=1 ... -m perf` → `2 passed`，报告落到 `tests/reports/perf/`。
  判据：`page-load-login.json` 与 `page-load-dashboard.json` 存在且 `checks` 段含 budget 与 actual。
- [x] 4.2 默认门禁不受影响：`python -m run check` 的 `pytest-collect` 仍绿。
  判据：该 gate 通过（收集 543，perf 不执行）。

## 5. 后续（另开变更，不在本单）

- [ ] 5.1 preview 场景参数化：一条命令完成 `vite build → vite preview → 探针 → 关服`。
- [ ] 5.2 体积门禁：把 `dist/assets` 的 gzip 上限并入 `utils/check_gates.py`。
- [ ] 5.3 按本单暴露的三大体积来源做优化：echarts 全量导入（1.04 MB）、`element-plus/dist/index.css`（397 KB）、
  Google Fonts 远端样式（渲染阻塞 + 内网不可用）。
