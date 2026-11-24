# Tasks: fix-eval-usage-billing

## 1. 评测真实 token 入账

- [ ] 1.1 live_runner._ask_model 改用 AgentEventRecorder 累积 record.usages，逐次映射真实 model/tokens/provider（context 密钥归属）/occurred_at，删除硬编码 0 usage；docstring 同步。验证：新增 unit 用例（fake agent reply_stream 发用量事件）断言 eval 账行 token 非 0、model 为逐次模型；`python -m pytest -c tests/pytest.ini tests/ai_assistant/unit -q` 通过
- [ ] 1.2 eval_billing.record_eval_usages 增 cache_input_tokens 透传；provider 由供给端携带（deepseek 兜底仅作最后防线并注释）。验证：unit 用例断言 cache token 落账、幂等不翻倍；同上套件通过

## 2. 任务入账模型归属（A4）

- [ ] 2.1 前置检查：retire-backend-dead-code 已合并。usage_ledger/api.py:111 改 `model=str(item.get("model") or "") or model`，docstring 同步。验证：新增双角色双模型 unit 用例——账本各行保留各自模型、按各自价目计费、与任务费用合计一致；逐次缺失时 run 级兜底用例；`python -m pytest -c tests/pytest.ini tests/task/unit/test_usage_ledger.py -q` 通过

## 3. pricing.json 死条目清理

- [ ] 3.1 删 pricing.json 4 个被 RATES 遮蔽的 deepseek 条目（先 grep 确认 lookup_rate 覆盖同名模型）。验证：新增 recalc 回归用例——含 deepseek 历史账行的 fixture 在删条目前后 recalculate_usage_costs 结果恒等；`python -m pytest -c tests/pytest.ini tests/task/unit/test_usage_ledger.py -q` 通过；语音条目与 rates.py 数值零改动（diff 核对）

## 4. 关单门禁

- [ ] 4.1 `python run.py check` 退出码 0；`python utils/gen_arch_stats.py --check-boundaries` 零违规；ruff check/format --check 相关路径通过；逐文件暂存、fix(usage_ledger)/fix(ai_assistant) 分提交，推特性分支提 PR，确认 python 与 frontend 两个 CI job 全绿后合并；发布说明注明「assistant_eval 来源费用从 0 恢复为真实值」