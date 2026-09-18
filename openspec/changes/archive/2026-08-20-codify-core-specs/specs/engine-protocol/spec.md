## Purpose
UiEngine 协议与注册表：Android 执行引擎的统一契约——UI 操作原语语义稳定，引擎实现可替换；新引擎必须通过契约测试方可注册。

## ADDED Requirements

### Requirement: 操作原语契约
引擎实现 MUST 提供 click、long_click、swipe、input_text、press_key、shell、start_app、stop_app 操作原语；语义 SHALL 与契约一致（坐标为设备像素）。

#### Scenario: 操作转发
- **WHEN** 上层调用任一操作原语
- **THEN** 引擎按契约语义将该操作执行到设备连接层

### Requirement: 感知标准化
screenshot MUST 返回 JPEG bytes；dump_hierarchy MUST 返回标准 Node 列表（models.ui_nodes.Node schema）；引擎不得向调用方泄漏引擎特有数据格式。

#### Scenario: 截图与层级
- **WHEN** 调用 screenshot 或 dump_hierarchy
- **THEN** 分别返回 JPEG 字节与 Node 列表

### Requirement: 能力声明
引擎 MUST 通过 capabilities 声明 xpath_locate、toast_wait、ocr 能力；上层使用可选能力前 MUST 依据声明探测，不支持时 SHALL 降级处理。

#### Scenario: 可选能力探测
- **WHEN** 上层需要使用 XPath 或 Toast 能力
- **THEN** 依据 capabilities 声明决定调用或降级

### Requirement: 注册表 fail-fast
未知或未实现的引擎名 MUST 在解析时抛出 ConfigurationError；工厂不得静默回退到其他引擎。

#### Scenario: 未注册引擎名
- **WHEN** get_device_engine 收到未注册的引擎名
- **THEN** 抛出 ConfigurationError（含已注册清单）

### Requirement: 契约测试门槛
每个注册进 ENGINE_REGISTRY 的引擎实现 MUST 通过 EngineContractTestBase 的契约测试集。

#### Scenario: 新引擎注册前提
- **WHEN** 新引擎实现加入注册表
- **THEN** 其继承基类的契约测试全部通过
