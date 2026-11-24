## Why

助手的新建、修改和删除现在认「运营」身份，工作流则允许任何已登录用户创建。运营组同时还管用户和模型配置，无法只把「创建助手与工作流」单独交给某个人。

## What Changes

- 新增「助手作者」能力：只有超级管理员天然拥有，并可单独授予、收回。
- **BREAKING**：助手的写操作不再认运营组。运营但不是作者时，与普通用户一样不能新建、修改、删除。
- **BREAKING**：工作流不再允许任意已登录用户创建。作者和超级管理员才能写，其他人只能使用已发布的记录。
- 被授权者不能再转授，也不能授予自己。收回后已发布内容继续可用。
- 停用账号同时失去作者身份，重新启用不自动恢复。

## 关联文档

PRD-评测与发布授权

## Capabilities

### New Capabilities

- `assistant-author`: 助手作者的判定、授予、收回，以及助手与工作流写操作的准入。

### Modified Capabilities

- `assistant-bound-sop`: 工作流的创建、编辑、删除从「已登录用户」收紧为助手作者。
- `ai-assistant-card`: 名片的创建、配置回写和删除从运营收紧为助手作者。

## Impact

- `backend/shared/users.py`：新增作者判定，不改 `is_operator()`。
- `backend/apps/ai_assistant/`：助手与工作流的写接口改权限；新增授予与收回接口。
- 前端助手页：按作者身份显示新建、配置、删除；使用入口保持不变。
- 测试：`tests/ai_assistant/api/`、`tests/ai_assistant/unit/`，以及运营身份的负向用例。
