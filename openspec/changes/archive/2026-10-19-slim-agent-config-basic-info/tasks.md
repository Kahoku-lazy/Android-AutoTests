## 1. 前端基本信息

- [x] 1.1 `constants.ts` 增加 `ASSISTANT_DUTY = "UI自动化"` 与 `ASSISTANT_WORKFLOW = "ui_auto_workflow"`；验证：两项常量各一处定义
- [x] 1.2 `AgentBasicInfo.vue` 去掉 `routeMode`，改为单一基本信息表单：名称 / 头像（上传 + 输入）/ 标签 / 描述 + 只读职责与工作流；验证：`npm run build` 通过
- [x] 1.3 `AgentDetail.vue` 删除循环次数、线路模型配置、模型校验三个区块与 `testConnection` / `activeRoute` / 上传目标线路逻辑；保存只提交 name/avatar/tags/description；验证：页面仅剩基本信息与保存按钮

## 2. 前端清理

- [x] 2.1 删除 `components/AgentRouteConfig.vue` 与 `components/ModelConfigField.vue`，并删除守护后者的 `tests/ai-assistant/p0/model-config-field.spec.ts`；验证：全仓 grep 零命中，`npm run test` 无模块解析失败
- [x] 2.2 更新 `frontend/src/modules/ai-assistant/AGENTS.md` 中「配置页」描述（只含基本信息与两项写死信息）；验证：文档不再描述模型/循环/校验区块

## 3. 后端入参收缩

- [x] 3.1 `AgentInputSerializer` 只保留 name / avatar / tags / description，删除模型/线路/状态/循环相关字段与两个 `validate_*`；验证：`python manage.py check` 通过
- [x] 3.2 `api.update_agent` 只应用四个基本信息字段，并把 name/avatar 镜像写入 `route_configs.device_control`（保留其余键）；验证：`manage.py check` 通过；实现为读-改-写，模型与 health 键不丢
- [x] 3.3 `api.create_agent` 只收四字段，模型字段用默认值，`route_configs` 写入 `device_control.name/avatar`；验证：`manage.py check` 通过
- [x] 3.4 删除 `encrypt_route_configs`、`__all__` 条目；保留 `encrypt_key`（`tests/api/test_task_submit_sop.py` 仍需用它构造线路配置）；验证：全仓 grep `encrypt_route_configs` 零代码命中

## 4. 门禁

- [x] 4.1 `python manage.py check` + `python manage.py makemigrations --check --dry-run` 通过（无迁移）
- [x] 4.2 `ruff check/format apps/ai_assistant` 通过
- [x] 4.3 `pytest tests/arch -q` → 24 passed；`gen_arch_stats --check-boundaries` 零违规
- [x] 4.4 前端 `npm run build` 通过；`npm run typecheck` 无报错；`npm run test` 仅剩既有 `TaskInputPanel` 规划输入断言（与本单无关）
