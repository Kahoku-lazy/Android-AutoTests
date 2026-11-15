## Why

角色创建主链已经改走 `assistant` + `models_new`，但知识库、语音音色、RAG 和计费仍直接调用旧包 `engines.agents.models`。旧包自己读文件、读环境变量，还把「查规格」和「造实例」焊在一起；主规格仍要求模型实例只经旧门面，和新包「只有一个创建出口」互相打架。现在不替换，下一次实现会按旧红线把调用打回去，旧包也删不掉。

## What Changes

- 新增只读模型视图：从已装载的模型表按短名取出 `model_name` / `family` / `voices` / `dimensions` / `api_key_env`。查看规格 MUST NOT 构造模型，MUST NOT 解密密钥。
- 角色装载、文字问答就绪状态、语音默认模型名、音色白名单、RAG 默认维度改读该视图，不再 import 旧包。
- 嵌入模型的构造改经 `models_new.create_model`。用量回调留在 RAG 服务自己包一层，不进入模型创建出口。**BREAKING**：包外不再经旧门面 `get_embedding_model` 取嵌入实例。
- 计费档名改为从模型表的正式模型名派生，不再依赖旧包的计费兼容类。
- 生产代码不再 import `engines.agents.models` 之后，删除旧包及其「自读 YAML、五入口、实例缓存、备用模型派生、交卷装饰」。
- 备用模型保持现状：未配置就不回退；重试模块只接收已建好的实例，不在本变更里改用新出口重造。
- 交卷时关闭思考的行为保持不变，实现从旧包装饰器挪到中间件，不在模型创建出口里做。
- 文档与主规格改为：造实例只经 `models_new`，查规格只经只读视图；`engines/agents/models/` 不再是模型代码归属。

## 关联文档

无关联 PRD。原因：这是模型层的结构替换，对齐已落地的 `config` 读表与 `models_new` 创建出口，不改变任务、用例、页面或对外 HTTP 行为。

## Capabilities

### New Capabilities

- `model-catalog-view`: 从已装载模型表按短名只读查看规格；不造实例、不解密密钥。

### Modified Capabilities

- `agent-harness`: 「模型配置唯一装载入口」与「模型实例只经单一门面获取」改为 config 读表、`models_new` 造实例、只读视图查规格；删除旧包门面约束。
- `agent-model-resilience`: 备用模型不再由旧模型包解析；未配置即不回退，重试模块仍只接收已建好的实例。

## Impact

- 代码：`engines/agents/config/`（只读视图）、`role_loader.py`、`knowledge_chat/config.py`、`realtime_vocie/config.py`、`rag/config.py`、`rag/service.py`、`messaging/billing.py`、`middleware/`；`backend/apps/knowledge_assistant/consumer.py` 改为读只读视图。
- 删除：`engines/agents/models/`（生产调用清零之后）。
- 文档：`engines/agents/AGENTS.md`、`engines/agents/models/AGENTS.md`（随包删除）、`engines/agents/models_new/AGENTS.md`、`engines/agents/config/AGENTS.md`。
- 测试：角色装载、知识库文字/语音配置、RAG、计费、模型重试、门面守卫；不要求联网。
- 非目标：不改 `workflow/` 编排；不把 RAG 用量回调、调用点 `temperature` / VAD 覆盖、厂商注册表做进 `create_model`；不恢复 TTS 生产入口（当前无生产调用方）。
