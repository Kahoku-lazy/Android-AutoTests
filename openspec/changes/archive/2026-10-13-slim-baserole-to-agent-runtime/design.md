## Context

见 `proposal.md` - Why。实测现状（`engines/agents/role/base.py` 共 301 行）：

- 有调用方：`start()`（`agents.py:189-190`）、`register_skills()`（`executor.py:29`、测试 4 处）、`agent` 字段（`workflow/steps.py:195` 的 `_require_agent`）。
- 0 调用：`reply`、`reply_detail`、`print_result`、`usage`、`cost`、`_cost_calculator`、`interrupt`、`scope_label`、`mark_scope`。
- `self._scope` 只在 `__init__:43` 与 `mark_scope:66` 被写，**没有任何读取点**。
- `messages.py` 现为纯函数风格（3 个工具输出解析函数），文件头自述"只依赖标准库与 AgentScope 消息类型，不 import `engines.agents.role`"。
- `billing.py` 的 `DeepSeekBilling.cost(model_name, in, out, hit, created_at=None)`：`created_at=None` 时按**空闲时段**计价；`BaseRole.cost` 传的是 `datetime.now(_SHANGHAI)`，因此**高峰时段会生效**。

## Goals / Non-Goals

- Goals：`BaseRole` 只剩「创建智能体（`start` + 装配期辅助）」+「两个运行方法（`reply` / `reply_stream`）」+ 运行控制（`interrupt`）；日志上屏与用量费用归 `messaging` 层；`base.py` 的 docstring 与 `config.py` 格式对齐。
- Non-Goals：
  - 不动 `register_skills`（在用）与 `interrupt`（运行控制）。
  - 不拆 `metrics.py`（用户指定放 `messages.py`）。
  - 不改计费口径、不改高峰时段规则、不改 `DeepSeekBilling`。
  - 不改 `agents.py` / `workflow/**` / `executor.py` 的调用方式。

## Decisions

**D1：`reply_detail` 改名为 `reply_stream`，仍是同步方法（用户已选）。**
与 `reply` 成对形成"两种运行方法"。全仓 0 调用，改名零破坏面。`_reply_stream`（异步实现）保留内部名，`reply_stream` 内部 `asyncio.run` 调它 —— 与 `reply` → `_reply` 的现有结构对称。

**D2：`register_skills` 与 `interrupt` 留在 `BaseRole`（用户已选）。**
`register_skills` 是装配期钩子且在 `executor.py` + 4 处测试里被调用；`interrupt` 是运行控制，放 `messaging` 属层错。

**D3：删除 `scope_label` / `mark_scope` / `self._scope`（用户已选）。**
过程日志退役后它们只写不读。搬去 `messages.py` 只是把死代码换个地方躺，还会污染新家的导出面 —— 故删除而非搬运。

**D4：费用做成两个纯函数，并**必须**保住 `created_at` 默认值。**
```python
def reply_usage(result) -> tuple[int, int, int]: ...
def reply_cost(provider, model_name, result, *, created_at=None) -> tuple[float, float, float]: ...
```
- `reply_cost` 内部：provider 经 `str(provider or "").strip().lower() == "deepseek"` 判定，否则返回 `(0.0, 0.0, 0.0)`（与 `_cost_calculator` 的现有语义一致）；用量取自 `reply_usage`。
- `created_at=None` 时**函数内部补 `datetime.now(_SHANGHAI)`**，与 `BaseRole.cost` 现在的行为一致。
  ⚠️ 这是本单最容易出错的地方：若把 `None` 直接透传给 `DeepSeekBilling.cost`，高峰时段（周一至周五 9-12 / 14-18，节假日除外）会被算成空闲时段，**静默少算一半费用**。任务里为此加一条等价性断言。

**D5：上屏抽成 `async def render_reply_stream(agent, user_msg) -> Msg | None`。**
把 `ConsoleRenderer(verbosity="debug")`、事件循环里的 `renderer.render(item)`、以及结尾的 `renderer.last_msg` 兜底一起搬过去。`BaseRole._reply_stream` 退化为「`async with self._running(): return await render_reply_stream(...)`」—— 任务登记（供 `interrupt` 取消）必须留在角色侧，因为它依赖 `self._reply_task` / `self._loop`。

**D6：`messages.py` 的自述与依赖同步更新。**
新增 `from ..billing import DeepSeekBilling` 与 `from agentscope.console import ConsoleRenderer`；文件头那句"只依赖标准库与 AgentScope 消息类型"要改，并保留"不 import `engines.agents.role`"这一条（本次仍成立，且是避免环的关键）。

**D7：`base.py` 的模块 docstring 改用 `config.py` 的格式（用户已选）。**
```
""" 
python -m 调试路径: engines.agents.role.base

本模块的业务功能如下：
1. BaseRole: 角色基类, 用模型配置与角色配置创建智能体, 并提供 reply 与 reply_stream 两种运行方法。
"""
```
按用户"格式对齐"的要求逐项对齐，包括 `config.py` 里 `"""` 后那个尾随空格与空行结构（会在报告里点明，若不要可一句话去掉）。

**D8：失效导入按 ruff `F401` 判定，不凭肉眼删。**
预计失效：`ConsoleRenderer`、`DeepSeekBilling`、`datetime`、`ZoneInfo`（连带 `_SHANGHAI` 常量）、`Msg`（若无其它用途）。

**D9：以 `skip_specs: true` 退出 specs 阶段。**
删的与改名的成员在脚手架内 0 调用；运行链路（`agents.py` → SOP runner → `ExecutorRole.start()`）行为不变。

## Risks / Trade-offs

- [计费时段语义被静默改变] → D4 明确 `created_at` 兜底，并加运行期等价断言：`reply_cost("deepseek", m, r, created_at=t)` 必须等于 `DeepSeekBilling().cost(m, in, out, hit, t)`；另加一条 `created_at=None` 时必须等于传"当前北京时间"的结果。
- [`messaging` 反向依赖 `role` 造成循环] → 只新增 `..billing`；`billing.py` 不 import role（已核实），且 `messages.py` 保持不 import role。
- [删 `mark_scope` 撞到测试] → 已核实 `test_agent_event_stream.py:177` 用的是平台侧 `engines.ai.agents.AgentRole`；任务里再检索一次确认。
- [`Msg` / `ConsoleRenderer` 变成未使用导入] → 以 ruff `F401` 判定（D8）。
- [改名 `reply_detail` → `reply_stream` 与框架方法同名造成混淆] → 两者层级不同：角色侧是**同步**入口，框架侧 `agent.reply_stream` 是**异步生成器**；角色侧包装它。文档里写明这一点。

## Migration Plan

无部署动作：`role/base.py` 不在平台运行链路的 import 图上（`apps/` 只引同包 `tools/tool_serial.py`）。
回退策略：把四个函数搬回 `BaseRole` 并恢复原方法名（`cost` / `usage` / `print_result` / `reply_detail`），`scope_label` / `mark_scope` / `_scope` 按需恢复。

## Open Questions

- `messages.py` 未来要不要拆出 `metrics.py`（用量与费用）—— 本次按用户指定不拆；若日后再长，可另立一单。
- `BaseRole.reply` / `reply_stream` 目前全仓 0 调用（脚手架实际走 SOP runner）—— 是否保留这两个公开入口由用户掌握，本次按"保留"处理。
