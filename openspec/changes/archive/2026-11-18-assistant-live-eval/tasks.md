## 1. 运行与过程

- [x] 1.1 为评测运行和逐条过程新增模型与迁移，写入只经过 `ai_assistant/api.py`；验证：`python manage.py makemigrations --check` 通过，且运行、过程的创建与终态更新有单测。
- [x] 1.2 助手与 SOP 的发布改为只认新运行的指纹、当前样本集和空清单，旧 `scripted` 记录不再放行；验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_release.py -q` 覆盖未评测、改内容后失效、旧记录不放行。

## 2. 假世界与运行链

- [x] 2.1 在 `backend_bridge` 增加同名假工具装配，签名与勾选工具一致，只记录调用并返回剧本，不调用 adb、用例库或文档实现；验证：`python -m pytest -c tests/pytest.ini tests/engines/backend_bridge/unit -q -k fake_world` 断言无真实副作用。
- [x] 2.2 助手评测走名片装配和同一对话实例的两轮探针，SOP 评测走两侧名片与平台 UI 步骤；验证：替身模型测试覆盖第二轮同一实例、一次通过、驳回后再通过、验收者被诱发写操作。
- [x] 2.3 目标流和团队流的评测请求直接拒绝且不创建运行；验证：接口测试返回明确原因，且不产生运行记录。

## 3. 规则、费用与接口

- [x] 3.1 用四条纯函数规则读取本次过程：未勾选工具、验收者写操作、连续重复、助手实例变化；中间隔着验收不算重复，不打综合分；验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/unit -q -k live_eval_ruler`。
- [x] 3.2 每次模型调用以 `assistant_eval` 入账，重复轮次不翻倍，入账失败只记日志；验证：账本单测覆盖一条调用一条记录、重复提交和入账异常不中断过程落库。
- [x] 3.3 提供开始、进度与过程查询接口，作者只能评测自己可编辑的草稿，过程响应不含密钥和图片；验证：接口测试覆盖 403、进度条数和过程字段。

## 4. 页面

- [x] 4.1 评测页改为选择对象后开始、轮询进度、逐条结果和点开过程，文案只用「规则通过」；目标流和团队流选择后直接显示不可评，不发请求；验证：`cd frontend && npx vitest run tests/ai-assistant`。
- [x] 4.2 评测页沿用 Doodle Craft 共享状态件，不新增魔法字符串和硬编码字号；验证：`cd frontend && node tests/check-style-gates.mjs`。

## 5. 门禁

- [x] 5.1 跑 `python utils/gen_arch_stats.py --check-boundaries`，确认评测没有新增跨 App 内部 import；验证：命令退出码为 0。
- 【已取消 · 未做取消】5.2 跑 `python run.py check`，确认本地门禁通过；验证：命令退出码为 0。
