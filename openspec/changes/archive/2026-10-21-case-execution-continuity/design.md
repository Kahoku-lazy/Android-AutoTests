## Context

任务 119 的证据链：配置 2 条用例 × 9 步；第 1 条第 2 步两次驳回后 `_drive_real` 直接 `return _case_failed(...)`，后续 16 步全部未执行；第 2 次尝试恰好用满 `max_iters=30` 被引擎提示收尾，handover 自述“尚未点击右上角 ✓”仍被当作一次尝试交给验收者。

现有实现的两个约束决定了方案：

1. 用例循环是串行的 `for case in cases:`，失败即 `return`，没有“逐条记账”的中间结构。
2. 执行者/验收者都是 `AgentLike`（`reply_stream(inputs, structured_schema, yield_final_msg)`），SOP 步骤从最终消息的 `structured_output` 里取 handover；这是在**我们自己的层**能拦到交卷的唯一位置。

## Goals / Non-Goals

**Goals:**

- 单条用例失败后继续跑后续用例，结果里能看出哪些通过了、哪些没通过。
- 执行者单步至少 60 轮工具预算，不再出现“只差一次点击就被预算逼着交卷”。
- 自述未完成的 handover 在同一轮尝试内被退回继续，不占用驳回次数。
- 提示词不再把设备连接加载圈当页面加载超时。

**Non-Goals:**

- 不改 `MAX_ATTEMPTS=2`（每条步骤仍是最多两次判决）。
- 不做用例级重跑或断点续跑。
- 不改验收判据、不改日志关键词表、不改用例 YAML。
- 不做“自动挑选用例顺序”或并发执行多条用例。

## Decisions

### 1. 用例循环改为“逐条记账”，失败不 return

`_drive_real` / `_drive_stub` 改为维护 `completed` 与 `failed` 两个清单：

- `phase == "completed"` → `completed.append(title)`，继续下一条；
- `phase == "cancelled"` → 立即 `return _cancelled(completed, failed)`，不再启动下一条；
- 其它（failed / running 被打断）→ `failed.append(title)`，继续下一条；
- 循环结束：`failed` 为空走 `_succeeded`，否则返回 `status="fail"`，`reason` 用「；」拼接全部失败标题。

结果字典新增 `failed` 键，`completed` 语义不变（仍是已完成的用例）。任务终态仍由 `RESULT_STATUS_MAP` 决定：`fail` 落到 `TaskStatus.FAILED`，不新增“部分成功”状态——报告口径（PASS/FAIL 二分）不因此分裂。

备选：
- **保留提前 return，只把剩余用例记为“未执行”**：报告仍然看不出到底哪里坏了，用户还是只能看到“只跑了两条”。
- **引入 `partial` 终态**：会让报告、趋势、通过率三处口径同时改，代价远大于收益。

### 2. 执行者预算 30 → 60，验收者不动

`_build_role` 增加 `max_iters` 参数，`_drive_real` 给执行者传 60、验收者传 30。`RoleSpecConfig` 的默认值仍是 30（`tests/graybox/unit/test_forced_handover_thinking.py` 锁的就是默认值），平台装配处显式覆盖，避免影响 `engines/agents/role/agents.py` 里的本地调试角色。

为什么是 60：119 的第 2 次尝试里约 12 轮是无效试错（加载圈 5 张截图、分段控件点错 4 次、xpath 3 次），30 轮被这些消耗完；60 轮给“试错 + 真正收尾”留出空间，同时仍是有限预算（宽限 5 轮由 agentscope 处理）。

### 3. 交卷拦截用 `AgentLike` 包装，不子类化 `SOPStep`

新增 `engines/agents/workflow/handover_guard.py` 的 `IncompleteHandoverGuard`：包住执行者 Agent，`reply_stream` 内部循环调用内层 agent，捕获最终消息：

- 最终消息的 `structured_output["handover"]` 命中未完成措辞且回灌次数 < 2 → 用 `UserMsg` 回灌“继续执行、不得现在交卷”，进入下一次内层 reply；
- 未命中，或已达上限 → 原样把最终消息 yield 给步骤。

为什么不用 `ToolMiddlewareBase` 拦 `GenerateStructuredOutput`：该工具由 agentscope 在每次 reply 内部 `add_tool` 重建（`_agent.py` 的 `remove_tool` + `add_tool`），外部拿不到注入点。
为什么不子类化 `SOPStep`：那要把 `state.phase`、`AWAITING` 停车、`record()` 的内部协议抄一遍，升级 agentscope 就会漂移；`AgentLike` 是公开协议，包装最薄。

事件归属：回灌仍在同一次 `SOPStep.reply_stream` 调用里，`_stamp_step` 读到的是同一个步骤序号与尝试序号，报告不会把它拆成两次尝试。

### 4. 措辞表而不是让模型自评

`INCOMPLETE_MARKERS = ("未完成", "尚未", "还没", "未点击", "未执行", "部分完成", "请下一步", "下一步立即", "下一步执行")`。

`未达成` 刻意不在表里：验收判据本身用“达成/未达成”表述，执行者按判据逐条汇报时会大量出现该词，纳入会造成稳定误判。

误判代价可控：误判只多一次“继续”的 reply（且被驳回次数不变），不会改变判定；漏判代价是回到今天的行为（验收者驳回）。因此取“宁可多拦一次”。

### 5. 提示词只改加载语义与 handover 措辞

`executor_prompt.py` 把“加载超过 10s 终止并输出 FAIL”限定为**页面整体加载**；新增一条：长按/点击卡片后卡片上的小加载圈是设备连接/同步，等待其消失（最长 60s），期间不要重复长按。并在 handover 段写明不得出现“尚未/未完成/请下一步”。

## 模块防火墙自检

- 改动都在 `engines/agents/workflow/` 与 `engines/agents/prompts/`，不跨 app import，不碰 Django。
- `task_runner.py` 只把 `failed` 清单透传进既有结果载荷，不直写 ORM。
- 报告页不改：用例格子仍由事件还原，失败用例之后的用例现在有真实事件，自然显示为 PASS/FAIL 而不是“未执行”。

## Risks / Trade-offs

- [失败任务耗时变长] → 最多多跑“剩余用例 × 单步预算”的时间；用户可随时取消，取消即刻生效。
- [措辞表误判多烧一轮] → 上限 2 次，且不占驳回次数；只在 handover 文本上做一次子串匹配，成本可忽略。
- [单步可能跑 3 × 60 轮] → 极端情况单步耗时上升；这是“宁可多跑也不交半成品”的显式取舍，且取消路径仍有效。
- [报告里失败用例之后出现真实执行记录，历史对比口径变化] → 这是修复目标本身；历史任务不受影响（数据未回填）。

## Migration Plan

1. 纯代码改动，无数据库迁移、无接口契约变化。
2. 发布即生效，下一条任务即可看到“单条失败不终止整批”。
3. 回滚：还原 `platform_run.py` 的用例循环与 `_build_role` 参数即可；`failed` 键对旧读取方是新增字段，忽略即可。

## Open Questions

无。
