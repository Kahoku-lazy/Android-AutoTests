## 1. 枚举与状态机现状测试

- [x] 1.1 新增 `tests/test_runner/test_state_machine_baseline.py`：覆盖合法流转表（idle→queued→running→done；fail 的 error/stopped/interrupted 三 outcome）与非法流转拒绝；验证 `python manage.py check && ruff check tests/test_runner/ && pytest tests/test_runner/test_state_machine_baseline.py`
- [x] 1.2 同文件覆盖 `repair_queued_terminal_drift`：构造 status=queued+终态 outcome 数据，断言批量 queued→done（标注"现状行为"）；验证同上
- [x] 1.3 同文件覆盖 TaskCard 序列化现状（`views/task_views.py` 的 running/outcome 字段映射）；验证 `pytest tests/test_runner/test_state_machine_baseline.py`
- [x] 1.4 锚定 TestRunStatus 双定义使用点：`state_machine.py:206` 写 "COMPLETED" 与 `runner.py:265` `TestRunStatus.COMPLETED` 各一条断言（标注"现状行为，L1b 后更新"）；验证 `pytest tests/test_runner/test_state_machine_baseline.py`

## 2. 算法现状测试

- [x] 2.1 新增 `tests/device_inspector/test_xpath_baseline.py`：`gen_xpath_candidates` 策略分支（resource-id/text/content-desc/class 组合、`_has_identity`、`_specificity` 排序、去歧）与 `trim_hierarchy` 裁剪；验证 `ruff check tests/device_inspector/test_xpath_baseline.py && pytest tests/device_inspector/test_xpath_baseline.py`
- [x] 2.2 新增 `tests/device_inspector/test_hierarchy_baseline.py`：`dump_hierarchy` 三层 fallback、XML 截断 rfind 修复、bounds 解析（mock `u2d.dump_hierarchy`）；验证 `pytest tests/device_inspector/test_hierarchy_baseline.py`
- [x] 2.3 新增 `tests/device_inspector/test_ocr_baseline.py`：`_pil_to_b64`、`recognize` 结果裁剪与 thumbnail 剥离（mock `_get_engine`）；验证 `pytest tests/device_inspector/test_ocr_baseline.py`

## 3. 引擎与连接现状测试

- [x] 3.1 新增 `tests/device_pool/test_pool_baseline.py`：`switch_to`/`_addr`（USB/WIFI/mDNS 解析）、`remove_device` 清理、`info` 2s 缓存（mock `ad`）；验证 `pytest tests/device_pool/test_pool_baseline.py`
- [x] 3.2 新增 `tests/test_runner/test_connect_baseline.py`：`_adb_connect` 成功关键词判定（connected/already/已连接/已经连接/成功）、`DEVICE_CHECK_TIMEOUT=45` 与 `U2_OP_TIMEOUT=20` 常量锚定（mock subprocess）；验证 `pytest tests/test_runner/test_connect_baseline.py`
- [x] 3.3 新增 `tests/test_runner/test_recovery_baseline.py`：`is_u2_crash`/`is_device_crash` 分类判定；验证 `pytest tests/test_runner/test_recovery_baseline.py`
- [x] 3.4 新增 `tests/device_pool/test_screenshot_baseline.py`：`screenshot_b64` 输出 JPEG base64 + `max_width` 缩放（mock `snapshot` 返回 numpy）；验证 `pytest tests/device_pool/test_screenshot_baseline.py`

## 4. 基线留档

- [x] 4.1 全量跑 `python manage.py check && python -m ruff check && python -m pytest -m "unit or integration" --nomigrations`，记录通过/失败清单（结果：check 0 issues；ruff 全过；pytest 247 passed / 201 deselected，其中 85 个为本变更新增基线测试；`--nomigrations` 原因：仓库迁移链含 MySQL 专属 RunSQL，SQLite 无法建库，项目惯例）
- [x] 4.2 勾选 `迁移实施注意事项-Checklist.md` §一"补测试先行/基线全绿留档"，基线结果附到本变更完成说明
