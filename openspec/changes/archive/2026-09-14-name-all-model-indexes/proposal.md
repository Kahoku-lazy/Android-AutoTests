## Why

`stabilize-drifted-index-names` 修掉了 3 处**已发生**的索引名漂移（根因：模型里没写显式 `name=`，Django 按「表名_字段前缀_哈希」现算）。本轮 D0 复查用 AST + Django 注册表扫了一遍，**还剩 5 处未显式命名**（3 个文件）——它们当前恰好没漂移（`makemigrations --check` 绿），但同一哈希漂移风险仍在：任何 Django 版本升级或字段调整都可能让它们变成下一批「Rename index」。

实测清单（`temps/d0_index_scan.py` 取证脚本，AST 找调用点 + Django 取计算名）：

| 文件:行 | 模型 | 索引字段 | 当前计算名（= 迁移状态名，因 `--check` 绿） |
|---------|------|----------|------------------------------------------|
| `apps/case_manager/models.py:165` | `TestDefinition` | project / directory / sort_order | `cm_test_def_project_032175_idx` |
| `apps/device_inspector/models.py:44` | `Snapshot` | created_at | `di_snapshot_created_7e4a98_idx` |
| `apps/device_inspector/models.py:45` | `Snapshot` | device_id | `di_snapshot_device__9cbb1d_idx` |
| `apps/device_pool/models.py:49` | `Device` | status | `dp_devices_status_47e1d0_idx` |
| `apps/device_pool/models.py:80` | `DeviceLock` | device / status | `dp_device_l_device__4b3c95_idx` |

## What Changes

- 给这 5 处 `models.Index(...)` 补显式 `name=`，取值**逐一取自 Django 当前计算名**（在 `makemigrations --check` 为绿的前提下，它等于迁移状态名 → 零 DDL）
- **不改**：索引字段、`Meta.constraints`、迁移文件；不动已显式命名的索引（含上一单的 3 处）
- **BREAKING**：无（数据库 DDL 无变化）
- 按 schema 约定设 `skip_specs: true`

## 关联文档

- 前置：`stabilize-drifted-index-names`（同源根因，修的是已漂移的 3 处）
- 取证脚本：`temps/d0_index_scan.py`（本单跑完即删，不入库）
- 门禁依据：`.agents/skills/django-backend-check/references/calibration.md` §7（`makemigrations --check` 必跑）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 源码：`apps/case_manager/models.py`（1 处）· `apps/device_inspector/models.py`（2 处）· `apps/device_pool/models.py`（2 处）
- 数据库：**无 DDL 变化**
- 验证：`makemigrations --check` 仍 exit 0（关键判据）· `manage.py check` · `ruff check` / `format --check` 三个文件 · `pytest tests/graybox/unit -q`（75 passed 基线）
