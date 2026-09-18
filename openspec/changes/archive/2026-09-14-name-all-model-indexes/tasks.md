## 1. 取证

- [x] 1.1 AST 扫 `apps/**/models.py` 的 `models.Index(...)`，筛无 `name` kwarg 的；验证：`temps/d0_index_scan.py` 输出 `UNNAMED_INDEXES 5`，分布 3 文件
- [x] 1.2 从 Django 注册表取计算名；验证：`case_manager.TestDefinition[project,directory,sort_order]` → `cm_test_def_project_032175_idx`；`device_inspector.Snapshot[created_at]` → `di_snapshot_created_7e4a98_idx`；`Snapshot[device_id]` → `di_snapshot_device__9cbb1d_idx`；`device_pool.Device[status]` → `dp_devices_status_47e1d0_idx`；`DeviceLock[device,status]` → `dp_device_l_device__4b3c95_idx`

## 2. 修改

- [x] 2.1 `apps/case_manager/models.py`：`TestDefinition` 的 directory 索引补名
- [x] 2.2 `apps/device_inspector/models.py`：`Snapshot` 两个索引补名
- [x] 2.3 `apps/device_pool/models.py`：`Device.status` 与 `DeviceLock` 补名

## 3. 验证

- [x] 3.1 **判据达成**：`python manage.py makemigrations --check --dry-run` → `No changes detected`，**exit 0**（证明补名零 DDL）
- [x] 3.2 `python manage.py check` → no issues，exit 0；`python -m ruff check` 三文件 → All checks passed；`ruff format --check` → 3 files already formatted
- [x] 3.3 `pytest tests/graybox/unit -q` → **75 passed**（无新增失败）
- [x] 3.4 取证脚本已删（`temps/d0_index_scan.py` 不存在）；`git diff --numstat` 仅三个 models.py（`12/3` · `8/2` · `8/2`，其中 case_manager 含上一单的索引名改动）

## 4. 结果说明

- [x] 4.1 全仓 `models.Index` 现已 **0 处未显式命名**（取证脚本口径：AST 扫描 `apps/**/models.py`）→ 同类哈希漂移风险已闭合
