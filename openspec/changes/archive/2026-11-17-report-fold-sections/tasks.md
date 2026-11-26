## 1. 报告区三层折叠

- [x] 1.1 `engines/ae_harness/event/render.py`：`_report()` 把子目标分组改成「标题行 + 可折叠正文」两段（正文包 `.phase-b`，标题行 `role="button" tabindex="0" aria-expanded="false"` 并显示分组名与调用次数），默认收起。验证：同构夹具（5 个真实子目标 / 100 次调用）渲染后首屏只有 5 条标题行 + 汇总句，见 `temps/fold-check/shot-fold-check.png`。
- [x] 1.2 同文件：角色块改成「角色标题行（`执行者` / `验收者` 胶囊）+ 可折叠正文」，把原来直接拼在 `.role-block` 下的卡片挪进正文容器，默认收起。验证：展开子目标后只看到 `执行者` 胶囊，卡片仍不显示，见 `temps/fold-check/shot-fold-check-open.png`。
- [x] 1.3 同文件：`_step()` 把卡片正文（意图 / 入参 / 结果 / 截图）挪进 `.card-b`，`.card-h` 补 `role="button" tabindex="0" aria-expanded="false"` 与折叠挂点；标题行保持「序号 + 工具名 + 耗时」。验证：收起态卡片只占一行 `▸ 1 adb_screenshot … 305.5 ms`，与需求方给的截图标题一致。
- [x] 1.4 同文件 `_CSS`：补收起 / 展开的显隐规则（`.fold-b { display: none }` / `.is-open > .fold-b { display: block }`），折叠用 `is-open` 前缀类，与抽屉的 `.open` 区分；`:focus-visible` 沿用既有规则。验证：状态类只在 `.fold-h` / `.is-open > .fold-b` / `.call.is-open > .trace-body` 三处出现，没有第二套 `display:none` 硬编码。

## 2. 折叠交互脚本

- [x] 2.1 同文件 `_SCRIPT`：新增统一折叠函数 `toggleFold()`（按 `.fold-box` 找折叠盒，切 `is-open` + 同步 `aria-expanded` + 换箭头）；标题行改成真 `<button type="button">`，Enter / Space 由浏览器原生转 click，因此不再写 `foldKey()`；删除只切 `hidden` 的旧 `toggleTrace()`。验证：三份截图里 `▸` / `▾` 与展开态一一对应；`test_toggle_script_is_shared_and_syncs_aria` 断言没有 `foldKey` / `toggleTrace` 残留。
- [x] 2.2 同文件：报告页 `tip` 改为「按子目标分组；点标题逐层展开（子目标 → 角色 → 工具卡），截图可点击放大。」，轨迹页补「点行展开该次调用的详情」。验证：`test_tips_match_behavior` 断言两条文案存在。

## 3. 轨迹页调用行展开

- [x] 3.1 同文件 `_CSS`：删掉没人用的 `.call-b` / `.call.open` 死规则，`.trace-body` 改为默认 `display: none`、由 `.call.is-open > .trace-body` 展开；`_trace()` 改用与报告区同一个 `toggleFold()`。验证：轨迹页点工具行展开概述 / 参数 / 结果 / Schema 四个页签，见 `temps/fold-check/shot-fold-check-trace.png`。
- [x] 3.2 同文件 `_trace()`：标题行 `aria-expanded` 初值 `false`，展开后由同一个函数改 `true`；模型调用行没有详情容器，切状态不报错也不留空白。验证：截图中 `deepseek-flash` 行收起无塌陷、`adb_screenshot` 行展开正常；`test_trace_body_collapsed_by_default` 断言默认收起与死规则已删。

## 4. 测试与门禁

- [x] 4.1 新增 `tests/engines/ae_harness/unit/test_report_render.py`：用最小 `RunRecord` 渲染一次，断言三层折叠挂点、默认 `aria-expanded="false"`、正文容器初始收起、折叠脚本函数存在、轨迹详情区不再被写死 `display:none`。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_report_render.py -q` → **6 passed**。
- [x] 4.2 注释自检：`cd .agents/skills/engines-docstring-check && python -m scripts.docstrings check` → **0 error / 0 warn**。风格自检：`cd .agents/skills/engines-agents-style-check && python -m scripts.check_engines_agents_style` → 7 条 `raises-doc`，全部在 `engines/device/**`（既有欠账，本次未触碰）。
- [x] 4.3 本地门禁：`python run.py check`。**未通过，但不是本次改动引起**：12 项阻塞失败全部落在本次没碰过的面 —— `pytest-collect`（dashboard / task / report / backend_bridge 共 22 个收集错误）、`engines-agents-retirement`（`tests/engines/backend_bridge/unit/test_model_billing_parity.py` 仍 import 已退役的 `engines.agents.messaging.billing`）、`ruff-engines-format`（`engines/ae_harness/agents/creator.py`、`engines/backend_bridge/models/discover.py`）、`ruff-format` / `ruff-lint`（`PY_SCOPES` 只含 `backend/`，本次未动）、openapi 两项与前端五项（`frontend/` 未动）。本次两个文件单独过检：`ruff format --check` → 2 files already formatted，`ruff check` → All checks passed。**待决定**：是否在本变更内顺手修这些既有失败（超出本变更范围）。
- [x] 4.4 规模复验：用 `temps/render_fold_check.py` 造 5 个真实子目标 / 100 次调用 / 58 张截图量级的同构记录，渲染三份视图（收起 / 全展开 / 轨迹）并用 headless Chrome 截图人工确认。**与原计划不同**：没有重放 `20261117_155020_sop_bound.jsonl`，因为图片 base64 按 `event/AGENTS.md` 红线从不写入 JSONL，`AgentEventRecorder.finish()` 也是内存态的，逐字节重放需要另写一个解析器；改成同构夹具 + 真实子目标名与工具名，`logs/` 下既有报告未改动。

## 5. 子目标手绘序号

- [x] 5.1 同文件：新增 0-9 的单笔画路径表与 `_ordinal_svg()`，把序号画成两位数并 `min(value, 99)` 封顶；两位数字各带方向相反的 1.8°~2.6° 倾斜。验证：`temps/ord_zoom.py` 放大到 96 / 180px 核对笔画与倾斜；`test_ordinal_caps_at_99` 断言第 100 个仍显示 `99`。
- [x] 5.2 同文件 `_CSS`：`.ord` 定高 24px（比 16px 标题高半档，初版 30px 偏大已按反馈收紧）、`.ord path` 统一圆头圆角 + 湍流滤镜，淡墨层与主笔画分别取 `8.4 / 5.2` 线宽；配色按需求方选定方案改为**左位红、右位蓝**，各自由 45% 淡到 30%（两个 `userSpaceOnUse` 渐变 + 路径上的 `ord-red` / `ord-blue` 类），新增 `--color-red-40` / `--color-blue-47` 两个颜色原子。验证：`test_subgoal_ordinal_is_svg_drawn` 断言两套渐变、四个类名各一份；截图见 `temps/fold-check/shot-fold-check.png`。
- [x] 5.3 同文件 `_report()`：子目标标题前插入序号（与标题同在按钮内，点序号等同点标题），`_ORDINAL_DEFS` 在报告区顶部只发一次。验证：`test_subgoal_ordinal_is_svg_drawn` 断言 defs 只有一份、标签为「第 1 个子目标」、两位数共 4 条 path；截图见 `temps/fold-check/shot-fold-check.png`。
- [x] 5.4 注释自检：`cd .agents/skills/engines-docstring-check && python -m scripts.docstrings check` → 0 error / 0 warn；`ruff format --check` / `ruff check` 两个改动文件均通过。

