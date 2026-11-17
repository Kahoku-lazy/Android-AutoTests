## 1. 品牌字体内联

- [x] 1.1 `render.py` 新增 `_brand_font_src(fallback)`：读 `frontend/public/fonts/ziku-feiyang.ttf` → `data:font/ttf;base64,...`，读不到文件时回落相对路径。`render()` 改为用它填 `@font-face` 的 `src`。验证：渲染产物含 `src: url("data:font/ttf;base64,`，且不再含 `frontend/public/fonts`。
- [x] 1.2 模块 docstring 补第 5 条（排版三档 + 字体内联 + 侧栏三成）。验证：`engines-docstring-check` 0 error。

## 2. 字号三档

- [x] 2.1 正文由 `--app-size-xs` 提到 `--app-size-sm`：`.task .v`、`.check-card li`、`.task-box p`、`.side-list`、`.token-card .row`、`.tip`、`.code`、`.cpanel pre`、`details.kv pre`、`.log-row`。验证：`test_type_scale_is_three_tiers` 断言正文全部 14。
- [x] 2.2 时间 / 日期保持 12：`.log-t` 显式声明 `--app-size-xs`（此前靠 `.log-row` 继承，行内升 14 后会跟着变大）。验证：同一测试断言 `.log-t` / `.t` / `.phase-h em` 仍是 12。
- [x] 2.3 标题 / 小标题升到 16：`.tool`（工具卡标题）、`.chart-card h4`、`table.marks th`；`.phase-h h3` 原本已是 16。验证：同一测试断言四个选择器取 `--app-size-md`。
- [x] 2.4 两处页面标题栏维持平台档位不动（`.brand-title` 20 / `.wb-title` 24）。验证：同一测试断言两者的字号令牌仍是 `lg` / `xl`。

## 3. 侧栏默认三成 + 可拖

- [x] 3.1 `:root` 的 `--side-w` 由 `260px` 改 `30%`，新增 `--side-min:220px` / `--side-max:760px`；`.sidebar` 用 `min-width` / `max-width` 兜底，去掉 `border-right`。验证：`test_sidebar_defaults_to_thirty_percent_and_is_draggable` 断言 `--side-w:30%` 与新上下限。
- [x] 3.2 新增 `.splitter`（8px 命中区 + 居中 2px 线，常态 `--color-orange-76`、hover/拖拽 `--ink`、`:focus-visible` 描边、`prefers-reduced-motion` 降级）。验证：同一测试断言 `cursor: col-resize` 与 `.splitter { display: none; }`（窄屏）。
- [x] 3.3 `render()` 在侧栏与主区之间插入手柄节点（`role="separator"`、`aria-orientation="vertical"`、`aria-valuemin/max`、`tabindex="0"`）。验证：同一测试断言 `id="splitter"` 与三个 aria 属性。
- [x] 3.4 `_SCRIPT` 新增 `initSplitter()` 并初始化：拖拽改宽、`col-resize` + 正文不可选、←/→ 16（Shift 48）、Home/End、双击回三成、`localStorage` 记住宽度、≤900px 不参与。验证：同一测试断言步长常量与 `DEFAULT_RATIO = .3`；`node --check` 通过。

## 4. 测试与文档

- [x] 4.1 `tests/engines/ae_harness/unit/test_report_render.py` 新增三条契约测试，模块 docstring 补第 3 条。验证：11 条用例全过。
- [x] 4.2 `.agents/skills/doodle-craft/references/standalone-html.md` 登记：单文件报告的品牌字体必须内联、字号三档、分栏手柄默认三成与上下限。验证：该文件出现「品牌字体」与「30%」两处新规。

## 5. 门禁

- [x] 5.1 `python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_report_render.py -q`，退出码 0。验证：全过。
- [x] 5.2 `engines-docstring-check`（`python -m scripts.docstrings check`）0 error；`engines-agents-style-check` 对 `render.py` 无新增告警（存量 `engines/device/*` 的 7 条 `raises-doc` 与本变更无关）。验证：两条命令输出如上。
- [x] 5.3 `openspec validate --change report-typography-and-split-pane`，退出码 0。
