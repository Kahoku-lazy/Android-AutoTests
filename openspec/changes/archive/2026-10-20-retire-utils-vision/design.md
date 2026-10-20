## Context

见 proposal.md - Why。当前事实：

- `utils/vision/ocr.py` 与 `engines/vision/ocr.py` 仅差 3 行 docstring，实现相同；全仓 `.py` 对 `utils.vision` 零引用（仅归档文档提及）。
- `utils/vision` 的 blob 与 `e14cf891^` 的 `algorithms/vision` 完全相同（`a860234a`），`e14cf891` 以 `R100` 把它改名成 `utils/vision`。`e14cf891^` 没有 `utils` 目录，说明改名来自工作区未提交内容，被 `git add -A` 夹带。
- `engines/vision` 首次入库在 `ff836e34`（18:16:13），晚于 `e14cf891`（17:12:04），说明 move-ocr 的删除发生在 `utils/vision` 已被跟踪之后。
- `2026-10-20 18:13:34` 有 198 个工作区文件被批量重写（tests/openspec/dev_docs/utils 等，毫秒递增），写入内容与 HEAD 一致；`88e3796a`（18:13:45）为空提交，可佐证这次是把工作区恢复成版本库状态的操作（git reset/checkout 或等价还原），不是新代码。
- [tests/engines/agents/test_ocr_tool.py](tests/engines/agents/test_ocr_tool.py:74) 的源码扫描只覆盖 `engines.vision`，不检查 `utils/vision` 是否存在。

## Goals / Non-Goals

**Goals:**

- `utils/vision` 从工作区与版本库都消失，`engines/vision` 是唯一 OCR 实现。
- 守卫同时覆盖「磁盘是否还存在」与「版本库是否跟踪」两个层面，防止删除后再被 `git add -A` 或批量还原带回来。
- 归档文档留下这次事故的成因与复核要求，不修改历史结论。

**Non-Goals:**

- 不重构 `engines/vision` 的识别逻辑，不改 `tool_ocr` 的调用方式。
- 不改任何 API、表结构、前端交互。
- 不追溯重写历史提交（不 rebase / filter-branch）。

## Decisions

### D1 直接删除，不做转发模块

`utils/vision` 零引用，保留转发（`from engines.vision.ocr import recognize`）只会延续双路径，掩盖「唯一实现」的约束。删除后若有仓库外脚本 import 会立即报错，这比静默漂移更安全。

备选：保留转发并标注 deprecated。否决，因为没有任何已知调用方，转发没有收益。

### D2 守卫做成「Git 层 + 源码层」两条断言

在 [tests/engines/agents/test_ocr_tool.py](tests/engines/agents/test_ocr_tool.py:74) 增加：

- Git 层：`git ls-files --error-unmatch utils/vision` 必须非零退出；同时 `Path("utils/vision").exists()` 必须为假。这样「工作区删了但索引里还有」也会失败。
- 源码层：扫描 `*.py` 的导入语句，任何 `utils.vision` / `utils import vision` 命中即失败（归档文档不算源码）。

不选 `tools/check_gates.py` 单点：门禁不是每次开发都跑，测试是每次 `pytest` 都跑。两者可以都加，但本变更先落测试，门禁项作为后续可选。

### D3 归档订正用「事后订正」小节，不改原文

在 `2026-10-20-retire-inspector-and-element-locator/tasks.md` 与 `2026-10-20-move-ocr-into-engine/tasks.md` 末尾各加一节，写清：

- 当时「删除 `utils/vision`」只发生在工作区，未在 git 层复核；
- `algorithms → utils` 改名未申报，被 `git add -A` 夹带进 retire 提交；
- 事后由 `retire-utils-vision` 收口，并给出 git 复核命令。

不修改原有验收结论（历史记录保持原样），只追加事实。

### D4 把「删除类验收必须查 git」写成流程要求

验收命令从「路径不存在」升级为三条一起看：

1. `git ls-files <path>` 为空；
2. `git status --porcelain -- <path>` 为空；
3. 源码扫描 `rg "<path 的导入名>"` 无业务命中。

这条要求写进归档订正节，避免下一单再犯。

## 模块防火墙自检

- 不新增跨 App import；删除的是零引用包，反而减少一条潜在跨层入口。
- 不涉及跨 App 写库、不新增 service/runner/consumer/state_machine 依赖。
- 前端不涉及；无数据库写入；无 `api.py` 契约变化。
- 删除后 `engines/vision` 的导入关系不变：仅 `engines/agents/tools/tool_ocr.py` 在函数内导入。

## Risks / Trade-offs

- [仓库外脚本仍 import `utils.vision`] → 仓库内零引用；删后报 `ModuleNotFoundError` 是期望行为，逼调用方迁移。
- [CI 环境没有 git 命令] → 守卫先检查 `git` 可用，不可用时跳过 Git 层断言并仍执行源码层；本地开发始终有 git。
- [批量还原再次把包写回] → Git 层断言会在下次 `pytest` 直接失败，且 `git status` 会显示未跟踪/已修改。
- [误删 `utils/__init__.py`] → 任务里明确只删 `utils/vision/` 子目录，`utils/` 其余文件保留。

## Migration Plan

无数据库迁移。回滚即从 `e14cf891` 恢复 `utils/vision/` 两个文件；当前无运行时代码依赖，回滚不影响服务。

## Open Questions

无。
