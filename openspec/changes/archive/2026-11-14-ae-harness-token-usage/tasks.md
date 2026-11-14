## 1. 创建层：交出密钥环境变量名

- [x] 1.1 `agents/models.py` 新增两字段不可变数据类（模型实例 + 密钥环境变量名），`create_model` 改为返回它；不重复解析配置。验证：`python -c "from engines.ae_harness.agents.models import create_model; c = create_model('govee_chat_flash'); print(type(c.model).__name__, c.api_key_env)"` 打出 `OpenAIChatModel GOVEE_API_KEY`
- [x] 1.2 `agents/creator.py` 的 `create_agent` 返回值改为两段（`.agent` + `.api_key_env`）；不新增第二个创建入口，三个入参含义不变。验证：`python -c "from engines.ae_harness.agents.creator import create_agent; b = create_agent('n','UI_EXECUTOR_PROMPT','deepseek_chat_flash'); print(b.api_key_env)"` 打出 `DEEPSEEK_API_KEY`
- [x] 1.3 在 `agents/AGENTS.md` 与 `agents/README.md` 登记「出口返回两段」的约定，并说明它不违反「禁止给角色加第四样东西」。验证：人工核对文档与代码一致

## 2. 事件层：形状与逐次采集

- [x] 2.1 新增 `engines/ae_harness/event/usage.py`：`TokenUsage` 八字段（密钥环境变量名 + 轮次 + 起止时刻 + 四类 token）+ `UsageSummary` + `summarize`；模块只依赖标准库。验证：`python -c "from engines.ae_harness.event.usage import TokenUsage"` 成功，且该模块不 import 同包任何模块
- [x] 2.2 `summarize` 按密钥环境变量名归组：给出每组次数与四类 token 合计；空标签归到空组不丢弃。验证：单测断言三次同密钥调用归一组、空标签仍被计数
- [x] 2.3 `event/record.py` 的 `RunRecord` 增加 `usages`（默认空列表）与 `api_key_env`（默认空串）两个字段。验证：不传标签直接跑入口不因缺字段报错
- [x] 2.4 `AgentEventRecorder` 增加仅关键字、默认空的标签参数；在模型调用结束分支构造 `TokenUsage` 并收集，轮次沿用既有计数。验证：单测喂两次模型调用结束事件得到两条记录且不合并
- [x] 2.5 时间合成：用本次运行起始墙钟 + 相对偏移得到绝对时刻，锚点缺失时留空不伪造。验证：单测断言有锚点可解析、无锚点为空串
- [x] 2.6 汇总行补写密钥环境变量名；四类 token 分别统计不互加。验证：实跑后读 `summary` 行能看到 `api_key_env`
- [x] 2.7 `event/__init__.py` 导出新增形状；`event/AGENTS.md` 登记口径（一次调用一条、缓存是输入子集、只记环境变量名不记明文）。验证：文档与实现一致，检查器通过

## 3. 入口：解包与透传

- [x] 3.1 `assistant/agent_executor.py` 解包两段并把标签传给记录器。验证：入口实跑后产物目录结构与控制台字段不变
- [x] 3.2 `assistant/agent_verifier.py` 同上。验证：输出结构不变
- [x] 3.3 `workflow/sop/runner.py` 的 `run_sop` 增加带默认值的标签参数并透传给记录器。验证：不传标签时 SOP 仍能跑完并产出记录
- [x] 3.4 `workflow/sop_runner.py` 把执行者的标签透传给 `run_sop`。验证：跑完后汇总行含 `api_key_env`

## 4. 测试资产

- [x] 4.1 测试目录放置用例，覆盖：创建两段返回、标签透传、两次调用各自成条、按密钥归组、缓存不互加、绝对时刻可还原与无锚点留空。验证：`python -m pytest -c tests/pytest.ini tests/engines/ae_harness -q` 全绿
- [x] 4.2 守卫用例：断言观测层不导入 `django` / `backend` / 创建层，且用法模块只依赖标准库；含一条自检用例（合成违规源码必须被报出）。验证：该用例通过，且故意加一句 django 导入时失败

## 5. 门禁与收尾

- [x] 5.1 `cd .agents/skills/engines-docstring-check && python -m scripts.docstrings check --path engines/ae_harness` 归零。验证：0 error / 0 warn
- [x] 5.2 `python -m ruff check` 与 `python -m ruff format --check`（engines/ae_harness + tests/engines/ae_harness）全过。验证：退出码 0
- [x] 5.3 `.agents/skills/engines-agents-style-check` 确认新增文件不引入新告警。验证：新增文件无命中
- [x] 5.4 `python run.py check` 与改造前基线对比，确认没有新增失败项。验证：失败项集合与改造前一致
- [x] 5.5 导入冒烟：walk 全部子模块并 import，0 失败。验证：输出「失败模块数: 0」
## 6. 混跑标签（真机验证时发现的缺口）

- [x] 6.1 密钥绑定到角色：`AgentEventRecorder` 收「agent 名 → 密钥环境变量名」映射（`role_api_keys`），每次调用按 `reply_id` 反查所属角色取标签；不再按 reply 顺序猜、也不再整轮共用一个。验证：`test_label_follows_agent_name` / `test_label_persisted_on_model_call_rows` / `test_unregistered_role_falls_back` 通过
- [x] 6.2 逐次调用的密钥名写进 `ModelCallEndEvent` 行，汇总行补 `by_api_key_env`。验证：真机混跑（执行者 govee / 验收者 deepseek）后只读 JSONL 复算，GOVEE 2 条 / DEEPSEEK 3 条与内存汇总逐项相等