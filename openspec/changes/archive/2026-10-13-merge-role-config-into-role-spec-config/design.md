## Context

见 `proposal.md` - Why。实测现状：

- `RoleConfig`（`engines/agents/role/base.py:34-63`）：手写类，12 个形参（3 个必填 + 9 个带默认值），逐项 `self.x = x`。
- `RoleSpecConfig`（`engines/agents/role/config.py:51-70`）：`@dataclass(frozen=True)`，6 个字段，**无任何实例化点**。
- `RoleConfig` 的消费点全部在 `base.py`，且**只读**：`:72`（stream/vision）、`:139-144`（name/system_prompt/toolkit）、`:241-243`（ReAct 三项）、`:248-251`（上下文四项）。全仓**没有**任何 `role.<字段> = …` 的重新赋值；`:120` 与 `:270` 是往 `role.toolkit.tool_groups` 里 append，改的是 Toolkit **内部**，不是给 `role.toolkit` 重新绑定。
- 构造点 3 处：`role/executor.py:22`、`role/executor.py:42`、`tests/graybox/unit/test_executor_tool_groups.py:59`。
- `Toolkit` 在 `base.py` 的用法只有 `:23`（导入）与 `:41`（`RoleConfig` 的注解）；另有 `:283` 是 docstring 里提到 "Toolkit" 的文字，不构成代码引用。

## Goals / Non-Goals

- Goals：一个包内只有一个"角色配置"类，名字是 `RoleSpecConfig`、宿主是 `role/config.py`；所有调用方从 `config` 取；行为零变化。
- Non-Goals：
  - 不改字段名（保留 `name`，不改成 `role`）。
  - 不改任何默认值。
  - 不引入平台侧"`tool_names` → 工具包"的解析层（那是一次真正的行为重构）。
  - 不动 `prompt_config.py` 里重复的 `ModelConfig` / `DeviceExecutionConfig`。
  - 不动 `config.py` 末尾的 `__main__` 调试块。

## Decisions

**D1：`RoleSpecConfig` 采用 `@dataclass(frozen=True)`（用户已选）。**
依据：与同文件的 `ModelConfig` 同风格；已核实全仓无 `role.<字段> = …` 的重新赋值，所以冻结不会撞到任何现有写入；Toolkit 内部的可变操作（`tool_groups.append`）不受 frozen 限制 —— frozen 只拦 `role.toolkit = …` 这种重新绑定。
代价（如实记录）：dataclass 会自动生成 `__hash__`，而字段里含 `Toolkit`。若将来有人把实例放进 `set` 或当 dict key，且 `Toolkit` 不可 hash，就会在运行期报 `TypeError` —— 与 `RoleSpec` 当初那个 `dict` 字段的隐患同类。本次不处理，登记在此。

**D2：字段集完全采用 `RoleConfig` 的 12 个（用户已选），不保留另外 5 个。**
顺序与原签名一致：`name`、`system_prompt`、`toolkit`（三个无默认值）在前，其余 9 个带默认值在后 —— 该顺序在 dataclass 里合法。
不保留 `role` / `prompt` / `tool_names` / `context_config` / `react_config`：它们全仓零引用，且与 `name` / `system_prompt` / `toolkit` / 摊平参数构成两套并存（尤其 `prompt` 与 `system_prompt`、`react_config` 与 `max_iters`）。
备选：取并集（保留两套）—— 否决，会让同一个类的提示词与 ReAct 参数各有两种来源。

**D3：删除 `base.py` 的 `Toolkit` 导入。**
删除 `RoleConfig` 后，`Toolkit` 在 `base.py` 只剩 `:283` 的 docstring 文字，不构成代码引用 → 留着会触发 ruff `F401`。`base.py` 里没有别的地方需要它。

**D4：`config.py` 新增 `from agentscope.tool import Toolkit`。**
供 `toolkit: Toolkit` 注解使用。虽然有 `from __future__ import annotations` 让注解变惰性字符串（运行期不解析），仍按正常做法导入 —— 否则 IDE 与 mypy 会报未定义名。

**D5：保留 `name` 字段名，不改成 `role`。**
依据：`name` 被 `base.py:139` 用作 Agent 名（现行取值为 `executor_role` / `verifier_role`）；而 `role`（planner/executor/verifier 类别）零引用。沿用 `name` 可让 3 处构造点**只改类名、kwargs 一字不动**。

**D6：以 `skip_specs: true` 退出 specs 阶段。**
纯重构：字段语义、默认值、Agent 名与提示词的来源全部不变。

## Risks / Trade-offs

- [手抄默认值时抄错，行为变了] → 任务里用 AST 断言 12 个字段名与默认值序列，并与 `RoleConfig` 原签名逐项对照；运行期再加一条"构造后打印 `vision`/`max_iters`/`max_image_num`"的冒烟。
- [漏改调用方] → 全仓检索 `RoleConfig`：除归档变更单文档外应 0 命中。
- [frozen 撞到隐式写入] → 已核实无重新赋值；但这条的**真实判据是 pytest**，所以只要提权可用就必须跑。
- [pytest 在本会话不可执行] → 沙箱读不到 `site-packages`；上一次同类提权被用户拒绝。本单把"用户在本机终端执行"写成并列路径，未执行不打勾。
- [改到用户手写的 docstring] → `config.py` 的模块 docstring 是用户前一单期间亲手写的，本次只改其中第 2 条（它描述的是即将被替换的旧字段集），保留其结构与语气。

## Migration Plan

无部署动作：`role/base.py` 与 `role/config.py` 都不在平台运行链路的 import 图上（`apps/` 只引同包 `tools/tool_serial.py`）。
回退策略：把 12 个字段搬回 `base.py` 重建 `RoleConfig`，恢复 `executor.py` / 测试的导入与构造名，`config.py` 恢复原来的 6 字段 `RoleSpecConfig`。

## Open Questions

- 是否引入平台侧那层"`tool_names` → 工具包"的解析（即 `BaseRole` 只吃配方、由装配层解析工具）—— 本次不做，见 Non-Goals；要做需另立一单。
- `RoleSpecConfig` 这个名字与平台侧 `RoleSpec` 不一致（本次按用户要求保留该名）—— 将来若要两棵树统一，应连同 `openai` 分支去留、异常类型对齐一起考虑。
