# engine-protocol Specification

## Purpose
UiEngine 协议与注册表：Android 执行引擎的统一契约——UI 操作原语语义稳定，引擎实现可替换；新引擎必须通过契约测试方可注册。

## Requirements

### Requirement: 操作原语契约
引擎实现 MUST 提供 click、long_click、swipe、input_text、press_key、shell、start_app、stop_app 操作原语；语义 SHALL 与契约一致（坐标为设备像素）。MUST 额外提供 click_xpath、long_click_xpath（按 XPath 定位第 index 个匹配元素中心后执行点击/长按，返回是否命中）。

#### Scenario: 操作转发
- **WHEN** 上层调用任一操作原语
- **THEN** 引擎按契约语义将该操作执行到设备连接层

#### Scenario: XPath 定位操作
- **WHEN** 上层调用 click_xpath 或 long_click_xpath
- **THEN** 引擎按 XPath 匹配第 index 个元素并点击/长按，越界返回 False

### Requirement: 感知标准化

screenshot MUST 返回 JPEG bytes；层级取数 MUST 返回**层级原始 XML 文本**，引擎 MUST NOT 解析层级、MUST NOT 构造 Node 列表（解析由调用方经算法层完成）；shell MUST 返回命令的标准输出**字符串**，MUST NOT 把引擎原生响应对象（含 tuple 或 NamedTuple 形态）交给调用方；引擎不得向调用方泄漏引擎特有数据格式，上层 MUST NOT 通过引擎实现的裸句柄取数。

#### Scenario: 截图与层级
- **WHEN** 调用 screenshot 或层级取数
- **THEN** 分别返回 JPEG 字节与层级原始 XML 文本

#### Scenario: 引擎不解析层级
- **WHEN** 调用层级取数
- **THEN** 引擎返回原始 XML 文本，MUST NOT 返回 Node 列表
- **AND** 引擎实现 MUST NOT 依赖任何解析模块（不得出现对算法层的 import）

#### Scenario: 解析由调用方完成且口径一致
- **WHEN** 调用方把层级原始 XML 交给算法层解析为 Node 列表
- **THEN** 得到的节点集合与既有解析口径一致（节点数，以及每个节点的类名、资源标识、文本与 bounds 相同）

#### Scenario: 不得经裸句柄取数
- **WHEN** 上层（apps/、algorithms/、AI 工具）需要截图或层级数据
- **THEN** 只能经引擎契约方法获取，MUST NOT 访问引擎实现的裸句柄

#### Scenario: shell 返回标准输出字符串
- **WHEN** 底层引擎的 shell 调用返回带输出文本与退出码的原生响应对象
- **THEN** 引擎契约方法返回该输出文本的字符串
- **AND** MUST NOT 把原生响应对象或其 `(输出, 退出码)` 元组形态交给调用方

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

### Requirement: Toast 完整能力
引擎 MUST 提供 get_toast_message（读取当前 toast 文本，无则空字符串）与 reset_toast（清空 toast 缓冲）；两者受 capabilities.toast_wait 门控，不支持时上层 SHALL 降级。

#### Scenario: 读取 toast
- **WHEN** 上层调用 get_toast_message
- **THEN** 返回当前 toast 文本（无则空字符串）

### Requirement: 分辨率查询
引擎 MUST 提供 get_resolution 返回设备物理分辨率 (width, height)，供上层做坐标换算；实现不得向调用方泄漏引擎特有数据结构。

#### Scenario: 获取分辨率
- **WHEN** 上层调用 get_resolution
- **THEN** 返回设备 (width, height) 整数元组
