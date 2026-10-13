## Why

脚手架自己的规范 `engines/agents/AGNETS.md` 对异常**没有任何规定**；上层 `engines/ai/AGENTS.md` 也只要求注释写"功能 / 入参 / 返回值"，所以 `Raises:` 一直靠自觉。AST 盘点（`engines/agents/**`，排除 `skills/` 供应商脚手架）结果：

- **15 个函数有显式 `raise`，只有 5 个写了 `Raises:` 段，10 个没写。**
- `BaseRole` 是其中最典型的：整类只有 `_require_agent` 一处 `raise`，但它此前**连 docstring 都没有**；而 `reply` / `reply_stream` / `interrupt` 会把两类 `RuntimeError` **穿透**出去（未 `start()`；在运行中的事件循环内调用被 `asyncio.run` 拒绝），调用方从签名上完全看不出来。
- 另有幽灵条目：`__init__` 的注释里写着 `ValueError: API 密钥不是字符串或 SecretStr 类型`，但**全仓没有抛点**（实测 `SecretStr(123)` / `SecretStr(None)` 都静默存值、不校验）。

本单先落**用户指定的范围**：`role/base.py` 的注释 + `AGNETS.md` 的规则；其余缺口留待后续单。

## What Changes

- `engines/agents/role/base.py`：
  - 类 docstring 写明两类既定异常（`ValueError` / `RuntimeError`）。
  - `__init__` docstring：保留用户已写好的格式与真实条目，删除不存在的 `SecretStr` 校验条目。
  - `reply` / `reply_stream`：补成「功能 + Args + Returns + Raises」，写出穿透的两类 `RuntimeError`。
  - `interrupt`：补 `Raises`（同上）。
  - `_require_agent`：补「功能 + Returns + Raises（`RuntimeError`）」。
- `engines/agents/AGNETS.md`：新增「异常与 Raises 规则」四条 + 两套注释格式模板（**模块 docstring** 与**方法 docstring**）。
- 清理尾随空白：`role/base.py` 4 行、`role/config.py` 10 行（含两处模块 docstring 首行 `"""` 后的空格）；`AGNETS.md` 的模块模板同步去掉该空格，并把原来的"说明"改成**禁止规则**（`"""` 后不得加空格、docstring 内空行不得留缩进空格）。
- 对 `role/config.py` 跑一次 `ruff format`（用户要求）：补齐 `RoleSpecConfig` docstring 后的空行、清理 `__main__` 块内的空行并把超长 `ModelConfig(...)` 折行、文件尾补换行。改后该文件与 `role/base.py` 均通过 `ruff format --check`。
- 删除 `role/config.py` 末尾的 `__main__` 调试块（用户要求）—— 该文件唯一的 `T201 print` 就在其中。删除后 `role/base.py` 与 `role/config.py` 的 `ruff check --no-cache` 均为 **`All checks passed!`**。
- **Non-goals（本次不做，已登记）**：
  - 其余 8 处 `Raises:` 缺口：`tools_config.py`（`select_tools` / `_assigned_tools` / `_skill_sources`）、`tools/tool_serial.py`（`_parse_log_at` / `read_device_log` / `check_device_log`）、`tools/tool_wrapper.py`（`call`）、`agents.py`（`main`）。
  - `role/config.py` 的 2 处幽灵 Raises（`ModelConfig` 与 `ChatModelFactory.__init__` 里那条不存在的 `SecretStr` 校验，以及写错归属的"不支持的模型提供商"）。
  - 不给不抛异常的函数加声明；不合并两处 `_require_agent` 守卫；不新增异常类。

## 关联文档

无关联需求编号。本次是纯文档变更（docstring + 规范一节），不改变任何可观察行为，也不进入项目的 PRD / ARCH 编号体系。按 schema 约定设 `skip_specs: true`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。纯文档：没有任何函数的异常类型、触发条件或运行时行为发生变化（校验脚本断言全类 `raise` 语句逐字未变，且只有 `_require_agent` 一处）。故以 `skip_specs: true` 退出 specs 阶段。

## Impact

- docstring：`engines/agents/role/base.py`（未被 git 跟踪）。
- 规范：`engines/agents/AGNETS.md`。
- 平台侧零改动：`engines/ai/**`、`apps/**`、`frontend/**` 不动。
- 行为风险：无（`raise` 语句与异常类型逐字未变）。
- 附带产出：用实测钉死了"工具 docstring 加 `Raises:` 会不会污染模型可见描述"这个问题 —— AgentScope `FunctionTool` **只取首行摘要**作 `description`、**只取 `Args:` 段**作参数说明，`Raises:` 段两者都不进（探针 `temps/probe_tool_docstring.py`）。这条事实写进了规范第 4 条。
