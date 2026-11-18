## 1. 实施前协调与确认

- [x] 1.1 核对 `add-serial-log-custom-ports` 落地状态（`origin` 迁移是否已生成），确定本单建表/数据迁移的依赖编号（design.md D4 顺延规则）；重新核对 `backend/config/device_log_keywords.json` 现状（关键词数、功能点数、内容），与提案基线（67 / 56）有差异时以实施时点内容重新冻结快照。验证：实施记录写明迁移依赖编号与快照基线（计数 + 内容摘要）。
- [x] 1.2 将 design.md「红线变更申请」提交需求方确认（前端 serial-log AGENTS「改表仍走文件」句、后端 serial_log AGENTS 关键词表登记）。验证：获得明确同意后才允许任务 6.1 动这两份 AGENTS；未获批则停下上报，不得先改后报。

## 2. 后端数据层

- [x] 2.1 `backend/apps/serial_log/models.py` 追加 `LogKeyword` 模型（字段、`unique(keyword, feature_id, scope)`、scope 索引、`ordering=["sort_order","id"]`、`db_table="sl_log_keywords"`，按 design D1；不触碰 `LogPort` 与双轨制条款）。验证：`python manage.py check` 通过；`makemigrations` 生成建表迁移且编号在 1.1 确定的依赖之后。
- [x] 2.2 数据迁移：把 1.1 核对后的 JSON 内容以 Python 字面量冻结迁入（`scope="*"`、`sort_order` 按原顺序步长 10、`apps.get_model` + `get_or_create` 幂等；reverse 清空本表行）。验证：临时 SQLite 全新 migrate 后关键词数 / 功能点数与基线一致、行序与原表逐行一致；reverse 后表被移除且 JSON 文件仍在。
- [x] 2.3 双引擎迁移演练：sqlite 与 mysql 各做一次全新安装 + 升级。验证：两种引擎 migrate 均成功、计数一致、`makemigrations --check` 无遗漏；结果记入关单清单。

## 3. 后端读写路径

- [x] 3.1 `api.py` 追加：`list_keyword_rows()`（全量按 sort_order）、`keyword_mapping_for_sku(sku)`（并集 `scope="*"` ∪ `scope=sku`，返回可注入 `KeywordIndex` 的 mapping）、`upsert_keyword(...)` / `delete_keyword(row_id)`（scope 校验 `"*"` 或 `^[A-Za-z0-9_-]+$`，feature_id 续编 max+1，唯一键 update_or_create）。验证：新增 `tests/serial_log/unit` 用例（并集口径、专用不覆盖通用、重复登记不产生第二行、非法 scope 拒绝）全绿；`ruff check` 相关路径通过。
- [x] 3.2 `keywords.py` 的 `collect_keywords()` 改经 api 读库：`origin="db"`、`updated_at` 取表内 `max(updated_at)`（北京时间秒精度）、移除 `keyword_file` 字段、空表给可读 note 不抛错；保持只组装不写库。验证：`python manage.py check` + 单测覆盖空表 / 行序 / 计数口径（关键词按原文去重、功能点按模块+编号+名称去重）。
- [x] 3.3 接口契约对齐：`GET /api/serial-log/keywords/` 返回 features 条目含 `scope`、无 `keyword_file`、`origin` 为 `db|none`；更新既有契约断言。验证：`python -m pytest -c tests/pytest.ini tests/serial_log/api/test_serial_log_api.py -q` 通过；`python manage.py spectacular --validate` 通过。

## 4. 前端

- [x] 4.1 `api.ts` 类型：`LogKeywordFeature` 加 `scope`、移除 `keyword_file`、`origin` 收为 `"db"|"none"`；`helpers/log-keyword-rows.ts` 行结构加 `scope`、row-key 纳入 scope、新增 `filterKeywordRowsByScope` 纯函数，计数口径不变。验证：`cd frontend && npx vitest run tests/serial-log/p0/log-keyword-rows.spec.ts` 通过（含范围筛选与叠加搜索用例）。
- [x] 4.2 `constants.ts`：范围列标题、范围渲染映射（`*`→「通用」、SKU→「<SKU>专用」）、筛选选项文案、origin 标签加 `db`；移除 `LOG_KEYWORD_RESTART_HINT`。`LogKeywordPanel.vue`：COLUMNS 加第四列「范围」、搜索条旁加 `.sketch-kit` 范围下拉（选项从全量行动态派生）、模块配色仍按全量行首次出现顺序分配；样式只改本组件 `sl-*`/`lk-*` 私有类与 tokens。验证：`npm run build:check` 与 `npm run lint:styles` 通过；`npx vitest run tests/serial-log/p0/LogKeywordPanel.spec.ts` 通过（四列、筛选、无写请求）。
- [x] 4.3 面板底部来源说明改为「取值来自数据库 · 最近写入时间 · 刷新即取最新条目」，不残留重启文案。验证：面板 spec 断言 origin 文案与无「重启」字样；`npx vitest run tests/serial-log` 全绿。

## 5. 测试与遗留清理

- [x] 5.1 重写 `tests/serial_log/unit/test_log_keyword_catalog.py`：改为「DB 条目与冻结快照一致」校验（关键词 / 编号 / 模块 / 名称 / 行序 / scope 全通用），不再引用已删除的 `engines/agents` 路径。验证：`python -m pytest -c tests/pytest.ini tests/serial_log/unit -q` 通过。
- [x] 5.2 新增迁移集成测试（`tests/serial_log/integration`）：升级保留存量条目、全新安装不依赖数据文件、reverse 可回退。验证：`python -m pytest -c tests/pytest.ini tests/serial_log/integration -q` 通过。
- [x] 5.3 架构边界检查：无新增跨 App 内部实现 import、engines 零 django/apps 依赖、写入收敛 `serial_log/api.py`。验证：`python utils/gen_arch_stats.py --check-boundaries` 通过。

## 6. 文档与关单

- [x] 6.1 凭 1.2 的批准修改两份 AGENTS 条款（仅申请范围内的文本替换，不动双轨制等其它条款）；`backend/config/device_log_keywords.json` 头部 description 标注「已迁库为种子档案，勿再手改，真相源 sl_log_keywords」。验证：diff 仅含申请条款与标注；相关架构文档如有引用按 `python utils/gen_arch_stats.py --check-md --doc <文档路径>` 同步。
- [ ] 6.2 本地门禁与提交：`python run.py check` 通过；逐文件 `git add`（禁 `-A`）、Conventional Commits（如 `feat(serial_log): 关键词对照表落库并支持范围`）、推 `Kahoku`。验证：`ci-phase1.yml` 6 个 job 全绿。
- [ ] 6.3 人工验收：打开 `/serial-log` 日志关键词 Tab，核对四列、通用/各 SKU 范围筛选、搜索叠加、计数恒全量、来源说明为数据库；计数与 1.1 基线一致；非超管无任何写控件。验证：验收记录与截图存 `temps/`，随关单说明提交。

## 实施记录

- **1.1 基线（2026-11-18）**：`device_log_keywords.json` 67 关键词 / 70 行（关键词×功能点）/ 56 功能点，与提案基线一致；SHA256 `97a42dc55a46b7bba03df56702771b63c78e1c59739adcba3e11805a631c1553`。迁移依赖确定为 `serial_log.0003_logport_origin`（add-serial-log-custom-ports 已生成，未提交）；本单建表/数据迁移顺延为 0004/0005（以实施时 makemigrations 实际生成为准）。
- **1.2 批准（2026-11-18）**：需求方在会话中明确「红线变更申请（design.md 内）同意」；6.1 获准执行。
- **交错实施决策（2026-11-18，需求方选定）**：`add-serial-log-custom-ports` 正在实施（4/17），与本单共享 `models.py` / `api.py` / 前端 `api.ts` / `constants.ts` / 两份 AGENTS。本单先做零共享文件切片（关键词纯函数层 + 其测试）；上述共享文件的追加、以及依赖它们的模型/迁移/读路径/面板接线，待对方提交后再做，避免双向污染。
- **4.1 部分完成（2026-11-18，交错切片）**：`helpers/log-keyword-rows.ts` 已加范围支持（`LogKeywordRow.scope`、行标识含范围、`filterKeywordRowsByScope` / `scopeOptions` / `scopeLabel`、`SCOPE_GENERAL="*"` / `SCOPE_FILTER_ALL`、过渡类型 `LogKeywordScopedFeature`）；`tests/serial-log/p0/log-keyword-rows.spec.ts` 扩至 17 项（范围缺省/筛选/叠加搜索/计数不缩水/选项派生）。验证：`npx vitest run tests/serial-log` 37 项全绿、eslint 通过、`vue-tsc --noEmit` 全项目通过。**未完成部分**：`api.ts` 类型补 scope / 移除 keyword_file / origin 收 db|none——属共享文件，待对方提交后随 4.1 收尾。
