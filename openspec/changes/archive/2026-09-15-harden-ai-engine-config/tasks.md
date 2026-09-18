## 1. 前置核查（只读，不改代码）

- [x] 1.1 核查存量 `route_configs` 的 provider 取值与三角色模型名：验证 —— 用 `python manage.py shell -c` 取 `AIAgent.objects.values_list("route_configs", flat=True)`，去重后的 provider 全部落在合法集合内、各角色 `model_name` 非空；若出现集合外值或空模型名，先记录并订正对应配置行再继续（订正属数据操作，需单独确认）
- [x] 1.2 复核 `credential_type` 确实零消费方：验证 —— `grep -rn "credential_type" apps/ engines/ tests/` 命中仅 `provider_registry.py` 定义处与本次将改动的行，无其他读取方
- [x] 1.3 复核异常兜底路径存在：验证 —— 阅读 `views_drf.py:840-847` 确认 `_run_task_async` 的 `except Exception` 会把装配异常落成任务失败终态（若已被改动，本单需补捕获点）

## 2. A2 侧：provider 归一与装配期校验

- [x] 2.1 `provider_registry.py` 删除 `credential_type`，`PROVIDER_DEFAULTS` 收敛为「provider → base_url」：验证 —— `grep -rn "credential_type" apps/ engines/` 0 命中；`ruff check apps/ai_assistant/provider_registry.py` 通过
- [x] 2.2 `engine_adapter.py` 新增 `_validate_route_cfg()`：`device_control` 线路必须存在，planner/executor/verifier 的 `model_name` 非空、`api_key` 解密后非空；缺失抛中文错误（含角色与字段名）：验证 —— 新增单测「缺 planner」「model_name 为空」「api_key 为空」三种输入各自抛错且文案含角色名
- [x] 2.3 `engine_adapter.py` 校验 provider 合法性：不在合法集合内即抛错，文案含该 provider 与合法集合：验证 —— 新增单测「未知 provider → 报错」
- [x] 2.4 `engine_adapter.py` 设备串校验：`task.device_serial` 为空且在线设备为空时抛错（不再返回空串）：验证 —— 新增单测 monkeypatch `apps.device_pool.api.get_online_devices` 返回 `[]` 并断言抛错；另有在线设备时仍能取到 serial 的正向用例

## 3. A3 侧：模型工厂的 provider 分支

- [x] 3.1 `model.py` 新增模块级常量 `OPENAI_COMPATIBLE_PROVIDERS = {"openai", "anthropic", "gemini", "custom"}` 与 `SUPPORTED_PROVIDERS = {"deepseek", "dashscope"} | OPENAI_COMPATIBLE_PROVIDERS`；`create_model` 兜底分支在集合外时抛 `ConfigurationError`（复用 `engines.ai.registry.ConfigurationError`）：验证 —— 新增单测「未知 provider → ConfigurationError」；并确认 `import` 后 `python -c "import engines.ai.agentscope.model"` 无循环导入报错
- [x] 3.2 `model.py` dashscope 分支传递 `base_url`：验证 —— 新增单测以 monkeypatch 捕获 `DashScopeChatModel` 构造入参，断言 `base_url` 出现在 credential 或模型参数中；若实测该链路不支持自定义地址，则改为在 A2 对该 provider 明确拒绝并在 design.md 的 Open Questions 回写结论
- [x] 3.3 `model.py` 六个合法 provider 均可构造：验证 —— 单测对 `deepseek`（含 vision 与非 vision 两支）、`dashscope`、`openai`、`anthropic`、`gemini`、`custom` 逐一调用 `create_model` 均不抛错

## 4. 测试

- [x] 4.1 新增 `tests/graybox/unit/test_ai_engine_config.py`，逐条对应 spec 的 7 个 Scenario（装配期三条 + provider 四条）：验证 —— `pytest tests/graybox/unit/test_ai_engine_config.py -q` 全绿，且用例数与 Scenario 数一致
- [x] 4.2 一致性断言：`set(SUPPORTED_PROVIDERS) == set(VALID_PROVIDERS)`：验证 —— 测试通过；故意在 `PROVIDER_DEFAULTS` 增删一个 provider 时该测试应失败（手工试一次后还原）
- [x] 4.3 回归：验证 —— `pytest tests/graybox/unit -q` 相比改动前无新增失败（记录改动前基线条数）

## 5. 门禁与收尾

- [x] 5.1 后端门禁：验证 —— `python manage.py check` 无 issue；`ruff check` 与 `ruff format --check` 对改动路径通过
- [x] 5.2 范围核对：验证 —— `git diff --stat` 仅含 `apps/ai_assistant/provider_registry.py`、`apps/ai_assistant/engine_adapter.py`、`engines/ai/agentscope/model.py` 与新增测试文件
- [x] 5.3 文档回写：验证 —— design.md 的 Open Questions 结论与实施结果一致（dashscope base_url 走向、无设备任务口径）；若有变化同步更新
- [x] 5.4 报告勾稽：验证 —— `dev_docs/05-开发与测试/设计方案与报告/报告-AgentScope代码核对分析.md` §六 P0 三条标注为已完成，并附本次涉及的文件落点
