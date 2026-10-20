## 1. 数据模型与迁移

- [x] 1.1 在 `apps/case_manager/models.py` 用 `SYSTEM_CHOICES` / `CASE_TYPE_CHOICES` / `PRIORITY_CHOICES` 替换 `TEST_TYPE_CHOICES`，为 `TestDefinition` 增删字段，并新增 `CaseStep`（表 `cm_case_steps`，`case` 外键 CASCADE、`sort_order`、`action`、`assertion`、索引 `cm_case_step_case_idx`）；验证 `python manage.py check` 通过、`python manage.py makemigrations --check --dry-run` 能列出待生成变更（说明模型已改）
- [x] 1.2 生成迁移 `0022` 并手写整理 ops 顺序为「加三列 → 建 `cm_case_steps` → `RunPython` 折叠旧数据 → 删 `test_type` / `expected_result`」，反向 `noop` 并在文件头写明不可逆；验证 `python manage.py sqlmigrate case_manager 0022` 输出的列操作顺序与设计一致
- [x] 1.3 实现折叠逻辑：`test_type` 按 `app→ANDROID+AUTO`、`web→WEB+FUNC`、`api→WEB+AUTO`、`func→ANDROID+FUNC` 映射；旧 `steps` 全文写入唯一一步的 `action`（空则填 `（原用例无步骤描述）`），`assertion` 填 `（待补充断言）`；空表时直接跳过；验证迁移在本地库连续执行两次均成功且不重复建步骤
- [x] 1.4 写迁移后核对脚本（放 `temps/`）：用例行数、编号集合、每条用例步骤数 ≥ 1、断言无空值、旧 `expected_result` 文本未出现在任何字段；验证脚本输出全绿并把结果贴进变更说明
- [x] 1.5 同步 `apps/case_manager/admin.py`（`list_display` / `list_filter` 引用的旧字段）与 `serializers.py`（枚举校验器）；验证 `python manage.py check` 与进入 `/admin/` 打开用例列表不报错

## 2. 后端 api 层

- [x] 2.1 改 `api_definitions.create_definition` / `update_definition` 接收 `steps` 数组，在事务内整段替换步骤并返回 `steps` 与只读 `step_count`；验证新增单测：提交 3 步 → 读取顺序为 A/B/C、删除第 2 步后只剩 2 步
- [x] 2.2 改 `serialize_definition` 与 `get_definition` / 文件表格读取路径：`prefetch_related(Prefetch("steps", order_by=("sort_order","id")))`，不按行放大查询；验证 `django_assert_num_queries` 测试：200 条用例（每行 5 步）的单次表格请求查询次数有固定上限
- [x] 2.3 重写校验：标题非空、步骤 ≥ 1、每步 `action` 与 `assertion` 非空、单段 ≤ 2000 字符、枚举合法；错误消息带「第 N 步」；验证各失败分支的单测均返回 400 且消息含步骤序号
- [x] 2.4 同步 `views_drf.TestDefinitionViewSet` 的字段白名单与默认值（`priority=P1`、`system=ANDROID`、`case_type=AUTO`），删除 `test_type` / `expected_result` 转发；验证 `curl` 或 DRF 测试：带旧字段的请求被忽略且不报 500
- [x] 2.5 补 `/api/cases/definitions/` 写路径的回归单测（新建、更新、批量删除、校验失败回滚、鉴权归属）；验证 `pytest tests/api/test_case_definitions_api.py -q` 全绿

## 3. 前端

- [x] 3.1 改 `types.ts`：`CaseStep` DTO、`CaseDefinition` 增删字段、四组枚举选项；验证 `npm run build` 无类型错误
- [x] 3.2 改 `composables/useCaseSheet.ts`：`validateRow` 覆盖步骤非空/步数 ≥ 1，保存载荷改为 `steps` 数组并把服务端错误拼成「第 N 行 · 第 M 步」；验证保存失败时提示同时含行号与步骤号
- [x] 3.3 改 `CaseFileSheet.vue`：表头换成 优先级 / 系统 / 类型 / 业务类型 / 模块 / 步骤，步骤列只显示「N 步」摘要，双击打开步骤抽屉（新增、删除、上下移、应用回草稿）；验证抽屉内改动未点页面「保存」时不发写请求、表格步数摘要随应用更新
- [x] 3.4 改 `components/CasePagePreview.vue`：第二列表头改「系统·类型」，单元格拼接两个中文标签；验证宽屏预览表头恰好五项、且 ANDROID+AUTO 显示为「ANDROID · 自动化」
- [x] 3.5 前端门禁：`npm run build` 通过，并按 `vue-frontend-check` 清单逐项自检（布局裁剪、字号 ≥12px、无硬编码色、DRF 契约对照）记录结论；本次验证方式为静态扫描，结论 0 阻塞 / 0 严重，一.1 布局裁剪待浏览器确认

## 4. 门禁与验收

- [x] 4.1 后端门禁：`python manage.py check` + `ruff check apps/case_manager` + `ruff format --check apps/case_manager`，三项全过
- [x] 4.2 架构红线：`python tools/gen_arch_stats.py --check-boundaries` 通过（确认未新增跨 App 内部 import、写库仍只在 `api.py`）
- [x] 4.3 手工验收主场景：新建「H6810 详情页开关测试」（P1 / ANDROID / 功能 / 家电 / 设备管理，2 步：启动 App → 点击开关），检查表格显示「2 步」、抽屉顺序正确、预览拼接正确、编辑后刷新仍保留（2026-10-20 由用户在浏览器验收通过）
- [x] 4.4 迁移验收：用 `temps/verify_case_migration.py data` 在临时 SQLite 上造 4 条旧用例（app/web/api/func + 一条空步骤）执行 0022，确认映射为 ANDROID+AUTO / WEB+FUNC / WEB+AUTO / ANDROID+FUNC、每条恰 1 步、断言为占位文案、编号不变、旧预期结果文本未落库；正式库 `python manage.py migrate` 已执行并核对：3 条存量用例全部映射为 ANDROID+AUTO、各至少 1 步、3 条占位断言、零空断言
- [x] 4.5 收尾：在 `design.md` 的 Open Questions 记录遗留项（YAML 导出桥、`module` 枚举化），并确认 `openspec validate reshape-case-form-fields --strict` 仍通过
