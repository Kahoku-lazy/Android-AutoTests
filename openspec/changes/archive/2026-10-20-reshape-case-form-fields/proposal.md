# 重新设计用例表单字段：系统/类型拆维 + 步骤子表

## Why

现有用例行只有「测试类型（app/web/api/func）」一个枚举，把「被测端」和「是否自动化」混在一起，无法按系统筛选、无法标优先级，也无法承载「每步一条断言」的真实用例写法；同时「步骤 + 预期结果」是两段自由文本，既不能逐步骤验收，也没法被执行侧直接消费。这次把字段模型一次性理顺，让表里写的用例具备可筛选、可校验、可执行的形状。

## What Changes

- **字段正交化**：删除 `test_type`，拆成两个正交枚举 —— `system`（ANDROID / WEB / IOS / API）与 `case_type`（FUNC 功能 / AUTO 自动化）。
- **新增 `priority`**：`P0` / `P1` / `P2`，默认 `P1`（枚举字符串，不用数字）。
- **业务类型保留三值**：家电 / 照明 / APP，不删「照明」。
- **步骤结构化**：删除行级 `steps`（纯文本）与 `expected_result`，改为子表 `cm_case_steps`（`sort_order` / `action` / `assertion`），通过 `case_id` 外键关联用例；断言下沉到每一步。
- **BREAKING** 接口契约：`steps` 由 `string` 变为 `Array<{id?, action, assertion}>`，新增只读 `step_count`；`test_type`、`expected_result` 两字段移除；`priority` / `system` / `case_type` 新增。
- **校验收紧**：标题非空、步骤至少 1 条、每步 `action` 与 `assertion` 均必填、单段长度 ≤ 2000、枚举合法；错误可定位到「第几行第几步」。
- **数据迁移（新增迁移 `0022`）**：旧 `test_type` 按映射写入新两维（`app→ANDROID+AUTO`、`web→WEB+FUNC`、`api→WEB+AUTO`、`func→ANDROID+FUNC`）；旧 `steps` 文本折叠为**一条**步骤的 `action`，`assertion` 统一填占位符 `（待补充断言）`；旧 `expected_result` 内容按决策直接丢弃（不折叠、不保留）。
- **右栏预览口径变更**：工作台预览第二列列名由「测试类型」改为「系统·类型」，单元格渲染系统标签与类型标签的拼接（如「ANDROID · 功能」）；列数、只读性与分页口径不变。

## 关联文档

- PRD-05-用例管理（该模块子 PRD 尚未编写，本变更即其字段与校验口径的来源）

## Capabilities

### New Capabilities

- `case-manager-case-form`: 用例表单的字段集合与四个枚举的取值口径、步骤子表的结构与读写语义（整段替换）、服务端校验规则与错误定位、旧字段到新字段的迁移映射规则。

### Modified Capabilities

- `case-manager-workspace-preview`: 「右栏用例预览只读且固定五列」这一需求中，第二列「测试类型」的呈现口径改变 —— 由单一 `test_type` 枚举标签变为 `system` 与 `case_type` 两个中文标签的拼接；列数、列名、只读性与分页口径不变。

## Impact

- **后端**：`apps/case_manager/` —— `models.py`（新增 `CaseStep`、改 `TestDefinition` 字段、新增枚举）、新增迁移 `0022`、`api_definitions.py`（序列化/校验/整段替换写入）、`api_ids.py` 不变、`views_drf.py`（字段白名单）、`serializers.py`。
- **前端**：`frontend/src/modules/case-manager/` —— `types.ts`（DTO 与四个枚举）、`composables/useCaseSheet.ts`（`validateRow` 与保存载荷）、`CaseFileSheet.vue`（列与抽屉式步骤编辑器）、`components/CasePagePreview.vue`（第二列拼接渲染）。
- **接口**：`/api/cases/definitions/` 系列（`create` / `partial_update` / `retrieve` / 文件表格读取）契约破坏性变更，前后端须同批发布。
- **测试**：`apps/case_manager` 相关单测（若有）与前端类型检查；不跑全量回归。
- **不做**：YAML 导入导出、`DB → 执行链`、按步骤维度统计失败率、`module` 枚举化、并发编辑乐观锁。
- **已知债务**：库与报文用 `assertion`，而执行侧 YAML（`dev_docs/H6810/h6810-card-style.yaml`）与 `engines/agents/workflow/ui_auto_workflow.py` 认 `assert`；做 YAML 导出时必须显式映射 `assertion → assert`，否则断言静默丢失。
