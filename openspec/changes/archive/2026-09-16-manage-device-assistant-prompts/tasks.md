## 1. 数据模型与灌数

- [x] 1.1 在 `AIAgent` 增加 `prompt_planner` / `prompt_executor` / `prompt_verifier`（`TextField`，default `""`），`makemigrations`；验证：`python manage.py makemigrations --check` 通过且生成迁移含三列
- [x] 1.2 数据迁移将现行三份引擎常量**快照**写入所有已有 `AIAgent`（禁止 import 已留空的常量）；验证：对测试库跑 migrate 后三字段非空

## 2. API 与装配

- [x] 2.1 `api.py` 增加 `get_device_prompts` / `update_device_prompts`（空串拒绝、一次写三列），`__all__` 同步；验证：单测「保存成功 / 空串拒绝不落库」
- [x] 2.2 新建 `views_prompts_drf.py` + 路由 `GET /api/ai/device-prompts`、`POST /api/ai/device-prompts/update`（信封、超管写、无平台智能体 404）；验证：API 单测覆盖读 / 写 403 / 空串 400 / 404
- [x] 2.3 `build_request` 读取三字段，空则抛含角色名的错误，填入 `TaskRequest.system_prompts`；更新 `test_ai_engine_config.py` 与 `test_ai_task_title_attach_dispatch.py` 的 agent 夹具；验证：`pytest tests/graybox/unit/test_ai_engine_config.py tests/graybox/unit/test_ai_task_title_attach_dispatch.py`

## 3. 引擎注入与常量留空

- [x] 3.1 `TaskRequest` 增加 `system_prompts`；`build_device_models` / `AgentRole` 使用注入值；`PLANNER_PROMPT` / `VISION_PROMPT` / `VERIFIER_PROMPT` 赋值为 `""`，`RoleSpec.prompt` 为空；验证：单测「注入正文出现在 Agent system_prompt」且常量 `== ""`
- [x] 3.2 `model_test` 等管理命令从平台智能体读提示词再 `build_request`（或显式传入），不得再依赖引擎常量；验证：命令装配路径无空提示词回退

## 4. 前端工具箱

- [x] 4.1 `api/toolbox.ts` 增加 fetch/update device-prompts；`ASSEMBLY_SOURCES` 增加无总闸的 `prompt` 来源；左侧不渲染该行开关、不进生效芯片；验证：`frontend/tests` 覆盖 helper（来源列表 / 芯片不含 prompt）
- [x] 4.2 `ToolboxPanel` 选中该来源时右侧三角色 Markdown 渲染（`renderSkillMarkdown`）；`canManage` 可编辑 textarea + 预览并一次保存；非管理员只读；空保存前端拦截；验证：相关 composable/组件单测 + 浏览器走只读与保存主路径

## 5. 文档与门禁

- [x] 5.1 更新 `dev_docs/DEV_TEST/接口文档/API-AI助手.md` 与模块 `AGENTS.md`（工具箱第三来源）；验证：文档描述与路由一致
- [x] 5.2 关单：`python manage.py check`、相关 ruff、`pytest`（本变更单测）、前端构建或既有门禁、`python tools/gen_arch_stats.py --check-boundaries`；验证：上述命令通过
