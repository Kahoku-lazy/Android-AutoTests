## MODIFIED Requirements

### Requirement: 感知标准化

screenshot MUST 返回 JPEG bytes；层级取数 MUST 返回**层级原始 XML 文本**，引擎 MUST NOT 解析层级、MUST NOT 构造 Node 列表（解析由调用方经算法层完成）；引擎不得向调用方泄漏引擎特有数据格式，上层 MUST NOT 通过引擎实现的裸句柄取数。

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