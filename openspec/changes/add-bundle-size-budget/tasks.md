# Tasks: add-bundle-size-budget

- [x] 1.1 `frontend/bundle-budgets.json`：四条 `baseline`（2026-11-26 主干 `82a3e252` CI 构建实测：入口 JS 12.8、入口 CSS 55.6、最大块 368.7、总量 873.2 gzip KB）与四条 `budget`（×1.1 向上取整：15 / 62 / 406 / 961）。原 2026-11-25 数字（44.4 / 55.4 / 194.4 / 570.3）测于带未合并前端改动的工作区，主干不可复现，已作废。
  判据：`python -c "import json;d=json.load(open('frontend/bundle-budgets.json'));print(d['budget'])"` 输出四项。
- [x] 1.2 `utils/check_bundle_budget.py`：解析 `dist/index.html` 取入口 JS/CSS，遍历 `dist/assets/*.js` 取最大块与总量，`gzip.compress(level=9)` 复算 KB。
  判据：`python utils/check_bundle_budget.py` 输出四行「指标 实测/预算」并以 0 退出。
- [x] 2.1 dist 缺失时自动补一次 `npx vite build`（复用 `vite-build` gate 的产物，不重复构建）。
  判据：删掉 `frontend/dist` 后单独运行脚本，能自建并给出结论。
- [x] 2.2 超限失败信息含指标、实测、预算、超出的 KB；入口引用缺失时报错而不是静默通过。
  判据：把某条 `budget` 临时改小后运行，退出码 1 且信息含该指标名；改回后 0。
- [x] 3.1 `utils/check_gates.py` 注册 blocking gate `bundle-budget`，排在 `vite-build` 之后。
  判据：`python utils/check_gates.py --only bundle-budget` 绿。
- [x] 3.2 CI frontend job 的 gate 串加 `bundle-budget`。
  判据：`.github/workflows/ci-phase1.yml` 里 frontend 的 `gates=` 含该名。
- [x] 4.1 `openspec validate add-bundle-size-budget --strict` 通过。
  判据：命令退出码 0。
- [x] 4.2 全量门禁不受影响：`python -m run check` 的 `pytest-collect` 仍绿（本单只加一条前端 gate）。
  判据：该 gate 通过。

## 5. 入口口径修正（2026-11-26）

- [x] 5.1 修正 `entry_js_kb` 口径：把 `rel="modulepreload"` / `rel="preload"` 指向的 JS 计入入口 JS，并在输出里给出「脚本 X + 首屏预载 Y」构成。
  原因：旧实现只读 `<script src>`，而 Vite 会把首屏要用的块写成预载——`element-plus` 手工分块那 296.7KB（gzip）一直在首屏被下载却没被计过。
  判据：同一份产物在旧口径下 `entry_js_kb` 为 12.9、新口径下为 386.3（A 分块）与 133.5（B 分块）。
- [x] 5.2 `frontend/vite.config.js` 去掉 `"element-plus": ["element-plus"]` 手工分块，让 Element Plus 按路由拆分。
  判据：首屏必载 JS 386.3 → 133.5（−65%）、JS 总量 706.1 → 573.9、最大块 296.7 → 194.4。
- [x] 5.3 按新口径重标定 `frontend/bundle-budgets.json`（baseline 133.5 / 55.4 / 194.4 / 573.9；budget ×1.1 = 147 / 61 / 214 / 632）。
  判据：`python utils/check_bundle_budget.py` 四项 ok；把 5.2 的分块改回去后该项立刻 FAIL（实测 386.3 > 147）。
- [x] 5.4 用 `tests/perf` 对两种分块做一次运行对照，确认没有把时间换成体积。
  判据：preview 3 轮中位数——A（旧）`/login` LCP 396ms / load 574.7ms / transfer 25 946KB / 15 请求；
  B（新）`/login` LCP 360ms / load 520.6ms / transfer 25 699KB / 18 请求。三项时间指标均不退化。
