## Why

`U2Engine.shell` 在契约里声明返回 `str`（`engines/device/base.py:53`），实现却直接把 uiautomator2 的原生响应对象 `ShellResponse`（`NamedTuple(output: str, exit_code: int)`）交给调用方。平台工具 `list_apps` 因此对这个对象调 `.splitlines()` → `AttributeError` → 调试页 400；而换成任何走 `_jsonable`/JSON 的消费方**不会报错**，只会静默得到 `["<stdout>", 0]` 这种错形状（`ShellResponse` 本身是 tuple，会被 `isinstance(obj, (list, tuple))` 命中）。引擎边界本就有「不得向调用方泄漏引擎特有数据格式」的要求，但该实现未归一化，也没有任何用例覆盖 `shell` 的返回值。

## What Changes

- `engines/device/android/u2.py::shell` 归一化为返回命令标准输出**字符串**（取 `ShellResponse.output`），恢复与 `base.py` 声明的 `-> str` 一致。
- `engine-protocol` 的「感知标准化」要求显式覆盖 `shell`：MUST 返回标准输出字符串，MUST NOT 直接返回引擎原生响应对象（含 tuple/NamedTuple 形态）。
- 新增**零设备**回归用例：假 u2 的 `shell` 返回真 `ShellResponse`，断言 `U2Engine.shell` 返回 `str` 且取到 stdout；同一用例断言协议对 `shell` 的返回声明为 `str`。
- **不**改 `list_apps` 的调用方式（它按契约拿字符串、用 `.splitlines()` 是对的）；**不**改其余协议方法；**不**动 `EngineContractTestBase`（全仓不存在，是另一个问题，见下方 Impact 备注）。

## 关联文档

- PRD-00（需求总纲，AI 工具箱增量）
- 前置变更：`add-platform-tool-debug`（`list_apps` 调试入口）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `engine-protocol`: 「感知标准化」扩展为覆盖 `shell` 的返回值归一化（MUST 返回字符串、MUST NOT 泄漏原生响应对象），并补一条对应场景。

## Impact

- 引擎：`engines/device/android/u2.py`（`shell` 一行）
- 测试：新增 `tests/graybox/unit/test_engine_shell_contract.py`（零设备、零 I/O）
- 消费方：`apps/ai_assistant/tools.py::list_apps` 不修改，修复后自然跑通
- 前端 / 数据库迁移 / 依赖：无
- **本单不处理的已知相邻问题**：`engine-protocol` 的「契约测试门槛」要求各引擎通过 `EngineContractTestBase`，但该基类全仓不存在（历史变更已注明未落地），因此这类违约没有通用守卫。修正该要求（落地基类或改写要求）属独立变更。
