## Why

`temps/login-layer-map/` 那份登录页设计层标注地图是**手工触发**生成的：它靠真实渲染 + 逐元素测量产出，但没有任何机制能发现「源码改了、图没重跑」。实际风险已经出现过一次——L5 覆盖层被修好后，同一份 HTML 里的 D 节仍写着「需修」，是我在修那个 bug 时顺手把它改成数据驱动才没留下误导。

同时该产物已经不止是「设计层地图」：D 节的实测结论是 L5 覆盖层约束（遮罩必须跳出 transform 包含块）在浏览器层的唯一证据，并与 `openspec/specs/frontend-l5-overlay` 的新增需求绑定。它需要被当作**需维护的产物**对待。

## What Changes

- 生成器内嵌**源码指纹**：把决定该 HTML 内容的源文件（登录模块 9 个 + 生成器自身 2 个）逐个算 sha256，随 HTML 一起写进 `<script type="application/json" id="layer-map-provenance">`，并在页头 meta 行展示摘要指纹与覆盖文件数
- 新增 `--check` 模式：不开浏览器，只重算指纹并与 HTML 内嵌指纹比对；不一致则**列出变更文件并以 exit 1 结束**，一致则 exit 0
- `README.md` 补「同步规则」与两条命令；`frontend/AGENTS.md` 登记该产物、触发重跑的文件清单与检查命令

**Non-goals**：
- 不把生成器接进 CI / pre-commit 钩子（钩子当前只管 Python ruff；接入方式需先定，登记为 Open Question）
- 不把 bundle 从 `temps/` 搬走（`AGENTS.md` 规定报告类文档放 `dev_docs/DEV_TEST/`，与本 bundle 现有位置冲突——需单独决策，见 Open Question）
- 不自动修正 `REGIONS` 里手写的 `src: ...:行号`（`--check` 只能发现文件内容漂移，管不了行号漂移）

## 关联文档

- `openspec/specs/frontend-l5-overlay/spec.md` —— D 节结论是该能力「Blocking overlays escape transformed ancestors」的浏览器层证据
- `frontend/AGENTS.md` —— 规则登记处（前端无登录模块级 AGENTS.md，故落在前端级）
- 前序变更：`2026-09-17-fix-l5-overlay-transform-trap`（把 D 节结论改为数据驱动）、`2026-09-17-remove-login-dead-code`（删除入口使 D 节图片/元素口径变化）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯工具与文档：`.openspec.yaml` 已设 `skip_specs: true`。不改变任何运行时行为——变更对象是 `temps/` 下的证据产物与 `frontend/AGENTS.md` 的登记条目。

## Impact

- 工具：`temps/login-layer-map/login-layer-map.cjs`（指纹 + `--check`）、`temps/login-layer-map/README.md`
- 文档：`frontend/AGENTS.md`（新增一节）
- 产物：`temps/login-layer-map/login-layer-map.html`（重新生成，内嵌指纹）
- 生产代码 / 后端 / API / 依赖：无
- 验证范围：生成一次 → `--check` exit 0；改一个受管源文件 → `--check` exit 1 且点名该文件；还原 → exit 0
