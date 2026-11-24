## MODIFIED Requirements

### Requirement: 自带配置且只允许配置向量模型

知识库 MUST NOT 再携带向量模型文件或库目录文件。向量模型参数与库列表 MUST 由调用方传入：向量模型参数限定为 `provider` / `api_key` / `model_name` / `dimensions`，且 `provider` 只接受受支持的向量厂商；出现其它字段、其它模型类别或不支持的厂商时 MUST 拒绝创建。库列表的每一项 MUST 含库名、说明、只读资料目录与启用状态，两个启用库的资料目录 MUST NOT 相同或互相包含。知识库 MUST NOT 读取平台数据库，也 MUST NOT import 平台代码。聊天模型创建层与 `agents/` MUST NOT 因本能力被修改。

#### Scenario: 调用方传入向量模型

- **WHEN** 调用方传入受支持厂商的向量模型参数与合法库列表
- **THEN** 知识库按该模型建索引并检索
- **AND** 不读取任何自带 yaml

#### Scenario: 非向量模型条目被拒绝

- **WHEN** 传入的向量模型参数含聊天、实时语音或语音合成字段，或厂商不受支持
- **THEN** 创建失败
- **AND** 错误信息指出违规字段或厂商

#### Scenario: 密钥不以明文出现

- **WHEN** 嵌入模型创建成功或失败
- **THEN** 错误信息与返回值只含环境变量名
- **AND** 不包含密钥明文

## REMOVED Requirements

### Requirement: 探针不调用聊天模型

**Reason**: 探针原先隐式读取自带 yaml。自带配置文件删除后，该入口不再有默认数据源。
**Migration**: 索引与检索探针改为必须显式接收向量模型参数与库列表；仍不得创建智能体、不得调用聊天模型。无命中时退出码为 0，参数非法或密钥缺失时退出码非 0。
