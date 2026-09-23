## 1. 删除第一代纯规则分区与其端点

- [x] 1.1 删除 `algorithms/layout.py`；验证：文件不存在，`grep -rn "algorithms.layout\|algorithms/layout" apps/ tests/ tools/ engines/ models/` 命中 0
- [x] 1.2 `apps/device_inspector/service.py`：删 `analyze_snapshot_payload` 与 `from algorithms.layout import classify_structure`，模块 docstring 的「capture 编排 + 结构分析」与「XPath / OCR / 布局算法」表述同步。验证：`grep -n "classify_structure\|analyze_snapshot_payload\|layout" apps/device_inspector/service.py` 命中 0
- [x] 1.3 `apps/device_inspector/api.py`：删 `analyze_snapshot` 与 `__all__` 中的条目；验证：`grep -n "analyze" apps/device_inspector/api.py` 命中 0
- [x] 1.4 `apps/device_inspector/views.py` 删 `snapshot_analyze`、`urls.py` 删其 import 与 `path(...)`；验证：`django.urls.resolve('/api/inspector/snapshots/1/analyze/')` 抛 `Resolver404`，而 `/api/inspector/snapshots/1/layers/` 解析为 `snapshot_layers`（实测输出见 §6）
- [x] 1.5 `tests/api/case/inspector.yaml` 删 TC-INS-004 与 TC-INS-040 两条用例；验证：`grep -n "analyze" tests/api/case/inspector.yaml` 命中 0，用例数 16 → 14，且 `python -m pytest tests/graybox/unit/test_api_path_callers.py -q` 全绿（yaml 面实测仍高于下限 42）

## 2. 删除孤儿语义层

- [x] 2.1 删除 `apps/ai_assistant/llm_semantic.py`；验证：文件不存在，`grep -rn "llm_semantic\|validate_semantic" apps/ tests/ tools/` 命中 0

## 3. 能力退役 delta

- [x] 3.1 `specs/page-analysis-semantic/spec.md` 写 5 条 `## REMOVED Requirements`（每条含 **Reason** 与 **Migration**），并在 `.openspec.yaml` 置 `retire_capabilities: true`；验证：`npx openspec validate retire-legacy-page-partition --strict` 通过

## 4. 文档同步

- [x] 4.1 `dev_docs/DEV_TEST/接口文档/API-设备检查器.md`：端点全集 9 → 8、删总览表的 analyze 行、删第 6 节、第 7~12 节重编号为 6~11、修正「第 12 节」交叉引用为「第 11 节」、删对已删第 6 节的说明；验证：`grep -n "analyze" ` 命中 0，章节号连续（§1~§11）
- [x] 4.2 `dev_docs/ARCH_PRD/PRD-03-设备检查器.md`：删 §结构分析 的 analyze 端点契约与 `layout.py` / `classify_structure` / `analyze_snapshot_payload` 指针、改「出口」为分层端点、删 2 条 TC 行、可重试来源 5 类 → 4 类、用例条数 16 → 14；验证：`grep -n "analyze\|classify_structure\|algorithms/layout" ` 只剩退役说明与既有 FE 漂移行（见 §6）
- [x] 4.3 `dev_docs/ARCH_PRD/ARCH-平台总体架构.md` 的 `algorithms/` 图节点去掉 `layout`；验证：`grep -n "xpath · hierarchy" ` 命中且不含 layout
- [x] 4.4【实施中补充】`tests/AGENTS.md` 的模块映射行去掉已退役的「结构分析」（该行的覆盖功能列举本变更使其失真）；验证：该行只剩 capture / 列表 / 详情 / 删除 / 保存到元素定位 / 页面回看六个覆盖项

## 5. 门禁

- [x] 5.1 后端：`python manage.py check`、`python manage.py makemigrations --check --dry-run`、`python -m ruff check`、`python -m ruff format --check`（本变更改动面）；验证：全绿
- [x] 5.2 测试：`python -m pytest tests/graybox -q`。验证：`392 passed`（含 yaml 面规模下限、路由连通性、api 路径对拍三项守护）
- [x] 5.3 边界与文档核对：`python tools/gen_arch_stats.py --check-boundaries`（退出码 0）、`python tools/gen_arch_stats.py --check-md --doc dev_docs/ARCH_PRD/ARCH-平台总体架构.md`（退出码 0）。验证：`✅ 模块边界检查通过 — 零违规`

## 6. 验收留痕（apply 期实测，供归档核查）

- **1.4 路由实测**：`resolve('/api/inspector/snapshots/1/layers/').url_name == 'snapshot_layers'`；`resolve('/api/inspector/snapshots/1/analyze/')` → `Resolver404`。端点由 9 降为 8（接口文档与 `urls.py` 同步）。
- **1.5 用例数**：`tests/api/case/inspector.yaml` 由 16 条降为 14 条（其中 `auth: "none"` 7 → 6）。`test_api_path_callers.py` 的 yaml 面实测同步下降 2 条，仍高于登记下限 42，**无需重登记下限**。
- **全仓复验已删标识符**：`classify_structure` / `analyze_snapshot` / `snapshot_analyze` / `llm_semantic` / `validate_semantic` / `algorithms.layout` 在 `algorithms/ apps/ tests/ tools/ engines/ models/ config/ shared/` 的 `.py` 中命中 **0**（`openspec/` 历史归档与本次变更工件除外）。
- **5.1 门禁的既有噪声（非本变更引入，已核实）**：`python -m ruff check algorithms apps tests` 报 1 条 `I001`，落在 `tests/graybox/unit/test_report_ai_task_list.py`（`git status` 为 `??` 未跟踪，并发会话新增）；`python -m ruff format --check apps/ai_assistant/api.py` 报需重排，该文件 `git status` 为 `MM`（并发会话已改）。两者均**不在本变更改动面**；本变更改动面 `algorithms/` + `apps/device_inspector/` 的 ruff check 与 format check **全绿**（13 files already formatted）。按「只碰必须碰的」未顺手修。
- **5.3 `--check-md` 的用法**：当前 CLI 需 `--doc <架构文档路径>`（无参调用报用法并以 exit 2 退出）；按正确用法运行得 exit 0，输出「💡 ARCH-平台总体架构.md 中无 ARCH_STATS 区域，需要初始化」—— 该文档未初始化自动区域是既有事实，与本变更无关。
- **PRD-03 的残留（既有漂移，未纳入本变更）**：`grep "analyze"` 仍命中第 241 行 `store.ts`（`applyFilters` · `analyzeSnapshot` · …）—— 该行的 `analyzeSnapshot` 与 `applyFilters` 是既有变更 `rework-inspector-layers-view` 移除的 FE 函数，先于本变更失效；同一文档的「后端 7 端点」「分区筹码 / 筛选 / 固定 7 行」等亦属既有漂移。只做局部替换会让该节半新半旧，故登记为遗留缺口。
- **旁证**：仓库根目录另有未跟踪的临时诊断文件 `dubug_001.py`，其中引用 `algorithms/xpath.py:8-140`（不引用 `layout`）；属既有未跟踪文件，未纳入本次改动。
