## Why

用例管理把功能用例和自动化用例放在同一张表，再用目录和文件分层。999 行以内，分层只增加跳转；行上的类型标签也挡不住把功能用例拿去执行。旧用例数据当前不用，应直接清掉。

## What Changes

- **BREAKING**：删除目录、文件和现有用例行。一个项目就是一张表，不再提供新建目录或文件夹。
- 新建项目时锁定库类型：自动化或功能。创建后不可改。
- 项目页直接打开这张表。筛选、排序、分组、隐藏列是个人视图，不是目录。视图跟随登录用户存在服务端。
- 一个项目最多 999 条用例。YAML 按字段追加导入；字段非法或追加后超过 999，整份不写入。
- 页头只保留图标和标题。新建、导入、保存、新增行放到正文工具条。
- 执行仍只跑里程碑 YAML。平台来源只可选自动化表中的行，提交前编译成里程碑。功能表不可执行。
- Agent 验收通过的功能用例继续追加进该用户的「AI 生成用例」功能表，同样受 999 限制。

## 关联文档

无独立需求编号。范围来自本轮确认：一项目一表、创建时锁定库类型、旧数据清空、YAML 追加且上限 999、个人视图存服务端、Agent 产物继续入库。`PRD-平台总需求.md` 仍写「项目 → 目录 → 文件 → 用例」，本变更会改掉目录与文件两层。

## Capabilities

### New Capabilities

- `case-project-sheet`：一项目一张多维表，库类型锁定，999 上限，个人视图，YAML 追加导入。
- `case-sheet-execution`：自动化表可编译为里程碑后执行；上传里程碑不入库；功能表不可执行。

### Modified Capabilities

- `case-manager-case-form`：用例行直接属于项目，不再挂文件；删除行内类型列。
- `case-manager-workspace-preview`：左树右预览与文件详情跳转作废，改为项目表。
- `appliance-case-authoring-task`：入库目标从用例文件改为该用户的功能表，并受 999 限制。
- `dashboard-case-project-cards`：项目卡进入项目表，计数按库类型取对应表。
- `frontend-l2-page-region`：用例管理页头不得再放功能按钮。
- `task-card-sop-form`：平台来源改为选择自动化项目中的行，而不是文件下的用例。

## Impact

- 后端：`backend/apps/case_manager/` 模型、迁移、项目/目录/文件/定义接口；`backend/apps/task_list/` 的平台用例物化；`backend/apps/dashboard/` 项目计数。
- 前端：`frontend/src/modules/case-manager/` 删除树、文件页和预览，改为项目表；任务提交选择器只列自动化项目。
- 规格与测试：上述 6 个既有 spec 的 delta，以及 `tests/case/`、`frontend/tests/case-manager/`。
- 不恢复已删除的 `engines/agents` 用例 YAML 执行器，不新增第二种 SOP。
