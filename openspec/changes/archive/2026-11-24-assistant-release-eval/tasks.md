## 1. 草稿与版本

- [x] 1.1 为助手和工作流增加草稿状态，新建默认为草稿，普通用户访问返回 404；验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api -q -k release` 覆盖作者可见和普通用户不可见。
- [x] 1.2 发布时经 `ai_assistant/api.py` 写入不可变版本，版本不含密钥明文；验证：同组测试发布后修改提示词，旧版本正文不变。
- [x] 1.3 修改运行字段时退回草稿并保留旧版本，只改显示名、头像、笔色不退回；验证：单测分别覆盖两类保存。
- [x] 1.4 保存请求校验版本戳，后保存的一方整次失败；验证：单测用旧版本戳保存返回冲突且内容不变。

## 2. 使用方读取版本

- [x] 2.1 新对话使用当前已发布版本，已发送的对话栏保持原版本；验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant -q -k thread` 覆盖新旧两栏。
- [x] 2.2 工作流提交记下版本号，开跑和重跑只读该版本；验证：`python -m pytest -c tests/pytest.ini tests/task -q -k assistant_sop` 在发布新版本后重跑旧任务，断言仍是旧提示词。
- [x] 2.3 删除仍只删工作流记录，历史任务保留。未开跑任务的版本号在任务行上，不随删除回读名片。验证：`tests/ai_assistant/api/test_sop_workflows.py::test_delete_removes_only_workflow`。

## 3. 评测

- [x] 3.1 增加随代码发布的六条样本，页面与 pytest 读取同一份；验证：样本加载测试断言两条入口的样本标识一致。
- [x] 3.2 在评测模块实现五把纯函数尺子，缺字段跳过，失败清单不打综合分；验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/unit -q -k eval_ruler` 覆盖驳回次数、空阶段、连续重复和隔着验收。
- [x] 3.3 自测使用样本与纯函数尺子，不调用真实模型或设备。超时与外部调用数由尺子测试锁定为纯计算。验证：`tests/ai_assistant/unit/test_eval_rulers.py`。
- [x] 3.4 发布只认当前指纹、当前样本集和空清单，超级管理员也不能跳过；验证：接口测试覆盖未自测、改内容后发布和超级管理员跳过三类拒绝。
- [x] 3.5 发布比对最新自测记录的样本标识。样本集变化后旧指纹不再相符，已发布版本不回退。验证：`eval_passed` 要求 `sample_ids` 与当前启用样本一致，见 `test_publish_without_eval_is_rejected_even_for_superuser`。

## 4. 页面与旧数据

- [x] 4.1 助手页显示草稿标识、自测和发布结果，普通用户不显示草稿；验证：`cd frontend && npx vitest run tests/ai-assistant`。
- [x] 4.2 编写可重复的旧数据迁移，把现有记录标为已发布并生成一个初始版本；验证：迁移测试执行两次后每条旧记录仍只有一个初始版本。

## 5. 边界

- [x] 5.1 跑 `openspec validate --change assistant-release-eval`，确认两份新 spec 与三份 delta 可校验；验证：命令退出码为 0。
- [x] 5.2 跑 `python utils/gen_arch_stats.py --check-boundaries`，确认评测与版本读取没有新增跨 App 内部 import；验证：命令退出码为 0。
