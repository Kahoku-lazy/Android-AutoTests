## 1. 搬迁计费模块

- [x] 1.1 将 `engines/agents/billing.py` 原样移到 `engines/agents/messaging/billing.py` 并删除旧文件。`messages.py` 改为 `from .billing import DeepSeekBilling`，`workflow/runner.py` 改为从 `..messaging.billing` 导入。不在 `engines.agents.billing` 或 `messaging/__init__.py` 再导出。验证：`from engines.agents.messaging.billing import DeepSeekBilling` 成功；`import engines.agents.billing` 失败；仓库内 `engines.agents.billing` 与 `from ..billing` 无剩余引用。

## 2. 两个解析类

- [x] 2.1 在 `messages.py` 增加共用整数收口，以及 `ReplyParser.tokens(result) -> tuple[int, int, int]`、`ReplyStreamParser.tokens(event) -> tuple[int, int, int] | None`。最终消息读 `usage` 的输入、输出、缓存命中，缺用量时返回 `(0, 0, 0)`。流式类只在类名为 `ModelCallEndEvent` 时返回三元组（字段缺失或为 0 时为 `(0, 0, 0)`），其它事件返回 `None`。不读取 `cache_creation_input_tokens`。`reply_usage` 改为走 `ReplyParser`；`reply_cost` 仍先判断 deepseek，再把三元组与调用时刻交给 `DeepSeekBilling.cost`，`created_at` 缺省时取当前北京时间。更新该模块 docstring，列出这两个类。验证：新增 `tests/graybox/unit/test_agent_reply_usage.py`，用假消息与假事件覆盖「同等数字得到同一三元组」「最终消息缺用量为全 0」「文本增量返回 None」「同一轮两次结束事件各自成组、不合并为 30/3/0」「三元组交给 `DeepSeekBilling.cost` 与直接传三个整数逐项相等」。运行 `python -m pytest tests/graybox/unit/test_agent_reply_usage.py -q`。

## 3. 接到现有调用方

- [x] 3.1 `SopRunner._record_call` 改为使用 `ReplyStreamParser.tokens(event)`。结果为 `None` 时不累计。非空时按该事件的 `created_at` 与当次模型名调用 `cost`，再累加用量与费用。验证：在 `test_agent_reply_usage.py` 中用未走 `SOPEngine` 的运行器实例连续记两笔（北京时间 2026-10-08 10:00 高峰、2026-10-10 10:00 空闲，模型 `deepseek-flash`），断言用量分笔相加，费用合计等于两笔 `cost` 之和；再喂一条非结束事件，调用次数不增加。

- [x] 3.2 `DialogueLog._on_ModelCallEndEvent` 改为用 `ReplyStreamParser.tokens(event)` 填助手块的 `input` / `output` / `cache_hit`。费用仍使用调用方传入的 `cost`。验证：`python -m pytest tests/graybox/unit/test_agent_dialogue_log.py -q` 通过，助手块 token 字段与改前断言一致。

## 4. 导出与目录说明

- [x] 4.1 `messaging/__init__.py` 导出 `ReplyParser` 与 `ReplyStreamParser`，保留既有函数导出。`engines/agents/AGNETS.md` 把计费说明从根目录文件清单改到 `messaging` 目录，写明模块为 `messaging/billing.py`。验证：`from engines.agents.messaging import ReplyParser, ReplyStreamParser` 成功；`AGNETS.md` 根目录清单不再把 `billing.py` 列为根模块；对改动过的 Python 文件运行 `ruff check`。
