## 1. 八位费用

- [x] 1.1 改 `engines/agents/messaging/billing.py`：`cost()` 用 `Decimal` 计算后量化到 `0.00000001`（`ROUND_HALF_UP`），返回三项 `Decimal`；增加取价快照（模型、三项单价、倍率、是否高峰）。价目、高峰钟点与法定节假日规则不动。验证：新增 `tests/engines/agents/test_billing_eight_decimals.py`，覆盖规格场景（12345 → 0.01234500、4670 → 0.00467000、4630 → 0.00463000、4650 → 0.00465000、2560/972/2560 → 0 / 0.00388800 / 0.00005120、1000 全命中 → 缓存 0.00002000、未登记模型三项为 0、缓存命中超过输入时输入费用为 0），运行 `python -m pytest tests/engines/agents/test_billing_eight_decimals.py -q` 通过。

## 2. 记录与接收方

- [x] 2.1 新增 `engines/agents/messaging/record.py`：结构化记录含事件类型、阶段、块类型、是否增量、角色名、角色种类、模型、payload、起止时刻、三项费用与取价快照；无 I/O。验证：同文件的类型可被导入，且模块不 import `apps`（`rg "apps" engines/agents/messaging/record.py` 无匹配）。
- [x] 2.2 新增 `engines/agents/event_sink.py`：接收方协议、绑定与取出、默认空实现（丢弃记录与图片）。验证：未绑定时取出的接收方接受一条记录与一段 base64 且不抛错；`rg "import apps" engines/agents/event_sink.py` 无匹配。

## 3. 事件折叠

- [x] 3.1 新增 `engines/agents/messaging/fold.py`：`step` 按规格决定落与不落、拼接文本与 base64、继承角色、生成既有措辞的日志行。`ModelCallEnd` 只调用一次 `cost()`，日志行与记录使用同一组 8 位费用。验证：新增 `tests/engines/agents/test_event_fold.py`，用假事件覆盖文本增量合并、工具入参序号 0/1、工具返回状态与文本、执行者到验收者的角色切换、`CustomEvent` 无输出、图片 base64 不出现在日志行但出现在结束记录、模型名从开始带到结束、1000 token 全命中的费用在日志行与记录中都是 0.00002000 元。运行 `python -m pytest tests/engines/agents/test_event_fold.py -q` 通过。

## 4. 编排

- [x] 4.1 把 `AgentEventsShow.show` 收成：调用折叠、写文本日志、再把记录与图片交给当前接收方。签名保持 `(event, buf, models)`。接收方抛错时写警告并返回，不向外抛。`ReplyStreamParser` 留在 `messages.py`。验证：`tests/engines/agents/test_event_fold.py` 增加一条「接收方抛错时日志行已经写出且异常不外抛」；`rg "show\\(event, buf, models\\)" engines/agents/workflow/ui_auto_workflow.py` 仍有调用。
- [x] 4.2 更新 `engines/agents/AGENTS.md` 的 `messaging` 目录说明，列入记录、折叠与接收方，并写明折叠不写库。验证：该节能读到 `fold.py`、`record.py`、`event_sink.py`。

## 5. 收口

- [x] 5.1 对改动路径跑 `ruff check engines/agents/messaging engines/agents/event_sink.py tests/engines/agents/test_billing_eight_decimals.py tests/engines/agents/test_event_fold.py` 与上述两个 pytest 文件。验证：ruff 与 pytest 均通过。不跑全量回归。
