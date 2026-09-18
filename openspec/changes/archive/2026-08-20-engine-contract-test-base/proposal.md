## Why

L1c 详档 §六 要求"每个引擎实现必须通过同一套 EngineContractTest"——现状 18 个契约用例与 AirtestU2Engine 的 mock 接线耦合在同一文件，新引擎落地时无法复用"协议行为断言"。基类化后：协议契约（连接流/感知格式/操作转发/XPath/生命周期）与引擎接线分离，新引擎只需继承 + 提供 ENGINE_CLASS 与 `_install_mocks`。

## What Changes

- 新增 `tests/engines/contract_base.py`：`EngineContractTestBase` + 6 个非 Test 前缀契约类（Capabilities/ConnectFlow/Perception/Operations/XPath/Lifecycle）+ FakeU2/FakeAd 假件
- `tests/engines/test_airtest_u2_contract.py` 重构：契约类继承基类并接线（ENGINE_CLASS=AirtestU2Engine、CONNECT_ERROR=EngineConnectError、`_install_mocks`）；AirtestU2 特有静态辅助（probe/fetch）留在本文件
- 行为零变化：用例集与断言等价（25 tests/engines 全绿）

## 关联文档

- ARCH：`设计-L1c-引擎层.md`（§六 契约测试规范）、`设计-现状架构-重构落地实测.md`（差距 #3）
- 纯测试重构：`skip_specs: true`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

## Impact

- 仅 `tests/engines/`；产品代码零改动
