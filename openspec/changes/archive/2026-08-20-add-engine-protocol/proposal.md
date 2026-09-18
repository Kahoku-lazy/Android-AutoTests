## Why

引擎接触点当前散落 6 处（pool/views/service/connect/recovery/adapter），且无统一接口契约——后续换引擎（真机云/新框架）无从谈起。Step 3a 是 L1c 详档 §三/§四 的**纯新增第一步**：定义 `UiEngine` 协议、`Node`/`EngineCapabilities` 数据契约与注册表工厂，不接任何现有代码（零激活、零行为变化），为 Step 3b 的实现收敛与 Step 4 的 DeviceSession 提供依赖面。

## What Changes

- 新增顶级包 `engines/`（零 `apps.*` 依赖，仅依赖 `models.*` 与第三方库）：
  - `engines/base.py`：`UiEngine` Protocol（生命周期/感知/操作原语/可选 XPath 能力/`capabilities`）、`EngineCapabilities` dataclass
  - `engines/registry.py`：`ENGINE_REGISTRY`（airtest_u2 插槽）、`ConfigurationError`、`get_device_engine(name)` 工厂（**调用方传引擎名**，engines 不 import django settings，保持层纯度）
- 新增 `models/ui_nodes.py`：`Node` dataclass（D-2 决策：Node 归属 models/，engines 可 import `models.*`）
- 新增 `tests/engines/test_base.py`、`tests/engines/test_registry.py`（纯单元测试）
- 不修改任何现有代码路径、不注册 settings、无运行时激活

## 关联文档

- ARCH：`dev_docs/03-设计与架构/设计-L1c-引擎层.md`（§三 接口契约权威详版、§四 注册表工厂、§六 契约测试规范）
- ARCH：`dev_docs/03-设计与架构/设计-目标架构-设备交互协议与引擎分层.md`（§2.4 L1c、§三 防火墙 engines 行、§一 D-2）
- 基线：OpenSpec 已归档 `2026-08-20-refactor-baseline-tests`
- 无 PRD 变更（纯新增接口，无需求级行为变化）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯新增接口/类型（无运行时激活、无需求级行为变化）：`.openspec.yaml` 已设 `skip_specs: true`。

## Impact

- 新增：`engines/{__init__,base,registry}.py`、`models/ui_nodes.py`、`tests/engines/`
- 对现有代码、API、数据库、前端零影响
