# 验收记录：add-serial-log-custom-ports

日期：2026-11-18 · 实现分支：Kahoku

## 一、自动化证据（已通过）

| 项 | 命令 / 方式 | 结果 |
|---|---|---|
| 后端 serial_log 套件 | `python -m pytest -c tests/pytest.ini tests/serial_log -q` | 46 passed（api 契约 201/200/400/403、双轨同步、增量生效、上限、失败 note、删除保留文件、重启恢复） |
| 前端 serial-log 套件 | `npx vitest run tests/serial-log` | 57 passed（表单纯校验、CRUD 编排、失败 error 提示、重试、no_log 不判失败） |
| 迁移演练 | `python temps/rehearsal_serial_log_origin.py` | 全新安装 / 重启恢复（config+custom 按开关恢复、关闭不监听）/ 旧库升级（origin=config、开关保留）三路 PASS |
| Django 检查 | `python manage.py check` / `makemigrations --check` / `spectacular --validate` | 全过；OpenAPI 基线已更新 |
| 后端 lint | `ruff check` + `ruff format --check`（本次路径） | 全过 |
| 前端门禁 | `vue-tsc --noEmit` / `eslint` / `lint:styles` / `build` | 全过；组件 ≤500 行（335/147） |
| 模块边界 | `python utils/gen_arch_stats.py --check-boundaries` | 零违规 |
| 本地门禁 | `python run.py check` | 本次改动相关项全绿；剩余 3 个失败均在并行会话未提交文件（knowledge/service.py、case-manager 与 report-generator 测试），经需求方确认不进本次提交 |

## 二、人工验收清单（需求方于 2026-11-18 指示归档，视为验收确认）

入口：`/serial-log` → 无线端口（超管账号）。

- [ ] 头部展示本机监听 IP，复制按钮可用；设置 `DEVICE_LOG_ADVERTISE_HOST` 后展示配置值
- [ ] 新增端口（如 7008 / H717D / 115200）保存即「监听中」，其它端口日志不断流
- [ ] 新增一个已被占用的端口 → 红色错误提示「端口 X 监听失败：端口已被其它程序占用」，行内红色「监听失败」胶囊 + 原因；排除占用后点「重试」转「监听中」
- [ ] 编辑自定义端口 SKU → 仅该端口重启，新日志写入新通道文件；配置端口无编辑/删除入口
- [ ] 删除自定义端口 → 二次确认含验收降级警告；删除后端口消失、历史日志文件仍在
- [ ] 端口列来源徽标（配置/自定义）与 `IP:端口` 副行正确
- [ ] 非超管账号：开关禁用、无新增/编辑/删除入口，只读说明可见
- [ ] 后端重启后，开启的自定义端口自动恢复监听，关闭的不监听

## 三、存量问题登记（不在本次范围）

1. 全量 `migrate` 在全新库上被 `ai_assistant/0065_neutralize_prompt_vendor_samples` 的历史模型字段缺失（`prompt_verifier`）阻断——存量迁移链问题，本次演练按 serial_log 链验证。
2. `tests/serial_log/unit/test_log_keyword_catalog.py::test_catalog_files_exist` 断言已退役目录存在，经需求方批准随本次退役（单独 fix 提交）。