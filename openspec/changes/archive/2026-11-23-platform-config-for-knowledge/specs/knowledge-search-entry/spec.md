## MODIFIED Requirements

### Requirement: 模块登记与路径维护

系统 SHALL 以平台数据库为模块登记的真相源：一个模块 = 唯一库名 + 描述 + 服务器本地资料目录 + 启用状态。库名 MUST 匹配 `^[a-z][a-z0-9_]*$`；资料目录 MUST 是已存在、可读的绝对路径；两个启用模块的资料目录 MUST NOT 相同或互相包含。模块的新增 / 编辑（含改路径）/ 删除 / 启停 SHALL 仅超级管理员可操作；模块列表 SHALL 登录可读。登记变更后的检索 MUST 使用平台登记的模块与平台检索配置，MUST NOT 再读取引擎自带的库目录文件。校验失败 MUST 返回可读原因且 MUST NOT 落库。已完成首次部署的环境 MUST 保留既有模块登记；全新安装在没有任何登记时模块列表 MUST 为空，MUST NOT 因缺少引擎配置文件而失败。

#### Scenario: 超管新增模块成功

- **WHEN** 超级管理员提交合法库名、描述与已存在的资料目录
- **THEN** 模块落库并出现在模块列表
- **AND** 后续检索能选中该模块

#### Scenario: 非超管写操作被拒绝

- **WHEN** 普通登录用户调用模块新增 / 编辑 / 删除 / 启停
- **THEN** 返回 403
- **AND** 模块列表不变

#### Scenario: 启用库目录冲突被拒绝

- **WHEN** 新增或启用一个模块，其资料目录与另一启用模块相同或互相包含
- **THEN** 返回 400 并指出冲突的两个库名
- **AND** 不落库

#### Scenario: 改路径后按新目录检索

- **WHEN** 超管把某模块的资料目录改为另一个合法目录
- **THEN** 后续提问只命中新目录下的资料
- **AND** 旧目录中已不在新目录的文件不再命中

#### Scenario: 全新安装带初始模块

- **WHEN** 平台首次部署完成且没有任何模块登记
- **THEN** 模块列表为空
- **AND** 不因缺少引擎自带库目录文件而部署失败
- **AND** 超管随后新增的合法模块可被检索选中

### Requirement: 嵌入用量逐调用入账

系统 SHALL 对索引与检索中每次真实发生的嵌入模型调用向 `ai_usage_records` 写入恰好一条记录：category=Embedding、provider 与模型名取自本次实际使用的向量模型配置、input_tokens 为该次调用 token 数、source=knowledge。幂等键 MUST 为「来源:执行 ID:轮次」，同一键重复提交 MUST 更新原行而 MUST NOT 翻倍。token 为 0 或空的调用 SHALL NOT 入账。入账失败 MUST 只记日志，MUST NOT 阻断检索或索引。费用 SHALL 按既有价目表与通用公式计算，MUST NOT 伪造金额。

#### Scenario: 一次提问的嵌入调用逐条入账

- **WHEN** 一次提问触发索引重建与查询嵌入
- **THEN** 每次嵌入调用各有一条 Embedding 记录，source=knowledge
- **AND** token 数与模型返回的用量一致
- **AND** 记录的 provider 与模型名等于本次实际使用的向量模型配置
- **AND** 记录不含密钥明文

#### Scenario: 重复提交不翻倍

- **WHEN** 同一调用的用量被提交两次
- **THEN** 账本仍只有一条该键记录

#### Scenario: 入账失败不阻断检索

- **WHEN** 账本暂时不可写
- **THEN** 检索结果照常返回
- **AND** 失败只记日志
