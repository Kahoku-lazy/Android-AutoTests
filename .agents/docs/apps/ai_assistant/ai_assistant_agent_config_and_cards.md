# ai_assistant · Agent 配置与助手名片

> 归属模块：`backend/apps/ai_assistant` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/ai_assistant/models.py`、`api.py`、`views_drf.py`
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 职责

用 **Agent 配置** 和 **模型配置** 创建 Agent 角色。模型配置只登记创建模型需要的连接参数，
不在这里造模型实例；Agent 配置登记名称、一条模型配置和系统提示词。

## 助手名片

名片是另一张表 `ai_assistants`：显示名、压缩头像、笔色、对 `role_id` 的引用、工具勾选。
**不复制提示词和模型参数。** 编号是 `YYYYMMDD_XXX`（大写），与 `role_id` 分开。

## 对话与快照

- 测试对话在 `ai_assistant_threads` / `ai_assistant_messages`。
- 打开对话**不跑模型**；首次发送才把当时名片冻成 snapshot，交给 `backend_bridge`。
- 改名片**不改**已经发送过的栏。
- **SOP 不读这些对话栏。**

## 分层纪律

**写库入口只在 `api.py`** —— View / Tool 一律经 `api.py` 落库，View 直写 ORM 属违规。
落库的**实现层在 `services/`**（`agent_configs.py` / `assistant_cards.py` / `assistant_threads.py` 等），
由 `api.py` 调用，不直接对外。
全局的写库路径与信封规则见 `backend/AGENTS.md` §1.1、§1.3。
