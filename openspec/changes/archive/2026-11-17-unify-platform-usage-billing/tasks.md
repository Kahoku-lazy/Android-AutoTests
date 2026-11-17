## 1. 基数与公式

- [x] 1.1 在 `usage_ledger` 增加按模型名索引的基数表，含原币种、四项单价、高峰倍率、长上下文门槛与高档价、可选映射；写入试看基数：`deepseek-flash`、`deepseek-v4-pro`、`grok-4.6`、`grok-4.7`、`qwen3.5-omni-plus-realtime`，以及 `deepseek-v4.1-flash` → `deepseek-flash`。验证：单测能按模型名取到基数，未知模型返回空。
- [x] 1.2 把平台计价收成设计中的一条公式：按调用起点选高峰，按该笔输入选长上下文整笔高档，原币费用再乘汇率得到人民币 8 位。验证：`python -m pytest -c tests/pytest.ini tests/task/unit/test_usage_ledger.py -q` 增加并覆盖「缓存不重复加」「Grok 达到 20 万整笔高档」「无起点按空闲」「无基数为 unpriced」。

## 2. 唯一入账

- [x] 2.1 任务、助手运行、语音与文字会话在模型调用结束时调用 `usage_ledger.api.record_usage`，幂等键为「来源:执行 ID:轮次」，快照保存单价、倍率、原币种与汇率。验证：对应单测重复提交不新增行，且入账异常不向外抛出。
- [x] 2.2 删除任务收口对 `price_usage` 的直接调用；任务费用改为按 `execution_id` 汇总账本已计价行，未计价调用写入任务结果。验证：`tests/task/unit/test_assistant_sop.py` 中跨时段两笔之和等于任务费用，缺模型名的一笔不进合计。
- [x] 2.3 确认 `engines/` 不新增价目、不写库。验证：`python utils/gen_arch_stats.py --check-boundaries` 通过。

## 3. 仪表盘与清单

- [x] 3.1 仪表盘 `ai_usage`、近 7 日与今日逐小时改为按 `occurred_at` 聚合账本；费用排除未计价行，并返回未计价 token。验证：`python -m pytest -c tests/pytest.ini tests/dashboard/unit/test_dashboard_platform_usage.py tests/dashboard/unit/test_dashboard_today_usage.py -q` 通过，且不再依赖小时表造数。
- [x] 3.2 前端账单副标题改为「平台」，展示未计价 token，并提供人民币 / 美元切换；美元按接口返回的 6.7132 与日期换算，不发写请求。验证：`frontend` 对应 dashboard 测试通过，切换前后库存字段不变。
- [x] 3.3 任务清单费用列改为展示账本汇总，不再标注为仅 DeepSeek。验证：任务列表接口测试中该数值等于账本合计。

## 4. 归档与收口

- [x] 4.1 仪表盘把切换点之前的小时表合计标为归档，不并入平台费用。验证：接口同时返回账本累计与归档数，两者不相加。
- [x] 4.2 跑本变更相关门禁：`python manage.py check`、相关路径 `ruff check`、上述 pytest。验证：命令退出码为 0。
