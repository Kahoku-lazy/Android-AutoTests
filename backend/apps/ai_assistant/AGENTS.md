# ai_assistant AGENTS.md

> 层级：根 `AGENTS.md` → `backend/apps/AGENTS.md` → **本文件**。

本 App 的设计目的是：用 **Agent 配置** 和 **模型配置** 创建 Agent 角色。模型配置只登记创建模型需要的连接参数，不在这里造模型实例；Agent 配置登记名称、一条模型配置和系统提示词。

助手名片是另一张表 `ai_assistants`：显示名、压缩头像、笔色、对 `role_id` 的引用、工具勾选。不复制提示词和模型参数。编号是 `YYYYMMDD_XXX`（大写），与 `role_id` 分开。写库只在 `api.py`。

测试对话在 `ai_assistant_threads` / `ai_assistant_messages`。打开对话不跑模型；首次发送才把当时名片冻成 snapshot，交给 `backend_bridge`。改名片不改已经发送过的栏。SOP 不读这些对话栏。
