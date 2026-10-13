## Why

SOP 编排现在写在智能体角色目录里，和「role 只放角色」的目录规则冲突。工作流需要单独成层：步骤有明确输入，装配后再交给运行入口，角色配置仍只来自执行角色与验收角色。

## What Changes

- 新增工作流目录 `engines/agents/workflow`，承接现在 `engines/agents/role/sop.py` 里的流程装配与单次运行。
- 步骤输入改为明确格式：`subject` 是步骤短名，`description` 只写必须达成的结果。装配时使用调用方已经启动的执行角色与验收角色，不在工作流里另写提示词、工具或技能。
- 装配结果交给单独的运行入口。运行仍负责事件上屏、对话稿、按次计费。持久化只保存 `SOPRunState`。工具报告日志为空时，这一次尝试记为引擎的一次驳回并消耗重试次数，由引擎决定重做或失败。
- **BREAKING**：`engines.agents.role.sop` 不再提供流程装配与运行入口。调用方改为工作流目录下的对应入口。
- 在 `engines/agents` 的目录说明中补上 `workflow` 的职责。`role` 目录只保留角色。

## 关联文档

无关联 PRD。本次只调整智能体引擎内部的目录职责与调用边界，不改变设备检查的产品需求。

## Capabilities

### New Capabilities

- `agent-sop-workflow`: 用已启动的执行角色与验收角色，把步骤输入装配成可运行流程，并由运行入口推进到完成、挂起或失败。

### Modified Capabilities

## Impact

- `engines/agents/role/sop.py`：移除工作流实现。
- `engines/agents/workflow/`：新增步骤输入与运行入口。
- `engines/agents/AGNETS.md`：补充 `workflow` 目录说明。
- `tests/graybox/unit/test_sop_log_empty_abort.py`：导入路径改为工作流入口；「日志为空」停步行为保持不变。
- 不改 `apps/`、前端页面、接口契约或数据库。
