## 1. 维护命令

- [x] 1.1 新建 `apps/element_locator/management/{__init__.py,commands/__init__.py}` 与 `commands/maintain_locator_media.py`（`--apply` / `--only backfill|prune`）；验证：`python manage.py maintain_locator_media --help` 输出 `[--apply] [--only {backfill,prune}]`
- [x] 1.2 backfill：路径不在 `locator/pages/` 下的页面截图与元素缩略图 → 复用 `_copy_into_locator` 复制并 `update_fields` 改指；源缺失跳过并计数；验证：集成测试「复制 + 改指 + 源保留」「源缺失跳过」；真机抽样 `Page#42..47` 已指向 `locator/pages/<id>/screen.png` 且文件在、元素样例 `locator/pages/42/el_com.govee.home_id_ivBack_9d93d629.png` 在盘
- [x] 1.3 prune：构建引用集 → 删除 `locator/pages/**` 下未被引用的文件与空目录（仅 `--apply`）；验证：集成测试「只删孤儿、保留被引用、`inspector/**` 不动」；真机当前孤儿数为 0（无需删除）
- [x] 1.4 默认 dry-run：不写文件、不改 DB；验证：集成测试「dry-run 前后文件与记录均未变」——**该用例实测抓到并修掉了一个真 bug**：首版 dry-run 仍会调用 `_copy_into_locator` 真的复制文件，已改为 dry-run 分支只算路径不落盘

## 2. 测试

- [x] 2.1 新增 `tests/graybox/integration/test_locator_media_maintenance.py`（4 例）；验证：**4 passed**；`ruff check --fix` 修掉 I001 后 `All checks passed`

## 3. 真机与门禁

- [x] 3.1 dev 库 dry-run 读数：`扫描 136 · 回填 118 · 源缺失跳过 18 · 孤儿 0`（页面 #39/#41 因源缺失跳过；#42/#43/#44/#46 待回填）
- [x] 3.2 dev 库 `--apply` 后：5 个页面（#42/#43/#44/#46/#47）的 `screenshot_path` 均指向 `locator/pages/<id>/screen.png` 且文件在盘；`curl` 复核 `locator/pages/43/screen.png` = **200**；#39/#41 保留原路径（源已不存在）；检查器源文件未被触碰（`inspector/shots/capture_20260921_170004_715750.png` 仍在）；再跑 dry-run 为 `回填 0`（**幂等**）
- [x] 3.3 `manage.py check`（0 issues）+ `ruff check apps/element_locator apps/device_inspector tests/graybox/integration`（All checks passed）+ `ruff format --check`（12 files already formatted）+ `pytest tests/graybox -q` 全量；验证：见读数
- [x] 3.4 归档；验证：`openspec validate --strict` valid（`skip_specs` 生效）
