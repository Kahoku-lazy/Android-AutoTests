## Context

见 `proposal.md` - Why。当前 `engines/agents/role/base.py` 里三个类承担三种职责：`ModelConfig`（连接数据，今天刚改为 `@dataclass(frozen=True)`）、`RoleConfig`（角色参数）、`CreateModel`（按 provider 造 `ChatModelBase`）。同文件还有一个今天新加、目前尚无任何引用的 `RoleSpec`。

平台侧 `engines/ai/agents/base.py` 另有一个同名 `RoleSpec`（同名不同类），与 `CreateModel` 对应的实现是函数 `create_model`。两棵树互相独立，本次只动脚手架这一棵。

引用面（已全仓核实）：`role/base.py` 的引用方只有同包的 `role/executor.py`、`agents.py` 与 `tests/**`；`apps/` 只从 `engines/agents` 引 `tools/tool_serial.py`，不经过本次改名的两个类。

## Goals / Non-Goals

- Goals：两个类名与本仓库命名口径对齐；引用一次性收敛，不留旧名残留。
- Non-Goals：
  - 不改平台侧 `engines/ai/agents/**`（含其同名 `RoleSpec`）。
  - 不改行为：不动 provider 分支、不动 `SecretStr` 归一化、不动字段顺序与默认值。
  - 不做脚手架与平台两棵树的合并或收敛（属另一件事）。
  - 不顺手修本文件已存在的静态检查问题（见 Risks 第 2 条）。

## Decisions

**D1：`CreateModel` → `ChatModelFactory`（而不是 `ModelVendor` / `ModelProvider`）。**
该类是工厂而非厂商：构造参数 `config` + `stream` + `vision` 里后两个是创建参数，唯一公开动作是 `.create()`，三个分支 `deepseek_model()` / `openai_model()` / `dashscope_model()` 就是按 provider 分派。「厂商」在本仓库已有载体（`ModelConfig.provider`；平台侧另有 `SUPPORTED_PROVIDERS`）。命名成厂商会得到 `ModelVendor(config, stream=..., vision=...)` 这种读不通的调用，并诱发把 provider 白名单搬进工厂的第二真相源问题。
备选：`ModelFactory`（可用，但丢掉「返回的是 ChatModel」这一信息）；`ModelBuilder`（`Builder` 通常指分步构建，语义不符）。

**D2：`RoleSpec` → `RoleSpecConfig`。**
与 `ModelConfig` / `RoleConfig` / `DeviceExecutionConfig` 的 `Config` 后缀口径一致。

**D3：只改脚手架这一份，平台侧 `RoleSpec` 保持原名。**
平台侧改名会波及 7 个文件 + 1 个测试，且平台侧当前正处在大范围未提交改动中（`engines/ai/**` 多文件已修改）。两者混在一个变更里，diff 将无法逐行追溯到本需求。将来若要统一，单独一单。

**D4：以 `skip_specs: true` 退出 specs 阶段。**
类名不是可观察行为。仓库既有的纯重构变更（`2026-10-08-split-agent-roles`）采用同一处理。

**D5：不顺手修本文件既有的 `from dataclasses import ...` 位置问题（第 40 行）。**
该行带来 `I001`（导入块未排序/未格式化）与 `F401`×3（`FrozenInstanceError` / `fields` / `replace` 未使用，仅在 docstring 文本里出现）。它在本需求之前就存在（改动前记为 `E402`，apply 阶段实测 ruff 报的是 `I001`，已按实测更正），与「改名」是两个意图；混进来会让 diff 变脏。改完后单独把问题报给用户。

## Risks / Trade-offs

- [脚手架或注释里仍留旧名] → 改完后全仓检索 `CreateModel` 与 `RoleSpec`，逐个确认归属（Django `migrations.CreateModel(`、平台侧 `RoleSpec`、`openspec/changes/archive/**` 历史文本均属预期）。
- [该文件未被 git 跟踪，改动没有版本历史可回退] → 改名是纯文本替换，回退等于改回原名；改动点只有 4 处（docstring 1 处 + 类定义 2 处 + 构造调用 1 处），改动前先记录。
- [与平台侧 `RoleSpec` 同名易混] → 本次不动平台侧，并在文档中写清两处差异；将来统一时单独立项。
- [该文件今天 15:16 刚被编辑过，编辑器里可能有未保存内容] → 动手前确认用户已保存；`write`/`edit` 走磁盘，不与编辑器缓冲合并。

## Migration Plan

无部署动作：`role/base.py` 不在平台运行链路的 import 图上（`apps/` 不引它），改名不影响任何运行中的服务，也不需要迁移指令。
回退策略：把两个类名改回 `CreateModel` / `RoleSpec`，并复原 4 处引用。

## Open Questions

无。目标名与范围已由用户确认（只改脚手架 `engines/agents/role/base.py` 一份）。
