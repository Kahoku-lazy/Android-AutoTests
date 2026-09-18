## Context

原 18 个契约用例直接 import `engines.android.airtest_u2` 并在 fixture 里 monkeypatch Android/subprocess/u2——协议断言与引擎接线混杂，无法复用。

## Goals / Non-Goals

**Goals:**

- 协议契约与引擎接线分离；新引擎继承基类即可过同一套断言
- 用例数/断言语义不变（纯搬移 + 参数化接线）

**Non-Goals:**

- 不新增契约用例；不接 registry 自动枚举（未来引擎落地时按需）

## Decisions

- **双继承结构**：`class TestAirtestXxx(XxxContract, TestAirtestU2Contract)`——契约类提供断言、接线类提供 ENGINE_CLASS/_install_mocks；契约类改名非 Test 前缀避免被 pytest 直接收集
- **CONNECT_ERROR 类属性**：连接失败异常类型引擎各异，默认 RuntimeError，AirtestU2 覆盖为 EngineConnectError
- **USB/ATX 用例进基类**：协议级行为（USB 跳过 adb、失败消息映射），经 `_make`（只接线不连接）表达

## 模块防火墙自检

- 纯测试改动；通过

## Risks / Trade-offs

- [多继承 MRO 歧义] → 契约类不含同名方法；fixture 仅基类定义；25 用例全绿验证
