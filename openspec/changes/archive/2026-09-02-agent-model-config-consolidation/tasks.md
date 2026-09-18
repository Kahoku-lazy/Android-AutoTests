## 1. 后端数据模型

- [x] 1.1 `apps/ai_assistant/models.py` 的 `AIAgent` 新增 `strong_model_name`（`CharField(max_length=100, default="", blank=True)`）与 `strong_enabled`（`BooleanField(default=False)`）；验证：`python manage.py makemigrations ai_assistant` 生成迁移文件，默认值安全（历史数据不启用强模型）

## 2. 后端契约与装配

- [x] 2.1 `apps/ai_assistant/serializers.py` 的 `AgentInputSerializer` 增 `strong_model_name` / `strong_enabled` 入参，`AgentDetailSerializer` 增两字段输出 DTO；验证：`python manage.py check && ruff check apps/ai_assistant/serializers.py` 通过
- [x] 2.2 `apps/ai_assistant/api.py` 的 `create_agent` / `update_agent` 读写 `strong_model_name` / `strong_enabled`（写库仍走 api.py）；验证：`python manage.py check` 通过
- [x] 2.3 `apps/ai_assistant/views/chat_views.py` 的 `_build_manager` config 增传 `strong_model_name` / `strong_enabled`；验证：`ruff check apps/ai_assistant/views/chat_views.py` 通过
- [x] 2.4 单测覆盖 strong 字段装配与留空回退（`config.get("strong_model_name") or config.get("vision_model_name")`）；验证：`pytest tests/ai_assistant/test_agent_manager.py tests/ai_assistant/test_model_instance.py` 通过

## 3. 前端配置页三类模型

- [x] 3.1 `frontend/src/modules/ai-assistant/AgentDetail.vue` 的 form 增 `strong_model_name: ""` / `strong_enabled: false` 初值，保存 payload 携带两字段；验证：编辑页 loadAgentDetail 能回填、保存后后端落库
- [x] 3.2 `frontend/src/modules/ai-assistant/components/AgentModelConfig.vue` 模型配置扩为三类：主推理模型（`model_name`）、视觉模型（`vision_model_name`）、强模型（`strong_enabled` 开关 + `strong_model_name` 下拉，留空回退视觉模型并注明）；验证：`cd frontend && npm run build` 通过
- [x] 3.3 `frontend/src/shared/types/ai.ts` 的 `AgentRecord` 增可选 `strong_model_name?` / `strong_enabled?`；验证：`cd frontend && npm run build` 无类型报错

## 4. 前端卡片收敛与清理

- [x] 4.1 `AgentStickyNote.vue` 移除 `model-row`（模型下拉 + 保存模型按钮）+ 卡片「删除」按钮 + 相关 props（`pendingModel`/`confirming`/`modelOptions`）、emits（`update:pending-model`/`confirm-model`/`delete`）、computed（`modelDirty`）与样式（`.model-row` 等）；验证：`cd frontend && npm run build` 通过，卡片仅剩「对话 / 配置 / 测试」
- [x] 4.2 `index.vue` 移除 `:pending-model`/`:confirming`/`:model-options` 绑定与 `@update:pending-model`/`@confirm-model`/`@delete` 事件，及 `useAgentBoard` 解构中对应成员；验证：`cd frontend && npm run build` 通过
- [x] 4.3 `index.logic.ts` 移除 `pendingModels`/`confirmingId`/`confirmModel`/`deleteAgent`/`hasPendingModelChange`/`syncPendingModels` 及 `getModelOptions` 导入，`openAgent` 去掉「未保存模型」拦截；验证：`grep -r "confirmModel\|pendingModels\|getModelOptions\|deleteAgent" frontend/src/modules/ai-assistant` 无残留
- [x] 4.4 `api/agents.ts` 移除 `updateAgentModel` / `deleteAgent` 函数（`saveAgent` 保留）；验证：`grep -r "updateAgentModel\|api/agents" frontend/src` 无残留调用
- [x] 4.5 删除 `helpers/model-config.ts`（先 `grep getModelOptions|BUILTIN_MODELS` 确认无其他消费者）；验证：`cd frontend && npm run build` 通过

## 5. 门禁与文档同步

- [x] 5.1 后端门禁：`python manage.py check && ruff check apps/ai_assistant && pytest tests/ai_assistant -m "unit or integration"`；验证：命令全绿、无回归
- [ ] 5.2 前端关单：`cd frontend && npm run build` + skill `vue-frontend-check`；验证：门禁通过、卡片与配置页真实页面验证
- [x] 5.3 架构红线：`python tools/gen_arch_stats.py --check-boundaries`；验证：零违规
- [x] 5.4 文档同步：PRD-08 §5.2 智能体详情字段、ARCH-08 §4.2 字段契约补 `strong_model_name` / `strong_enabled`；验证：`python tools/gen_arch_stats.py --check-md` 通过
- [x] 5.5 端到端手测（≥2 次）：配置页配三类模型并保存 → 对话分别验证强模型开关 ON 短路、视觉/推理按意图路由；卡片页仅显示「对话 / 配置 / 测试」；验证：SSE 流式正常、路由正确、模型字段落库
