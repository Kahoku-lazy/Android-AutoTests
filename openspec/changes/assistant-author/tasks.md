## 1. 作者判定

- [x] 1.1 在 `ai_assistant` 增加作者授权记录，写入只经 `api.py`；验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/unit -q -k author` 覆盖授予、收回和重复授予。
- [x] 1.2 在 `backend/shared/users.py` 增加作者判定，超级管理员天然通过，且不改变 `is_operator()`；验证：同一组单测覆盖超级管理员、作者、运营和普通用户四类结果。

## 2. 写接口收紧

- [x] 2.1 助手的创建、修改、删除改为要求作者，运营不再放行；验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api -q -k assistant` 中运营请求返回 403 且不落库。
- [x] 2.2 工作流的创建、修改、删除改为要求作者；验证：同组接口测试中普通用户返回 403，作者请求仍按原字段校验。
- [x] 2.3 停用账号时删除作者授权，重新启用不恢复；验证：单测先停用再启用，创建请求返回 403。

## 3. 授权入口

- [x] 3.1 增加仅超级管理员可调用的授予与收回接口，作者调用返回 403；验证：接口测试覆盖成功授予、作者转授和自我授予三类请求。
- [x] 3.2 身份接口返回作者标记，前端按标记显示新建、配置和删除；验证：`cd frontend && npx vitest run tests/ai-assistant`，非作者看不到写入口。

## 4. 边界

- [x] 4.1 跑 `openspec validate --change assistant-author`，确认 delta 可校验；验证：命令退出码为 0。
- [x] 4.2 跑 `python utils/gen_arch_stats.py --check-boundaries`，确认没有新增跨 App 内部 import；验证：命令退出码为 0。
