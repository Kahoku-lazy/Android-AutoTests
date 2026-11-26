## 1. 代码

- [x] 1.1 `_grid_points` 支持 `step_y`（0 沿用 `step`）与 `size ∈ {3,5,7}`，非法值仍抛 `ValueError`；用 `python -m` 跑 `temps/` 冒烟脚本核对 3×3 / 5×5 / 7×7 的点数、两轴间距与贴边夹取（实测 9 / 25 / 49 点，y 间距按 `step_y` 生效，越界被夹到 0 与 1）
- [x] 1.2 `_annotate` 增加 `ring` 分支：空心圆环（半径按间距收敛、白色外描边）+ 列号在首行上方、行号在首列左侧；`cross` 分支逐行不变（含 25 点上限）
- [x] 1.3 `_render` / `_screenshot_with_points` 透传 `style` 与 `grid_size`；`marks` 每项补 `row` / `col`；`grid` 回显 `marker` 与生效 `step_y`；环点上限 49
- [x] 1.4 `adb_screenshot_grid` 增加 `marker`（默认 `cross`）与 `step_y`（默认 0）参数与取值校验，失败走 `_fail` 返回可读错误；工具 docstring 首行摘要与 `Args:` 同步写明两种形态的用法

## 2. 真机验证（脚本留在 `temps/`，不提交）

- [x] 2.1 以 `marker="ring"`、`size=3`、默认步长对真机出图，确认环心可见、行列号各出现一次（`temps/grid_out/tool_ring3_default.png`）
- [x] 2.2 以 `marker="ring"`、`size=5`、`step=0.02`、`step_y=0.01` 对准 49×48 px 的右侧箭头徽标，确认 9 个环压在徽标上（行 2~4 × 列 2~4），并用第 3 行第 3 列坐标 `(0.904, 0.504)` 回填单点核对，红点正中箭头（`temps/grid_out/final_ring5.png` / `final_confirm.png`）
- [x] 2.3 以默认参数（不传新参数）出图，确认十字渲染与返回字段与改动前一致（时钟差异外无变化；`grid.step_y` / `grid.marker` 为新增回显字段，`index/nx/ny` 不变）

## 3. 门禁

- [x] 3.1 `python -m scripts.docstrings check`（`.agents/skills/engines-docstring-check`）无新增问题：0 error / 0 warn
- [x] 3.2 `python -m scripts.check_engines_agents_style`（`.agents/skills/engines-agents-style-check`）通过：96 文件 0 违规
- [x] 3.3 `python -m run check` 本地门禁通过（阻塞项为零）—— 27/29 通过，`vitest` 与 `vite-build` 因环境 `EPERM`（`frontend/node_modules/.vite-temp` 写权限）失败，与本变更无关；与 Python 相关的 15 个阻塞项全绿（含 `ruff-engines-format` / `ruff-engines-lint` / `engines-agents-style` / `pytest-collect`）

## 4. 文档与收尾

- [x] 4.1 `.agents/docs/engines/ae_harness_tools/ae_harness_tools_domain_tools.md` 的「网格核对」与「视觉定位精度」两处口径同步为环点阵与双轴步长
- [x] 4.2 `openspec validate harness-adb-grid-ring-marker --strict` 通过，任务清单勾完
