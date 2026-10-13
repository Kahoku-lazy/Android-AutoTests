## 1. `messaging/messages.py` 接收日志与费用

- [x] 1.1 新增 `reply_usage(result)` 与 `reply_cost(provider, model_name, result, *, created_at=None)`；新增 `_SHANGHAI` 与 `from ..billing import DeepSeekBilling`。验证：AST 断言两函数存在、`reply_cost` 体内出现 `_SHANGHAI`/`datetime.now`；运行期等价断言见 4.2。**验证结果**：通过 —— AST ⑫⑭⑮ 全 PASS（`reply_cost` 体内确有 `_SHANGHAI` 与 `datetime.now`，且走 `DeepSeekBilling().cost`）；4.2 实测高峰/非高峰两时刻的三项费用与 `DeepSeekBilling().cost` 直算**逐项相等**，`created_at` 缺省时等于"当前北京时间"的结果。
- [x] 1.2 新增 `print_result(result)` 与 `async render_reply_stream(agent, user_msg)`（把 `ConsoleRenderer`、`renderer.render(item)` 与 `renderer.last_msg` 兜底一起搬走）。验证：AST 断言两函数存在；`ConsoleRenderer` 只出现在 `messages.py`。**验证结果**：通过 —— AST ⑫⑬（`render_reply_stream` 为异步函数）⑰ PASS；AST ⑥ 确认 `role/base.py` 已不再引用 `ConsoleRenderer`。
- [x] 1.3 更新 `messages.py` 模块 docstring 与 `__all__`，并在 `messaging/__init__.py` 导出四个新函数。验证：导入冒烟。**验证结果**：通过 —— AST ⑯（`messages.py` 不 import role，无环）⑱（四个函数都在 `__init__.py` 的导入与 `__all__` 里）PASS；4.3 的 `from engines.agents.messaging import reply_usage, reply_cost, print_result, render_reply_stream` 成功。

## 2. `role/base.py` 瘦身

- [x] 2.1 删除 `usage` / `cost` / `_cost_calculator` / `print_result` / `scope_label` / `mark_scope` 与 `self._scope`。验证：六个名字与 `_scope` 在 `base.py` 0 命中。**验证结果**：通过 —— AST ③（六个名字逐个断言不在）④（`_scope` 0 命中）PASS。**附带删除（同属该特性，已单独说明）**：模块常量 `SCOPE_STANDALONE` —— 它只被 `scope_label` 使用（AST ⑤ 现为 0 命中）；已核实 `workflow/runner.py:19` 自带同名常量、不 import 本模块的，故删除无影响。
- [x] 2.2 `reply_detail` 改名为 `reply_stream`；`_reply_stream` 退化为「登记任务 + 调 `render_reply_stream`」；新增 `from ..messaging.messages import render_reply_stream`。验证：AST 断言 `BaseRole` 有 `reply`/`reply_stream`、无 `reply_detail`。**验证结果**：通过 —— AST ①（成员集合与预期**完全相等**，无多无少）②③⑨ PASS；4.3 运行期成员清单实测为 `interrupt / register_skills / reply / reply_stream / start` + 13 个私有方法，**不含** `reply_detail`。
- [x] 2.3 按 ruff `F401` 清理失效导入（`ConsoleRenderer`、`DeepSeekBilling`、`datetime`、`ZoneInfo` 与 `_SHANGHAI`、`Msg`），并把模块 docstring 改成与 `config.py` 对齐的格式。验证：`ruff check --no-cache` 通过；检索到 `python -m 调试路径: engines.agents.role.base`。**验证结果**：通过 —— AST ⑥⑦⑧（不再引用 `ConsoleRenderer` / `DeepSeekBilling` / `Msg`，`UserMsg` 保留）⑩⑪ PASS；`ruff check --no-cache` 三个文件 **`All checks passed!`**（连原先那条 `T201` 也随 `print_result` 一起搬走了）。

## 3. 静态复核（会话内可做）

- [x] 3.1 新增 AST 校验脚本 `temps/verify_slim.py`。验证：`python temps/verify_slim.py` 退出码 0 且 `RESULT: PASS`。**验证结果**：通过 —— **31 项全 PASS**。**过程如实记录（三轮都是我脚本自身的问题，非被测代码）**：① ⑯ 用字符串检索"`engines.agents.role`"，撞到我自己刚写进 `messages.py` docstring 的那句"不 import `engines.agents.role`"，改为 AST 判定导入模块；② ⑰ 引用了我在同一次编辑里删掉的 `messages_src` 变量，改为就地读取；③ ⑲ 最初按名字全文检索，把**新导出的** `print_result` 与 `runner.py` 自己的 `self._billing.cost(` 误判为残留，改为 AST 判定"是否有别处从 `role.base` / `role.config` 导入被删成员"。
- [x] 3.2 静态检查与格式归属。验证：`ruff check --no-cache` 不新增问题；格式化器"新增行"中不含我方标识符。**验证结果**：通过 —— 三个文件 `All checks passed!`（无 `F401` / `F821` / `I001` / `T201`）；对 `ruff format --diff` 只取 `+` 新增行过滤后无任何我方标识符。
- [x] 3.3 平台侧零改动：指纹比对。**验证结果**：通过 —— 前后均 `lines=93 sha256=93B153A423291C9501F1437D766F425B5140F87556D233DA87BEB66AFC2CA10C`。

## 4. 运行验证

- [x] 4.1 `python -m pytest tests/graybox/unit/test_executor_tool_groups.py -q`。验证：**15 passed**。**验证结果**：通过 —— `15 passed in 2.65s`。
- [x] 4.2 计费等价断言（`temps/check_slim_runtime.py`）。验证：脚本退出码 0。**验证结果**：通过 ——
  ```
  reply_usage: (1000, 500, 400)
  2026-10-13 10:00 deepseek-flash   got=(0.0012, 0.004, 0.0)      want 同值  equal=True
  2026-10-13 10:00 deepseek-v4-pro  got=(0.0054, 0.0135, 0.0001)  want 同值  equal=True
  2026-10-13 10:00 unknown-model    got=(0.0, 0.0, 0.0)           want 同值  equal=True
  2026-10-13 20:00 同上三项         全部 equal=True（数值为高峰的一半，说明时段生效）
  高峰/空闲两次结果是否不同: True
  created_at 缺省 vs 当前北京时间: (0.0012, 0.004, 0.0) == (0.0012, 0.004, 0.0)
  ```
  D4 那个坑（把 `None` 透传会静默按空闲时段少算一半）由最后一条断言守住。
  **过程如实记录**：首跑报 `ModuleNotFoundError: No module named 'engines'` —— 又是**我按路径执行脚本**导致 `sys.path[0]` 是 `temps/`，加 `PYTHONPATH=<仓库根>` 后通过，与被测代码无关。
- [x] 4.3 导入与成员冒烟。验证：`reply` / `reply_stream` / `register_skills` / `interrupt` 在，被删的六个不在。**验证结果**：通过 —— 输出成员清单为
  `['_basic_tool_group', '_context_config', '_interrupt_paused', '_react_config', '_reply', '_reply_stream', '_require_agent', '_resolve_skill_dir', '_running', '_skill_sources', '_source_dir', '_tool_group', '_user_msg', 'interrupt', 'register_skills', 'reply', 'reply_stream', 'start']`，断言全部通过。

<!-- 编写约定：apply 阶段按 `- [ ]` 解析进度。
     按根 AGENTS.md「禁止主动跑全量回归」，本次只做上列定向验证，不跑全量回归。
     本单有意**不**包含：动 register_skills / interrupt、拆 metrics.py、改计费口径、
     改 agents.py / workflow/** 的调用方式。

     【环境记录】本次 apply 期间会话为完全访问、审批提示关闭，故运行验证直接执行，未申请沙箱提权。 -->