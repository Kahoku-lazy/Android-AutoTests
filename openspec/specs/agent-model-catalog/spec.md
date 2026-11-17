# agent-model-catalog Specification

## Purpose
把模型从「角色的一个配置段」升级为独立资产：`models.yaml` 唯一声明连接参数与能力，角色只写引用与调用姿势，任何代码位置都能按模型名取到模型，并且在加载前完成配置校验。

## Requirements

### Requirement: 模型表是唯一数据源

系统 SHALL 从 `engines/agents/config/data/models.yaml` 读取 chat / realtime / embedding / tts 四族模型声明；表按模型短名平铺，每个条目 SHALL 用 `family` 声明所属族，并声明 provider、正式模型名、密钥环境变量名与可选的能力、上下文长度、默认参数。角色配置 MUST NOT 定义 `provider` / `model_name` / `base_url` / `api_key` 等连接参数，只 SHALL 写模型短名引用与调用姿势（如 `stream`）。

#### Scenario: 角色只写引用与调用姿势

- **WHEN** 检查任一角色的 `ModelConfig` 段
- **THEN** 只包含 `model: <短名>` 与 `stream` / `temperature` 等调用姿势字段，不出现 provider、模型名、地址或密钥

#### Scenario: 角色写连接参数被拒绝

- **WHEN** 某个角色的 `ModelConfig` 段出现 `provider` 或 `api_key` 字段
- **THEN** 配置加载失败，报错指出该角色与禁止出现的字段名

### Requirement: 加载前完成配置校验

系统 SHALL 在构造任何模型实例之前校验模型表，且校验 SHALL 分为三段，每段只做「它拿得到输入」的那部分判断：

1. **结构**（单条）：类型、必填、取值范围、枚举、未知字段——由 `ModelSpec` 的字段声明承担；
2. **语义**（单条）：provider 已在注册白名单内、族必填项齐全、`parameters` 不含禁止键；
3. **引用**（批量）：短名唯一、`model_name` 必须存在于该 provider 该族的模型目录。

归一（`vision` 展开、按族补 `output_types` 缺省）SHALL 发生在结构校验之前，因为 `vision` 不是模型字段、且「放错层的键」需要在未知字段校验之前给出解释性报错。校验不通过的模型 MUST NOT 进入加载阶段；报错 MUST 包含所在文件、族与短名、字段路径；同一份配置的报错文案 MUST 风格统一（不得中英混杂）。

#### Scenario: 未注册的 provider

- **WHEN** 模型表里出现未注册的 `provider: mygateway`
- **THEN** 校验失败并提示该 provider 未注册，列出已注册 provider

#### Scenario: 字段类型错误

- **WHEN** 某模型的 `context_size` 写成非整数字符串
- **THEN** 校验失败，报错含模型短名、字段路径与期望类型

#### Scenario: 能力声明冲突

- **WHEN** 某模型同时声明 `vision: true` 且 `input_types` 不含任何 `image/*`
- **THEN** 校验失败并指出两处声明矛盾

#### Scenario: 未知字段

- **WHEN** 某模型条目里出现不属于模型字段的键（如 `bogus`）
- **THEN** 校验失败并报「未知字段」，指出该字段路径

#### Scenario: 提示词或明文密钥混入模型表

- **WHEN** 某模型条目里出现 `system_prompt` / `prompt_path` / `api_key`
- **THEN** 校验失败，报错说明该内容应归属角色配置或环境变量，而不是笼统提示「未知字段」

#### Scenario: 一次报出同一条目的多处结构错误

- **WHEN** 同一模型条目同时存在两处结构错误
- **THEN** 报错一次列出全部错误，而不是只报第一条

### Requirement: 模型名必须真实存在

系统 SHALL 在装载阶段核对 `model_name` 是否属于该 provider 该族的模型目录（框架模型类的 `list_models()`），不属于时 MUST 装载失败并列出可选模型名。该校验 MUST 可一键关闭，关闭时装载不依赖任何框架模型目录。

#### Scenario: 模型名写错

- **WHEN** 某 chat 条目的 `model_name` 写成 `deepseek-v5`
- **THEN** 装载失败，报错指出该模型名不在 `deepseek` 的模型目录里，并列出可选模型名

#### Scenario: 关闭该校验

- **WHEN** 把该开关关闭
- **THEN** 装载只做结构与语义校验与短名唯一检查，不读取任何框架模型目录

### Requirement: 按模型名加载四族模型

系统 SHALL 提供按模型名取模型的能力：短名（如 `deepseek_flash`）与正式模型名（如 `deepseek-flash`）都必须可解析，且命中同一条目；四族分别提供聊天、实时语音、嵌入与语音合成的取用入口。未知模型名 MUST 报错并列出当前可用的短名。

#### Scenario: 按短名取聊天模型

- **WHEN** 调用方请求 `deepseek_flash`
- **THEN** 返回该条目的聊天模型实例，调用方无需提供任何连接参数

#### Scenario: 按正式模型名反查

- **WHEN** 调用方请求 `deepseek-flash`
- **THEN** 解析到同一条目 `deepseek_flash` 并返回模型实例

#### Scenario: 未注册的模型名

- **WHEN** 调用方请求一个不存在的短名
- **THEN** 报错并列出当前可用短名清单

#### Scenario: 非聊天模型同样按名取用

- **WHEN** 需要实时语音、嵌入或语音合成模型
- **THEN** 分别经对应入口按模型名取用，调用方不出现框架模型类的构造代码

### Requirement: 能力由声明推导

系统 SHALL 由 `input_types` 是否含 `image/*` 推导模型是否支持图片输入，MUST NOT 依赖手写的布尔开关；SHALL 提供 `context_size` / `output_size` 的查询供上下文预算与界面展示使用。当请求携带图片而目标模型的 `input_types` 不含 `image/*` 时，系统 MUST 拒绝并说明该模型不支持图片输入。

#### Scenario: 声明含图片即支持视觉

- **WHEN** 某模型 `input_types` 含 `image/png`
- **THEN** 该模型被判定为支持图片输入，装配视觉角色时无需额外开关

#### Scenario: 纯文本模型收到图片请求

- **WHEN** 向 `input_types` 只有 `text/plain` 的模型发起带图片的请求
- **THEN** 拒绝该请求并说明模型不支持图片输入

### Requirement: 模型级参数与覆盖优先级

系统 SHALL 支持在模型表中声明 `parameters` 默认值、`context_size`、`max_retries`、`formatter`；角色与调用点 SHALL 可覆盖其中可覆盖项。生效优先级 MUST 固定为「框架默认 < 模型表 < 角色配置 < 调用点覆盖」，同一字段出现在多层时以更高层为准。`provider` / `model_name` / `api_key_env` MUST NOT 被角色或调用点覆盖。

#### Scenario: 角色覆盖流式开关

- **WHEN** 两个角色引用同一模型，其中一个角色写 `stream: false`
- **THEN** 该角色取到的模型为非流式，另一个角色仍按模型表或自身配置取值

#### Scenario: 调用点覆盖采样参数

- **WHEN** 调用方在取模型时传入 `temperature`
- **THEN** 该次实例使用调用点的值，模型表与角色层的同名字段被覆盖

#### Scenario: 连接参数不可被覆盖

- **WHEN** 调用方试图在取模型时覆盖 `model_name`
- **THEN** 请求被拒绝，并提示连接参数只能在模型表中修改

### Requirement: 模型实例按规格复用

系统 SHALL 按「模型短名 + 覆盖指纹 + 事件循环」复用聊天模型实例：同一事件循环内、生效规格完全相同的两次取用 MUST 返回同一实例；任一覆盖项变化 MUST 视为不同实例；MUST NOT 跨事件循环复用。系统 SHALL 提供显式清空复用的入口。

#### Scenario: 同规格同实例

- **WHEN** 同一循环内两次以相同参数取同一模型
- **THEN** 两次返回同一对象，不重复构造客户端

#### Scenario: 覆盖变化即新实例

- **WHEN** 第二次取用时 `stream` 与第一次不同
- **THEN** 返回新建实例，不复用旧实例

#### Scenario: 跨事件循环不复用

- **WHEN** 两个任务在各自线程的事件循环里取同一模型
- **THEN** 后起的循环得到新实例

### Requirement: 备用模型由主模型派生

系统 SHALL 以主模型的生效规格为基线派生备用模型，只覆盖环境变量中显式给出的差异（模型名、provider、地址、密钥），并 SHALL 允许备用模型属于不同 provider。未配置备用模型名时 MUST 返回空，不构造实例。

#### Scenario: 跨 provider 派生

- **WHEN** 主模型为 DeepSeek、环境变量指定备用模型为 DashScope 且给出对应密钥变量
- **THEN** 备用模型使用 DashScope 的连接参数，其余能力与调用姿势继承主模型

#### Scenario: 未配置备用模型

- **WHEN** 环境变量中没有备用模型名
- **THEN** 取备用模型返回空，不产生任何实例

### Requirement: 提示词不进入模型表

模型条目 MUST NOT 包含系统提示词正文或其文件路径；提示词 SHALL 由角色侧（`RoleConfig` 与提示词目录）提供，模型实例只接收已解析好的提示词字符串。

#### Scenario: 校验拒绝提示词字段

- **WHEN** 模型条目里出现 `system_prompt` 或提示词路径字段
- **THEN** 校验失败并提示提示词属于角色配置

#### Scenario: 模型表不含提示词

- **WHEN** 检查 `models.yaml` 的全部条目
- **THEN** 不存在提示词正文或提示词文件路径字段
