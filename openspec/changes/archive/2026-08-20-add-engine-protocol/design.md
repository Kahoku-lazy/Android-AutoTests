## Context

L1c 详档 §三 已给出接口契约权威详版；L1a 详档 D-2 决策 `Node` 归属 `models/`（engines 只可 import `models.*`）。Step 3b 将实现 `AirtestU2Engine` 并收敛 6 处接触点，Step 4 的 DeviceSession 经 `get_device_engine()` 取引擎——本变更只立契约，不接实现。

## Goals / Non-Goals

**Goals:**

- `UiEngine` Protocol / `EngineCapabilities` / `Node` 三件契约落地且可 import
- `get_device_engine(name)` 工厂：已知名→实例；未知名→`ConfigurationError`（fail-fast）
- 纯单元测试覆盖契约与工厂

**Non-Goals:**

- 不实现 `AirtestU2Engine`（Step 3b）
- 不改 `device_pool`/`test_runner` 任何现有代码
- 不写 `EngineContractTest` 完整套件（Step 3b 随实现交付）
- 不 import django settings（engines 层纯度：调用方传引擎名）

## Decisions

- **Node 归属 models/**：`models/ui_nodes.py` 独立模块（非 test_models，避免与测试域混装）；字段与目标架构 §2.4.2 一致（含 `xpaths` 默认空列表）
- **UiEngine 定位**：`Protocol`（结构子类型，不强制继承）；XPath 三方法（exists/get_text/wait_toast）为可选能力，由 `capabilities` 声明门控（L1a 决策 D-A：路线 A）
- **注册表懒加载**：`ENGINE_REGISTRY` 存 import 路径；`get_device_engine` 惰性 import + 实例缓存（threading.Lock 保护），未实现插槽（airtest_u2）在 3b 前被调用时抛 `ConfigurationError`（明确失败而非静默）
- **工厂签名**：`get_device_engine(name: str = "airtest_u2") -> UiEngine`——调用方（未来 DeviceSession）负责从 settings 解析名字传入

## 模块防火墙自检

- `engines/` 只 import `models.*`（`from models.ui_nodes import Node`）与标准库；无 `apps.*`/`django.*`
- 本变更不新增任何跨 App import、无 ORM、无前端改动
- 通过

## Risks / Trade-offs

- [接口契约过早冻结] → 契约在 L1c 详档 §三 已经过评审口径；若 3b 实现时发现出入，以「⚠️ 契约出入」显式登记并回改 base.py（详档已约定该流程）
- [airtest_u2 插槽指向未实现模块] → 工厂在 import 失败时抛 `ConfigurationError` 带路径信息，测试覆盖该分支
- [Node 与 dict 现状并存] → Node 是目标契约，现状 dict 经 Step 2 保留；转换在 Step 3b/4 逐步发生
