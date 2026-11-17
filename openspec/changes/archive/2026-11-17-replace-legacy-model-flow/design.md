## Context

见 proposal.md 的 Why。现状与本设计相关的约束：

- `config.load_model_config()` 已返回整张表，密钥以 `SecretKey` 注入；缺密钥不阻断装载。
- `models_new.create_model(表, 短名, stream=)` 已能造 chat / realtime / embedding / tts。它不读文件、不缓存、不提供查询，也不接受 `api_key` / `dimensions` / `voice` / `usage_sink`。
- `assistant.create_chat_agent` 已按 `(短名, stream)` 复用聊天模型；`create_voice_agent` 不复用实时语音模型。`agent_builders.build_*` 与语音会话已转调这两个出口。
- 生产代码仍 import 旧包的位置：`role_loader`（角色引用与短名存在性）、`knowledge_chat/config.py`（正式名与密钥变量名）、`realtime_vocie/config.py`（默认模型名，以及仅测试使用的 `create_realtime_model`）、`knowledge_assistant/consumer.py`（`voices`）、`rag/config.py`（默认名与维度）、`rag/service.py`（嵌入实例 + 明文密钥 + `usage_sink`）、`messaging/billing.py`（Flash / Pro 档名）。
- `omni.voices` 在 `models.yaml` 里目前是注释，不是有效字段。消费者仍调用 `get_realtime("omni").voices`；空列表时不拦截用户音色。
- 交卷关思考只挂在旧包 `builder` 上。新创建路径没有这层包装。删除旧包前必须把行为挪走，否则强制交卷会重新打开思考。
- `get_fallback_chat_model` 没有生产调用方。重试中间件只使用调用方传入的实例。

## Goals / Non-Goals

**Goals:**

- 生产代码不再 import `engines.agents.models`，随后删除该包。
- 查规格与造实例分开：查看不 `reveal()`，创建仍只经 `create_model`。
- 聊天模型复用继续留在 assistant，不搬回模型层。
- 交卷关思考的行为在删除旧包装饰器后仍然只生效一次。

**Non-Goals:**

- 不把 `temperature`、VAD、`voice=`、明文 `api_key=`、`usage_sink` 加进 `create_model`。
- 不在本变更里用新出口重造备用模型。未传入实例就不回退。
- 不恢复 TTS 的生产调用方。`create_model` 已能造 tts，没有调用方就不另做门面。
- 不改 workflow 编排，不改角色 YAML 字段形状。

## Decisions

### 1. 只读视图放在 `config`，不放进 `models_new`

新增 `engines/agents/config/model_view.py`，只导出按短名取视图。输入是 `load_model_config()` 的表，或测试注入的同形映射。视图是冻结数据：`model_name`、`family`、`voices`、`dimensions`、`api_key_env`。它不调用 `reveal()`，`repr` 不含密钥。

未知短名抛现有 `ValueError`，消息带可选短名。不新增异常类。

备选是让每个调用方自己读表。否决：字段名会散到 5 个模块，音色和维度的缺省也不一致。另一备选是给 `models_new` 加 `describe`。否决：该包的红线是只有一个创建出口。

### 2. 嵌入实例仍经 `create_model`，用量留在 RAG

`rag/service.py` 改为 `load_model_config()` + `create_model(表, 短名)`。维度以模型表为准，不再在调用点覆盖。

用量回调不进创建出口。RAG 在拿到嵌入模型后，只在本服务内记录嵌入 token；记录失败不得中断检索。若当前框架实例没有可挂的用量回调点，本服务保持「检索失败降级为空上下文」，不把回调参数加回 `create_model`。

明文 `api_key=` 删除。密钥只来自表内 `SecretKey`，在 `create_model` 内部 `reveal()`。

### 3. 语音会话不再保留第二套 Omni 构造

`realtime_vocie/config.py::create_realtime_model` 与包导出删除。会话继续走 `create_voice_agent`。VAD / `turn_detection` 仍留在会话配置，不写入 `create_model` 的覆盖参数。现有「经 config 工厂造 Omni」的测试改为断言会话路径只转调语音出口，或改为注入假模型，不联网。

### 4. 计费档名从模型表读取

`DeepSeekBilling` 继续只认两个正式模型名。档名在计费模块装载时从只读视图取 `deepseek_flash` 与 `deepseek_pro` 的 `model_name`，不再 import `DeepSeekModelConfig`。旧名别名（`deepseek-v4-flash` 等）仍按 Flash 价，别名表留在计费模块。

### 5. 交卷关思考挪到中间件，不进 `create_model`

把 `apply_forced_handover_kwargs` 的行为移到 `engines/agents/middleware/`，由现有中间件装配在模型调用前改写请求。幂等条件改为「改写函数本身对非交卷请求原样返回」，这样共享聊天模型不会被叠包装。

不在 `models_new.create_model` 里挂装饰。创建层不知道什么是交卷。

### 6. 旧包整包删除，不做兼容门面

生产 import 清零、测试改完后删除 `engines/agents/models/`。不在旧 `__init__.py` 里把 `get_chat_model` 转调 `create_model`：签名（正式名、覆盖项、缓存键、明文密钥）对不上，兼容层会假装迁完。

`models_new` 不改名为 `models`。调用方已经写死 `models_new`，改名是另一次无行为变化的搬移。

### 7. 文档与门面守卫一起改

`engines/agents/AGENTS.md` 与 `config/AGENTS.md` 改为：造实例只经 `models_new`，查规格只经 `config.model_view`。`models/AGENTS.md` 随包删除。门面守卫测试从「禁止 import `models` 子模块」改为「禁止包外构造模型类，且生产代码不 import 已删除的旧包」。

## 模块防火墙自检

- 不新增跨 App import。`knowledge_assistant/consumer.py` 继续只读 engines 的公开视图，不 import 其它 App 的 service / consumer。
- 无 INSERT / UPDATE / DELETE。本变更不写库。
- 前端不参与，仪表盘不参与。
- engines 仍不 import `django` / `apps.*`。只读视图放在 `engines.agents.config`，backend 只调用该公开函数。
- 新依赖方向：`config.model_view` 不 import `models_new`；`models_new` 不 import `config`；RAG / 计费 / 语音配置只 import 视图或 `create_model`，不 import 对方内部模块。

## Risks / Trade-offs

- [删除旧包后强制交卷重新打开思考] → 先迁中间件并跑现有交卷测试，再删装饰器。
- [`omni.voices` 仍是注释，迁移后白名单变空] → 只读视图对缺失 `voices` 返回空元组，消费者保持「空列表不拦截」。是否把注释改成有效字段不在本变更。
- [RAG 不再接受调用点维度与明文密钥] → 维度只以模型表为准；测试改为注入带 `SecretKey` 的假表，不传明文密钥。
- [聊天缓存从「短名 + 覆盖指纹 + 事件循环」收成「短名 + stream」] → 这是 assistant 的既有行为，本变更不改缓存键。旧测试若断言跨循环新建，改为断言 assistant 的键。
- [备用模型环境变量不再被任何生产代码读取] → 与规格一致：未传入实例就不回退。需要备用模型时由后续变更在调用方显式传入，不在本变更猜造。

## Migration Plan

1. 加只读视图，并把 5 个「只查不造」调用方改过去。旧包仍在。
2. RAG 改 `create_model`；删除 `create_realtime_model`；计费改读视图。
3. 交卷改写挪到中间件，跑交卷测试。
4. 生产代码与测试不再引用旧包后，删除 `engines/agents/models/`，并改 AGENTS 与门面守卫。
5. 回滚：恢复旧包目录与 import。只读视图是新增文件，回滚时调用方改回旧 import 即可，不需要数据迁移。

## Open Questions

无。未在模型表中启用的 `voices` 字段是否改成有效 YAML，不改变本变更的读取与空列表语义，留到单独的音色配置变更。
