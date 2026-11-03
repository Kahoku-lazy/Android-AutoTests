## 1. 移除单步 token 预算

- [x] 1.1 删除 `engines/agents/middleware/budget.py`，并从 `middleware/assembly.py` 移除预算的导入、装配项与顺序说明——验证：`python -c "from engines.agents.middleware import build_agent_middlewares; print([type(m).__name__ for m in build_agent_middlewares()])"` 只输出 `['ModelRetryMiddleware']`
- [x] 1.2 从 `engines/agents/middleware/__init__.py` 删除 `build_budget_middleware` 导出——验证：`python -c "import engines.agents.middleware as m; print(hasattr(m, 'build_budget_middleware'))"` 输出 `False`
- [x] 1.3 删除 `.env.example` 中 `AGENT_REPLY_TOKEN_BUDGET` / `AGENT_REPLY_INPUT_WEIGHT` / `AGENT_REPLY_OUTPUT_WEIGHT` 三行——验证：`Select-String -Path .env.example -Pattern 'AGENT_REPLY_'` 无匹配

## 2. 轮次作为唯一单步上限

- [x] 2.1 保持 `agent_config.yaml` 中执行者 `max_iters: 60` / `structured_output_grace_iters: 5` 不变（不改数值、不新增开关）——验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_case_run_continuity.py -q` 通过（该用例已断言执行者 60、验收者 30）
- [x] 2.2 在 `middleware/assembly.py` 的模块 docstring 与装配函数说明里，把「单步收敛由轮次上限决定」写清楚，避免后来者重新加回 token 护栏——验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_agent_middleware_assembly.py -q` 通过，且装配结果里不含任何按 token 计数的中间件

## 3. 精简 handover 契约

- [x] 3.1 改写 `engines/agents/config/data/prompts/UI_EXECUTOR_PROMPT.md` 的 handover 段为两块：① 本步做了什么（点击 / 长按 / 拖动的 `action_time` 原文，按序逐条，含输入与开关改动）；② 最终结果（「达成」或「未达成」+ 一句话实况）；同步调整第 11 条与第 13 条，使「未达成」成为如实交卷的合法口径——验证：`python -c "from engines.agents.role_sys_prompts import EXECUTOR_PROMPT; assert '最终结果' in EXECUTOR_PROMPT and '达成' in EXECUTOR_PROMPT"` 通过
- [x] 3.2 删除与 `UI_EXECUTOR_PROMPT.md` / `UI_VERIFIER_PROMPT.md` 字节完全相同、全仓无引用的副本 `EXECUTOR_PROMPTS_MD.md` / `VERIFIER_PROMPTS_MD.md`——验证：`Select-String -Path . -Pattern 'EXECUTOR_PROMPTS_MD|VERIFIER_PROMPTS_MD' -Recurse` 无匹配，且 `python -c "from engines.agents.role_sys_prompts import EXECUTOR_PROMPT, VERIFIER_PROMPT; print(len(EXECUTOR_PROMPT), len(VERIFIER_PROMPT))"` 正常输出
- [x] 3.3 更新 `tests/graybox/unit/test_role_prompt_guardrails.py`：断言两块交卷结构、`action_time` 原文要求与「未达成」口径；删除与新口径冲突的旧断言——验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_role_prompt_guardrails.py -q` 通过

## 4. 测试与回归

- [x] 4.1 更新 `tests/graybox/unit/test_agent_middleware_assembly.py`：默认集合改为只剩重试、顺序断言去掉预算、删除三个预算开关用例、清理 `_ENV_NAMES` 里的预算变量——验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_agent_middleware_assembly.py -q` 通过
- [x] 4.2 更新 `tests/graybox/unit/test_model_retry_middleware.py` 中依赖 `AGENT_REPLY_TOKEN_BUDGET=0` 的用例，改为不设该变量也能得到空的重试链——验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_model_retry_middleware.py -q` 通过
- [x] 4.3 复核 handover 守卫对「未达成」的放行仍然成立（不改守卫代码）——验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit/test_handover_guard.py -q` 通过

## 5. 门禁与冒烟

- [ ] 5.1 单元套件全绿——验证：`python -m pytest -c tests/pytest.ini tests/graybox/unit -q` 通过
- [x] 5.2 engines 注释与风格自检无本次新增问题——验证：`.agents/skills/engines-docstring-check` 下 `python -m scripts.docstrings check`；`.agents/skills/engines-agents-style-check` 下 `python -m scripts.check_engines_agents_style`
- [ ] 5.3 仓库门禁通过——验证：`python run.py check`
- [x] 5.4 有设备时跑一条短用例（如「启动 govee 应用并进入 H6810 详情页」），确认执行者正常交出 handover、该步产生验收判决且不再出现「没有结构化输出」的判负——验证：任务事件里该步有 `GenerateStructuredOutput` 调用与 `verdict passed` 记录
