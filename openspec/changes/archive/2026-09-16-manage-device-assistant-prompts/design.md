## Context

动机见 `proposal.md` Why。现状：三角色系统提示词写死在 `engines/ai/agentscope/config.py`（`PLANNER_PROMPT` / `VISION_PROMPT` / `VERIFIER_PROMPT`），`AgentRole._assemble` 使用 `self.spec.prompt`。`TaskRequest` 无提示词字段。`AIAgent.system_prompt` 已在 0029 删除。工具箱左侧来源仅 `biz` / `skill`，带「交给助手」总闸。前端已有 `renderSkillMarkdown`（marked + DOMPurify）。写库必须走 `apps/ai_assistant/api.py`。`views_drf.py` 已超 views 行数上限，本变更的 HTTP 入口单独落文件。

## Goals / Non-Goals

**Goals:**

- 三份提示词以表字段为唯一运行时真相源
- Django `build_request` 读库注入引擎；引擎常量留空
- 工具箱第三来源管理提示词：渲染 MD + 管理员编辑保存
- 空提示词：保存拒绝、任务装配 fail-fast

**Non-Goals:**

- 不恢复已删除的单字段 `system_prompt`
- 不把提示词塞进 `route_configs`（避免与密钥混存）
- 不引入所见即所得 Markdown 编辑器
- 不给提示词加「交给助手」总闸
- 不改平台业务工具 / Skill 启停语义
- 不在本变更修复 `enable_business_tools` 未过滤 `build_tool_specs` 的既有缺口

## Decisions

### D1 存 `ai_agents` 三列，不进 JSON

- 选择：`prompt_planner` / `prompt_executor` / `prompt_verifier`（`TextField`，blank 允许、应用层禁止空串）
- 理由：用户要求「从数据表读取」；三列可迁移灌数、装配校验直白
- 备选：`route_configs.device_control.{role}.system_prompt` — 无迁移但与 api_key 同对象，序列化脱敏易误伤；独立表 — 单智能体过重

### D2 专用读写端点，不塞进 platform-config

- 选择：`GET /api/ai/device-prompts`（登录可读）、`POST /api/ai/device-prompts/update`（仅超管）
- 响应键：`planner` / `executor` / `verifier`（与线路角色名一致）
- 理由：提示词体量大，不应与 `enable_*` 开关混在同一 PATCH；权限模型对齐 `PlatformConfigAPIView`
- 备选：扩 `platform-config` — 少路由，但配置接口膨胀、前端工具箱每次拉开关都带全文

### D3 数据迁移快照灌数，再把引擎常量留空

- 选择：schema 迁移加列后，`RunPython` 把**快照**（现行三份常量正文）写入所有已有 `AIAgent`；代码变更将 `config.py` 三常量赋值为 `""` 并保留名字以免 import 断裂
- 理由：若迁移时 `import` 已留空的常量，存量库会灌进空串并导致全员任务 fail-fast
- 回滚：恢复常量非空 + 回退迁移；已编辑过的库内容需人工备份

### D4 `TaskRequest.system_prompts` + 角色构造注入

- 选择：`TaskRequest.system_prompts: dict[str, str]`，键 `planner` / `executor` / `verifier`。`build_device_models(..., system_prompts=)` 传入各 `AgentRole`；`system_prompt=` 用注入值，`RoleSpec.prompt` 改为空串
- 理由：协议层仍零 Django 依赖；引擎无回退路径，符合「引擎提示词留空」
- 备选：继续读 `RoleSpec.prompt` 若请求缺省 — 禁止，会把空常量或旧文案偷偷用回来

### D5 工具箱第三来源无总闸

- 选择：`ASSEMBLY_SOURCES` 增加 `prompt`；`gateKey` 可空；该行不渲染 `el-switch`，不进入顶部生效芯片
- 右侧：三角色分段或 Tab；默认 `v-html` + `renderSkillMarkdown`；管理员「编辑」切出 textarea + 实时预览，一次保存三份
- 理由：提示词不是可选工具源；MD 渲染复用 Skill 预览，不新增依赖
- 备选：独立路由页 — 离开装配台，与用户指定的左侧栏位不符

### D6 视图文件拆分

- 选择：新建 `apps/ai_assistant/views_prompts_drf.py`（`DevicePromptsAPIView`），`urls.py` 注册；写库函数 `get_device_prompts` / `update_device_prompts` 进 `api.py`
- 理由：`views_drf.py` 已超 300 行上限，继续堆砌会关单失败

## 模块防火墙自检

- 跨 App import：本变更只读/写 `ai_assistant` 自己的 `AIAgent`，不 import 其他 App 的 service/runner/consumer
- 写库：仅 `api.update_device_prompts` → ORM
- 引擎：`engines/ai` 仍零 `apps.*`；提示词经 `TaskRequest` 注入
- 前端：只走 `djangoClient` `/api/ai/device-prompts*`
- 无新跨模块写依赖

## Risks / Trade-offs

- [灌数快照与代码常量日后漂移] → 迁移只跑一次；之后以库为准，常量保持空串
- [空提示词导致任务全失败] → 保存与装配双 fail-fast；迁移必须先灌满存量
- [Markdown XSS] → 继续 DOMPurify；服务端存源码不执行 HTML
- [超大提示词撑满 JSON] → 可接受（现有常量已数千字）；不做分页
- [正在运行的任务不热更新] → 与 Skill 开关相同：下次 `build_request` 生效

## Migration Plan

1. 加列 + 数据灌入（部署迁移）
2. 发布含注入与空常量的应用代码
3. 回滚：回退应用使引擎再用旧常量（仅当库被改坏且无备份时的紧急手段）；正常回滚以恢复库备份为准
