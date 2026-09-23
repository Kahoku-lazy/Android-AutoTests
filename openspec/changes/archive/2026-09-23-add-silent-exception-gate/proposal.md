## Why

`AGENTS.md` 原则「错误不应默默忽略，除非明确地选择忽略」此前**无法验证**：它是人工约定，没有任何检查能判收。仓库里实际存在「捕获后什么都不做」的异常处理器——`pass` / `continue` 之后既不抛出、也不记录、也不说明为什么忽略，出问题时完全无法从日志或代码追查。

本变更把这条原则落成**可机械验证**的检查，并按检查结果清掉存量。

## What Changes

- `tools/check_gates.py` 新增门禁 `silent-except`（AST 检查，非 CI 内联项）：一个 `except` 处理器若**同时**满足下列全部条件即判违规——
  1. 处理器体只有 `pass` / `continue` / `break`；
  2. 作用域内没有任何 `raise`；
  3. 没有任何日志调用（`logging/logger/log` 的 debug/info/warning/error/exception/critical）；
  4. 处理器覆盖的源码行内没有任何 `#` 注释。
- 检查范围：`apps/ config/ gateway/ shared/ engines/` 下的 `.py`；**排除** `engines/ai/skills/skill-creator/**`（供应商产物，与 `ruff.toml` 的 exclude 一致）与 `**/migrations/**`（历史迁移不可改）。
- 存量清理：为 8 处项目自有违规各补一行「明确忽略」注释，说明为什么可以忽略（纯注释，不改任何逻辑）。
- 门禁级别：**告警**（`blocking=False`）。转拦截由后续独立变更执行（需与其余告警项一并处理）。
- **BREAKING**：无。

## 关联文档

无对应需求编号（未关联 PRD / ARCH）。本变更为开发工具链与错误处理规范落地，需求来源为「不许静默吞异常要不要做成真检查」的决策，已在 proposal 内完整描述。

## Capabilities

### New Capabilities

无。检查与注释清理不改变系统行为，按 schema 约定置 `skip_specs: true`。

### Modified Capabilities

无。

## Impact

- 新增/修改：`tools/check_gates.py`（新增一个门禁）· 8 个 Python 文件各加一行注释。
- 不涉及 API 契约、数据模型、前端或依赖；8 处改动均为注释，运行期行为零变化。
- 存量基线（本次实施测得）：全仓「处理器体为空」的处理器共 **18 处**，其中 10 处在供应商产物、1 处在历史迁移（均按上述范围排除），**项目自有 8 处已全部补齐说明**。
- **明确不覆盖的类别**：`except X: return <默认值>` 这类「直接返回默认空值」共 **31 处**，本次**不判违规**。理由见 design.md 决策 2。
