## 1. 可见性语义：无主即平台共享

- [x] 1.1 `backend/apps/ai_assistant/api.py` 的 `filter_agents_for_user`：普通用户集合加入 `owner_id IS NULL` 分支，并更新函数 docstring（验证：`pytest tests/graybox/unit/` 相关用例通过）
- [x] 1.2 `backend/apps/ai_assistant/permissions.py` 的 `check_agent_visible`：`owner_id` 为空直接判可见，注释说明「无主 = 迁移种子，平台共享」（验证：`pytest tests/graybox/unit/` 通过）
- [x] 1.3 确认 `check_agent_owner` / `check_can_update_agent` 等写权限未放宽（验证：代码走查 + 既有 403 用例仍通过）

## 2. 默认设备执行智能体种子迁移

- [x] 2.1 `backend/apps/ai_assistant/migrations/0064_seed_default_device_agent.py`：库中不存在 `task_kind=device_control` 的智能体时种下 `Agent-01号`（`deepseek / deepseek-flash`、`route_configs.device_control` 带 name/avatar），存在则跳过（验证：`python manage.py check` + 迁移单测）
- [x] 2.2 同一迁移把 `owner_id IS NULL` 的智能体回填为「现存第一个超级管理员」，无超管时静默跳过且 `owner_id` 保持为空（验证：迁移单测覆盖两种情形）
- [x] 2.3 反向迁移只删除本迁移创建的那一行（按 `task_kind` 精确匹配，且已挂任务时跳过），不触碰人工数据（验证：迁移单测 + 代码走查）

## 3. 测试

- [x] 3.1 新增单测：普通用户在智能体列表里能看到 `owner_id` 为空的智能体（验证：`pytest -c tests/pytest.ini tests/graybox/unit/`）
- [x] 3.2 新增单测：普通用户用无主智能体提交任务不会被判不可见（验证：同上）
- [x] 3.3 新增单测：种子迁移幂等——已有设备执行智能体时不新增、无超管时 owner 为空、有超管时回填（验证：同上）
- [x] 3.4 回归既有可见性/权限用例全绿（验证：`pytest -c tests/pytest.ini tests/graybox/unit/ tests/api/`）

## 4. 文档与门禁

- [x] 4.1 `README.md` 快速开始补一句：`migrate` 后默认已有设备执行与用例编写两条智能体，无需手工创建（验证：人工核对文字）
- [x] 4.2 通过本地质量门禁（验证：`python run.py check` 退出码 0）
