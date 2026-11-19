## 1. 名单数据

- [x] 1.1 在 `ai_assistant` 增加用户与模型配置的使用关系，写入只经 `api.py`；验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/unit -q -k model_grant` 覆盖空名单、重复关系和超级管理员默认关系。
- [x] 1.2 新建模型配置时只给超级管理员建立关系；验证：同组单测中普通用户名单不包含新配置。

## 2. 主动选择拦截

- [x] 2.1 模型列表、对话切换和助手保存模型共用一个名单校验，名单外请求不发起模型调用；验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api -q -k model_grant` 覆盖三类入口。
- [x] 2.2 增加仅超级管理员可写的名单接口，运营请求返回 403；验证：同一组接口测试覆盖授予成功和运营拒绝。
- [x] 2.3 前端主动选模型的入口请求 `selectable=1`，只渲染接口返回项。模型区目前没有第二份本地全量清单。验证：`frontend/src/modules/knowledge-search/api.ts` 的 `fetchEvalModelConfigs` 带 `selectable: 1`；名单外模型由接口测试 `test_selectable_list_hides_models_outside_grant` 保证不返回。

## 3. 上线补齐与工作流边界

- [x] 3.1 编写可重复执行的补齐迁移，按已有使用关系生成名单；验证：迁移测试连续执行两次后，同一用户与模型仍只有一条关系。
- [x] 3.2 工作流提交和开跑不按提交人名单过滤模型；验证：`python -m pytest -c tests/pytest.ini tests/task -q -k assistant_sop` 中名单外用户仍可提交已有工作流。

## 4. 边界

- [x] 4.1 跑 `openspec validate --change model-use-grant`，确认 delta 可校验；验证：命令退出码为 0。
- [x] 4.2 跑 `python utils/gen_arch_stats.py --check-boundaries`，确认 `task_list` 没有新增 `ai_assistant` 内部 import；验证：命令退出码为 0。
