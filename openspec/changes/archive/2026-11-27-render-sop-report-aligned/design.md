## Context

一次 SOP 运行已经在同一条管线上产出了三样东西：AgentScope 事件流（`reply_stream`）、观测记录（`ObservationMiddleware` 七个 hook）、过程日志（`AgentEventRecorder`）。单角色执行器在这三样之上又加了「对齐记录 + 原始事件流 + 五页签报告」，SOP 没跟上。

现状差异（全部为代码事实）：

| 维度 | 单角色执行器 `session.run_turn` | SOP `run_sop` / `run_bound_sop` |
| --- | --- | --- |
| 观测中间件 | `ObservationMiddleware(capture_messages=True)` | `ObservationMiddleware()`，默认不采消息 |
| 对齐记录 | `AlignedRun` → `.aligned.json` | 无 |
| 原始事件流 | `RawEventDump` → `.raw.jsonl` | 无 |
| 报告 | `AlignedReportRenderer`（五页签） | `HtmlReportRenderer`（四段式，不渲染观测） |
| 设备校验 | `require_online` + `lock_serial` 全程持锁 | 只把 serial 拼进任务文本 |
| 运行参数 | `max_image_num=2` / `tool_result_limit=20000` / `max_iters=20` | 框架默认 5 / 50000 / 50 |

`logs/agents/backend_bridge` 实测：25 次 `sop_bound` 运行，12 份 HTML、0 份 aligned；最大 HTML 20.7 MB（图像与工具结果都按默认上限保留）。旧渲染器里 `observations` 零引用，所以已采集的系统提示与压缩判定在报告里完全不可见。

SOP 相比单角色多出的信息，是新报告必须承载的：步骤事件（`CustomEvent` 的 `SOP_STEP_STARTED` / `SOP_STEP_ENDED`，带 `step` 与 `attempt`）、每步验收结论、两个角色（执行者 / 验收者）交替回复。

## Goals / Non-Goals

**Goals**

1. SOP 与单角色产出同口径的四类文件，报告共用一套五页签渲染。
2. 阶段视图按 SOP 步骤切分，每步两个角色各自成块，带验证结论与尝试次数。
3. SOP 补齐设备前置校验与全程独占，参数与单角色一致。
4. 单角色、`goal`、`team` 三条既有路径行为零变化。

**Non-Goals**

1. 不给 `goal` / `team` 接对齐记录（它们仍用 `HtmlReportRenderer`）。
2. 不改报告视觉契约与前端报告查看器。
3. 不改任务字段、账本口径、接口契约。
4. 不合并两个角色的上下文（各跑各的 agent，这是 SOP 本体语义）。

## Decisions

**D1 运行器只透出事件与观测，不自己决定产物。** `run_sop` 增加 `on_event` / `on_observation` 两个可选回调，调用方（`run_bound_sop`）在回调里同时喂 `RawEventDump` 与 `AlignedRun`。理由：`ae_harness` 的 workflow 层不该知道平台目录结构与文件命名。备选（在 `run_sop` 里直接建 aligned）被否：会把平台命名规则压进原语层。

**D2 报告渲染由调用方接管。** `run_sop` 增加 `render_report: bool = True`；`run_bound_sop` 传 `False`，自己在步骤结论算完之后渲染。理由：步骤结论（`passed` / `attempts` / `message`）只有 `run_sop` 返回后才知道，而报告需要它；若在 `run_sop` 内部渲染就拿不到。备选（先渲染再补步骤）被否：等于同一份 HTML 写两次。

**D3 对齐记录只做「加字段」的向后兼容扩展。** schema 仍是 `agentscope.run/1`，新增三个可选键：`steps`（步骤结论）、`run.roles`（角色清单：名字 / 角色 / 模型 / 密钥环境变量）、`input.roles`（每角色系统提示与工具清单）；`replies[]` 增加可选 `role`。缺这些键时渲染器走现有按轮逻辑，单角色记录行为不变。理由：改 schema 版本会打断已产出的历史记录重渲染。

**D4 阶段切分优先用步骤事件，其次按轮。** 有 `steps` 段时：`CustomEvent` 的 `SOP_STEP_STARTED` / `SOP_STEP_ENDED` 给出步序，事件里的 `reply_id` 把回复挂到步上；每步内部再按 `reasoning` 起点分轮。无 `steps` 段时退回现状（按 reply_id 分组 + 按轮）。理由：步骤边界是运行期事实，不能从文本猜。

**D5 两个角色共用同一个观测中间件实例。** `build_bound_roles` 现在是「执行者建 watcher，验收者复用同一 watcher」，这条保持不变，只把 `capture_messages=True` 传进去。理由：一个 run 一份观测流，报告才能按 reply_id 排成时间序；两个实例会产生两条互不知情的流。

**D6 设备校验放在 `run_bound_sop` 的最前面，锁包住整个 run。** 复用 `session.require_online`（同一条错误文案与判定口径：空串、未连接、状态非 `device` 三种拒绝），`lock_serial` / `unlock_serial` 用 `try/finally` 包住 `run_sop`。理由：平台提交流程已强制选设备（`views._submit_assistant_sop` 对空 serial 直接报「请选择设备」），所以新增校验对可达入口没有回退，只是把「连不上」从模型跑到一半失败提前到开跑前。

**D7 运行参数抽成共享常量。** 把 `_MAX_IMAGE_NUM` / `_TOOL_RESULT_LIMIT` / `_MAX_ITERS` 从 `session.py` 提到可复用位置（`engines/backend_bridge/agents/run_params.py`），`session.open_session` 与 `build_bound_roles` 都引用同一组值。理由：两处各写一份必然漂移，本次问题的直接来源就是一处写了一处没写。

## 与既有 spec 的冲突与处置

`openspec/specs/backend-bridge-sop/spec.md` 的「SOP 只装配不自创」写着「本变更 MUST NOT 修改 `engines/ae_harness` 下的任何代码」——那是上一轮（SOP 初次接入）的约束，目的是防止在 SOP 层另写编排。本轮必须改 `ae_harness`（`run_sop` 出口 + 渲染器），因此该条款以 delta 的 MODIFIED 形式收窄为「不得另写编排、不得自建采集与渲染」，并保留「复用 `load_spec` / `run_sop`」的原意。

处置依据：报告与采集的契约属于原语层，SOP 侧只是接线；把契约留在 SOP 层反而会造出第二套采集。

## 数据结构增量（对齐记录）

```jsonc
{
  "schema": "agentscope.run/1",
  "run":   { "role": "sop_bound", "model": "...", "serial": "...",
             "roles": [ {"name": "...", "role": "executor|verifier", "model": "...", "api_key_env": "..."} ] },
  "input": { "system_prompt": "（单角色兼容位）", "tool_schemas": [],
             "user_message": "...",
             "roles": [ {"name": "...", "role": "executor|verifier",
                         "system_prompt": "...", "tool_schemas": []} ] },
  "replies": [ { "reply_id": "...", "agent": "...", "role": "executor|verifier", "msg": { } } ],
  "observations": [ ],
  "steps": [ { "index": 1, "subject": "...", "description": "...",
               "passed": true, "attempts": 1, "message": "...", "expected": "...",
               "reply_ids": ["..."] } ],
  "summary": { }, "event_count": 0, "events": [ ]
}
```

`steps[].reply_ids` 由渲染期从事件推导后回填，用于把回复挂到步上；不写进记录也能推导，这里写进记录是为了让「单文件复现」不依赖重放事件。

## Risks / Trade-offs

1. **SOP 报告体量仍会偏大**：两角色、多步、每步多轮，事件数必然是单角色的数倍。缓解：图像上限降到 2、工具结果上限降到 20000，delta 事件在事件流页签默认折叠。若仍过大，下一步考虑步骤级懒加载（本次不做）。
2. **`capture_messages=True` 让过程日志与观测都变大**：单角色实测 145 条观测、日志数百 KB 级，SOP 预计数 MB。可接受，且这是用户明确要的「全量信息」。
3. **两个角色共用一个 watcher 的 `_rounds` 计数会累加**：轮次编号跨角色连续递增，报告里会出现「第 7 轮」属于验收者的情况。缓解：状态里带 agent 名，步骤卡按角色分组渲染；轮次仅作序号展示，不作为语义。
4. **`append_event` 对 `CustomEvent` 的折叠**：官方 `Msg.append_event` 不认步骤事件，会落进 `unfolded` 兜底。缓解：步骤事件已在渲染期单独消费，`unfolded` 只影响该条回复的块完整性文案。
5. **设备锁的持有时长**变长（整个 SOP 可能跑几分钟）。缓解：平台已有取消路径（`cancel_controls` + 取消释放定时器），锁在 `finally` 释放。

## Migration Plan

1. 先加共享参数常量与 `run_sop` 的两个出口 + `render_report` 开关（默认行为不变）。
2. 再改 `bound_roles`（`capture_messages=True`）与 `bound_sop`（设备校验、锁、aligned/raw、渲染接管）。
3. 最后扩展 `AlignedRun` 与 `AlignedReportRenderer`（`steps` / `roles` / 按步阶段），单角色记录回归确认无变化。
4. 历史 SOP 的 `.html` 不迁移重渲染；旧记录仍能被新渲染器打开（缺 `steps` 段走按轮逻辑）。

## Open Questions

无。设备契约的口径沿用「平台已强制选设备」，不做额外确认；报告是否保留旧四段式作为兜底，结论是不保留（`goal` / `team` 已经覆盖旧渲染器的使用）。
