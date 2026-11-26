# 已取消：retire-tests-to-temps

> 状态：**cancelled + archived**（2026-11-26，需求方决定）
> 原因：**未启动即取消**（tasks 0/25，卡在 0.1 变更申请获批）。2026-11-26 需求方指示「任务取消，这个变更直接归档」，
> 因此未做任何代码与文档改动，直接以 `--skip-specs` 归档，主规格 `api-path-convention` 保持原样。
> 位置：`openspec/changes/archive/2026-11-26-retire-tests-to-temps/`（不在 `openspec/changes/` 下，CLI 不再列为活跃变更）

## 取消后的实际状态

- `tests/` 17 个用例目录、`frontend/tests/` 11 个模块目录**都还在原位**，收集量仍是 541。
- 根 `AGENTS.md` 与 `tests/AGENTS.md` 的红线措辞**未被修改**（这条本来要等 0.1 获批）。
- `openspec/changes/retire-tests-to-temps/specs/api-path-convention/spec.md` 的 delta **未应用到主规格**（`--skip-specs`）。

## 恢复方法

把本目录整体移回 `openspec/changes/retire-tests-to-temps/`，即重新出现在 `openspec list`；
恢复前先重核 proposal 里的事实是否仍成立（代码在动，`tests/` 的规模与文档路径可能已变）。
