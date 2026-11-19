## 1. 后端数据层

- [x] 1.1 在 `backend/apps/ai_assistant/models.py` 新增 `AIRoleKind`（`role` 外键 CASCADE、`kind` 三选一、`created_at`，两条唯一约束 `uniq_ai_role_kind_role` / `uniq_ai_role_kind_pair`），验证：`python manage.py makemigrations ai_assistant --name airolekind` 生成迁移后 `python manage.py makemigrations --check` 无待生成项
- [x] 1.2 在 `migrations/0076_airolekind.py` 写入保守回填（名称按 `[-_]` 切词，命中整词 `EXECUTOR` / `VERIFIER` / `PLANNER` 才补）与可逆反向（清空标签表），验证：`python manage.py migrate ai_assistant` 后再 `migrate ai_assistant 0075` 双向都成功
- [x] 1.3 在 `services/agent_configs.py` 增加 `replace_kinds(role, kinds)`（差集写法，同一事务）并给 `list_roles()` / `get_role()` 加 `prefetch_related("kinds")`，验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant -m unit`（存量 `test_role_registry.py` 为先行失败，见本次暂停说明）

## 2. 后端契约与写库入口

- [x] 2.1 `serializers.py` 的 `RoleInputSerializer` 增加 `kinds`（ChoiceField 子项 + 去重与「最多 1 项」校验），`RoleOutputSerializer` 增加 `kinds = SerializerMethodField()`；「新建必须恰好 1 项」在 `RoleViewSet.create` 校验（PATCH 需允许空数组），验证：`tests/ai_assistant/api/test_role_kinds.py` 覆盖缺省 / 空 / 两项 / 非法值四种入参
- [x] 2.2 `api.py` 的 `create_role` 增加 `kinds` 参数并与配置同事务写入；`update_role` 由 services 增加 `kinds` 参数（None=不改动），保持写库只经 `api.py`，验证：`ruff check backend/apps/ai_assistant` 通过 + 契约用例全绿
- [x] 2.3 `views_drf.py` 的 `RoleViewSet.create` / `partial_update` 从 `validated_data` 取出 `kinds` 后透传，`retrieve` / `list` 无需改动即带出 `kinds`，验证：`GET /api/ai/roles/` 每条含 `kinds` 数组、`POST` 不传返回 400
- [x] 2.4 补 `tests/ai_assistant/api/test_role_kinds.py` 用例：创建带类型、PATCH 换类型、PATCH 清空、两项被拒、删除角色级联删除标签、存量无类型返回 `[]`，验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_role_kinds.py` 11 passed

## 3. 前端契约与展示

- [x] 3.1 `ops-console/types.ts` 增加 `OpsAgentKind` 联合类型、`OpsAgent.kinds`、`OpsAgentInput.kinds`；`constants.ts` 增加 `OPS_AGENT_KIND_OPTIONS` / `OPS_AGENT_KIND_LABELS` / `OPS_AGENT_KIND_UNSET` 与「类型」列定义（位于名称后、`width: 130`），验证：`npx vue-tsc --noEmit` 通过
- [x] 3.2 新增 `components/OpsAgentKindTags.vue`：chip 渲染 0..N 个类型、空数组显示「未分类」，样式只用 tokens（实线、`--app-size-xs`、`--app-radius-sm`），验证：`tests/ops-console/p0/agents-kind.spec.ts` 断言四种渲染状态
- [x] 3.3 `agents.vue` 的 `#cell-kinds` 接入该组件；抽屉表单在「名称」后加 `el-radio-group` 三选一，草稿 ↔ 入参互转与校验下沉 `helpers/agent-form.ts`，未选时阻止提交并提示，验证：vitest 断言 payload 与校验提示 + 真后端浏览器验收（见 4.3）
- [x] 3.4 补 `frontend/tests/ops-console/p0/agents-kind.spec.ts` 用例：类型列位置与顺序、chip 三种状态、编辑预填、未选类型不发起请求、未知取值兜底，验证：`npx vitest run tests/ops-console` 51 passed

## 4. 门禁与验收

- [x] 4.1 后端关单门禁：`python manage.py check`、`python manage.py makemigrations --check`、`ruff check` + `ruff format --check backend/apps/ai_assistant` 全通过；`pytest -m "unit or integration"` 为 21 failed / 637 passed，与 HEAD 独立 worktree 的 21 failed / 585 passed **逐条一致**（仓内既有欠账，非本次引入）；`openapi-schema` / `openapi-coverage` 已通过重生成基线转绿
- [x] 4.2 前端关单门禁：`cd frontend && npx vue-tsc --noEmit && npx eslint src/modules/ops-console && npm run lint:styles && npx vitest run tests/ops-console` 全通过
- [x] 4.3 真实浏览器验收（Playwright + 真实后端）：类型列顺序为名称/类型/模型配置/系统提示词/操作，存量显示「未分类 / 验收者 / 执行者」，新建未选类型被拦且不发请求，选「验收者」保存后列表回带该标签，验证：截图 `temps/shots/kind-0{1,2,3}.png`
- [x] 4.4 OpenSpec 收尾：`openspec validate ops-agent-role-kind --strict` 通过；按需求方指示执行 `openspec archive ops-agent-role-kind`，delta 同步进 `ai-role-registry` / `ops-agent-config` 主 spec
