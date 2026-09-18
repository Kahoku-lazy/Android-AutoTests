## Context

动机与实测输出见 `proposal.md` - Why。这是**模型声明与迁移状态不一致**，与 D0 治理线同源（声明 ≠ 实际），但落在模型层。

## Goals / Non-Goals

**Goals:**

- `makemigrations --check` 恢复绿（关单门禁红线）
- 索引名在「模型声明」与「迁移状态」两侧一致，不再随 Django 版本/哈希变化漂移

**Non-Goals:**

- 不生成 3 个 `Rename index` 迁移
- 不批量给全仓索引补显式名（避免大范围 diff；autodetector 对其它索引当前无异议）
- 不改索引字段或查询性能相关设计

## Decisions

### 1. 补显式 `name=`，而不是生成 rename 迁移

- **选择**：在模型 `Meta.indexes` 上写死迁移里已有的名字
- **理由**：Django 官方建议显式命名索引；生成的 rename 迁移只改名字、不带来任何能力，且在 MySQL 上仍是一次真实 DDL（`ALTER TABLE … RENAME INDEX`），纯风险无收益。补名后 autodetector 立即收敛
- **备选**：生成迁移 —— 会把「Django 哈希变了」固化进迁移历史，并为未来每次哈希变化埋下同样的坑，否决

### 2. 名字取自迁移状态，而不是 Django 现算名

- **选择**：`cm_case_fil_project_9a1b2c_idx` · `cm_test_def_project_file_idx` · `wf_document_prototy_idx`
- **理由**：线上库里的索引名就是迁移记录的那个；写现算名才会产生真正的 rename DDL

### 3. 只改漂移的 3 处

- **选择**：只给 autodetector 报出的这 3 个索引补名
- **理由**：最小 diff、判据明确（`makemigrations --check` 归零）；把全仓其它未命名索引一并显式化属独立的命名规范变更，不在本单

## 模块防火墙自检

- 跨模块写库：不涉及（只改模型 Meta 声明，无新写路径）
- 引擎边界 / 通信通道：不涉及

## Risks / Trade-offs

- [写错名字反而产生真实 rename DDL] → 名字逐字取自迁移对应行（`0021:83` / `0021:110` / `0003:108`），并以 `makemigrations --check` 归零作为判据
- [其它 App 仍有未命名索引将来再漂移] → 已登记为范围外；本次判据只覆盖已发生的漂移

## Migration Plan

1. 复核漂移现状（`makemigrations --check` exit 1 + 3 条语句）
2. 给 3 个索引补显式 `name=`
3. `makemigrations --check` 必须 exit 0；`manage.py check` / `ruff` / 相关单测回归
4. 归档；回滚 = `git checkout` 两个 models.py
