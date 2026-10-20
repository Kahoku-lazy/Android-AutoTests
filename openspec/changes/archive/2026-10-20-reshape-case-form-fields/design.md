## Context

- 现状：用例行集中在 `cm_test_definitions` 单表，字段为 `title` / `test_type` / `business_type` / `module` / `precondition` / `steps`(Text) / `expected_result`(Text)。前端 `CaseFileSheet.vue` 是内联表格编辑（双击单元格改文本），`CasePagePreview.vue` 是只读五列预览。
- 执行侧：`engines/agents/workflow/ui_auto_workflow.load_test_cases` 从 YAML 读 `title` 与 `steps[{action, assert}]`；库里的用例目前与执行链没有连接。因此这次的数据形状要按「将来能直接导出成可执行 YAML」来定，而不是只为表格好看。
- 历史约束：`0020_project_document_cases` 曾清库重塑为文档用例，同时删掉了 `priority` 与 `steps_json`。这是第二次动这块 schema，且已有真实用户数据，**禁止再用清库方式解决字段变更**。
- 平台约束：表前缀 `cm_`；响应信封 `{status, data}`；HTTP JSON 一律 snake_case；写库只经 `apps/case_manager/api.py`，View 只分发。

## Goals / Non-Goals

**Goals:**

- 一次迁移完成「旧两维压一维」到「两维正交」的字段重塑，保留全部存量用例行与编号。
- 把步骤从自由文本改成有序集合，并明确读写语义（整段替换、单事务、一次性预取），使保存行为可预测。
- 表格不再承载步骤全文，编辑入口收敛到一个面板。

**Non-Goals:**

- 不做 YAML 导入导出、不接执行链（库到引擎的桥留给后续变更）。
- 不做步骤级统计与步骤模板复用（决定是否改成按 id 差异更新）。
- 不做 `module` 枚举化、不做并发编辑乐观锁、不调整移动端断点。

## Decisions

### D1 步骤存独立子表，而不是 JSON 字段

选子表 `cm_case_steps`（`case_id` / `sort_order` / `action` / `assertion`），而非在 `cm_test_definitions` 上加 `JSONField`。理由：步骤是将来要挂元素定位、截图、超时的实体，子表可以逐列扩展；JSON 字段每次扩字段都要改读写两端并把历史数据当无结构文本处理。备选 JSON 的优点是整段保存最简单，但代价是后续每加一个步骤属性都要改一次结构约定。

### D2 保存语义定为「整段替换」，而不是按 id 差异更新

提交完整序列 → 事务内删除该用例全部步骤 → 按提交顺序 `bulk_create`。理由：步骤没有任何外部引用（执行结果按 `case_id` 记，不按步骤记），整段替换不存在悬空引用；代码量是差异更新的一半，也不会出现「删一半留一半」。

代价：每次保存步骤 id 全会变。触发改回差异更新的条件写死为「出现按步骤 id 的外部引用或步骤级统计」，届时必须让客户端回传 `id`。

### D3 全链路命名 `assertion`，只在与 YAML 交界处映射 `assert`

模型字段、DB 列、API 报文、前端 DTO 全部用 `assertion`；`assert` 是 Python 关键字，`obj.assert` 无法解析。备选是「DB 列保留 `assert`、Python 属性叫 `assertion`」，被否掉的理由是同一概念在库与报文里出现两个名字，排查时更容易看错。

**这笔债必须在后续 YAML 导出变更里显式偿还**：导出时把 `assertion` 写成 `assert`，并在导出后做一次自检（导出的每条步骤 `assert` 非空），否则执行器会读到空断言并静默判定通过。

### D4 编号继续用主键，不新增 `case_id` 列

表单上的「编号」= `cm_test_definitions.id`（`TC-YYYYMMDD-NNNN`），只读展示。理由：主键已被 `tr_test_results.case_id`（字符串）引用，且编号要跨项目稳定；再引入一个人工编号必然出现「两个编号对不上」。备选新增 `external_id` 只在接入外部用例库时再做。

### D5 `expected_result` 内容直接丢弃，迁移后的断言统一占位

按已确认的决策，旧预期结果不入库，迁移生成的唯一一步断言填 `（待补充断言）`。这不是无损方案：存量用例的验收信息会全部丢失，等于每条都要人工补断言。已知接受。空步骤的用例另用 `（原用例无步骤描述）` 兜底，保证「步骤至少 1 条 + 断言非空」的校验在迁移后自洽。

### D6 读取用 `prefetch_related` + 排序 `Prefetch`，不拆两次请求

文件表格接口一次返回该文件全部用例，每行带 `steps` 数组与只读 `step_count`。备选「列表只给计数、打开抽屉再取详情」被否：多一次往返，抽屉要等网络，且现有交互是「行内即时可看」；在单文件用例数百条的量级下预取完全够用。若单文件超过约 1000 行再改成按需加载。

排序必须显式 `Prefetch("steps", queryset=CaseStep.objects.order_by("sort_order", "id"))`，否则数据库不保证返回顺序，`step_count` 与顺序会对不上。

### D7 校验放在 `api_definitions`，错误信息带步骤序号

`views_drf` 只做字段白名单转发；校验在 `api.py` 层抛 `ValueError`，由既有 `_raise_or_conflict` 转成 400。**不新增自定义异常类**（引擎/后端规范禁止），因此错误定位靠消息文本：`第 2 步：断言不能为空`。行号由前端补——保存是逐行 PATCH/POST，一次请求只针对一条用例，前端知道自己在存第几行，拼成「第 3 行 · 第 2 步」提示。

### D8 枚举真相源在后端 choices，前端 `types.ts` 同批对齐

不新增「枚举接口」：四组枚举在一次发布里前后端同改，多一个接口反而多一处漂移点。但 `TEST_TYPE_CHOICES` 必须替换为 `SYSTEM_CHOICES` / `CASE_TYPE_CHOICES` / `PRIORITY_CHOICES` 三个常量，`admin.py`、`serializers.py` 的校验器同步改，避免出现「模型改了、admin 列表还引用旧字段」这类运行时报错。

### D9 迁移用 `RunPython` 折叠，反向 `noop` 并显式声明不可逆

迁移顺序固定为：加三个新列（带默认值）→ 建 `cm_case_steps` → 数据折叠 → 删 `test_type` / `expected_result`。折叠前先判空表（新环境直接跳过）。反向迁移不重建旧字段，迁移文件头部写明「需用备份恢复」，与 `0020` 的警示风格一致。

## 模块防火墙自检

- **跨 App import**：本设计只在 `apps/case_manager` 内部改动，不新增任何跨 App 依赖。`apps/dashboard/views.py` 对 `TestDefinition` 只做 `count`，不读 `test_type`，删字段不影响它。
- **写库路径**：所有 INSERT/UPDATE/DELETE（含步骤子表）收敛在 `apps/case_manager/api_definitions.py`；`views_drf.py` 只转发，不直接操作 ORM。
- **前端**：只经 `modules/case-manager/api.ts` 走 `djangoClient`，不新增直连出口。
- **表前缀**：新表 `cm_case_steps`，符合 `cm_` 约定。
- **未经 api.py 的例外**：无。

## Risks / Trade-offs

- [存量断言全部丢失] → 占位文本可被检出（固定文案），后续可加「待补断言」筛选；本次不实现筛选，但占位文案一旦确定不得再改，否则无法检索。
- [步骤 id 每次保存都变] → 当前不建立任何按步骤 id 的引用；将来要做步骤级统计时，必须先改 D2 为差异更新。
- [忘记预取导致 N+1] → 在 api 层写一条查询数断言测试（`django_assert_num_queries`），固定 200 行数据的查询次数上限。
- [前后端字段不同批发布] → 旧前端读不到 `steps` 字符串会显示空；发布必须同批，且前端类型检查与 `vue-frontend-check` 作为门禁。
- [`assertion` ↔ `assert` 静默丢断言] → 记录在 D3；后续导出变更必须带 round-trip 自检。
- [空步骤用例迁移后仍不合规] → 迁移用占位动作兜底，并在迁移后跑一次「所有用例步骤数 ≥ 1 且断言非空」的核对查询。
- [再次清库] → 本次迁移禁止任何 `delete()`；只做字段增删与数据折叠。

## Migration Plan

1. 迁移前备份数据库文件（SQLite 停服复制 / MySQL dump），记录用例总数与编号集合。
2. 生成 `0022`（手写 ops，不用 `makemigrations` auto 的字段顺序）。
3. 本地连续执行两次迁移（验证不会重复折叠）。
4. 迁移后核对：用例行数不变、编号集合不变、每条用例步骤数 ≥ 1、断言无空值。
5. 代码回滚策略：迁移不可逆，回滚 = 恢复备份 + 回退后端与前端同一提交。
6. 发布顺序：后端迁移 → 后端代码 → 前端（同批），避免中间态出现旧前端读新接口。

## Open Questions

- `module` 何时改为项目内枚举 + 允许新增（解决当前自由文本产生的近似重复值）——不影响本次字段形状。
- 步骤级统计（按步骤维度的失败率）是否进入路线图——它决定 D2 何时切换成差异更新。
