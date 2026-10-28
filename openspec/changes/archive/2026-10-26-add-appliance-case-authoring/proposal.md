# 家电测试用例编写与验收角色

## Why

`appliance-test-cases` 技能把家电用例方法论写全了，但只有方法论正文：平台无法把「拆解需求写用例」和「验收用例」交给两个独立模型互相制衡，产出质量只能靠人工通读，覆盖空洞与不可判定的预期容易漏到执行阶段。

## What Changes

- 新增用例编写角色 `case_writer_role`：按技能的五阶段 SOP 把需求拆成原子，产出需求原子表、方法分配表、冲突登记表、13 字段用例表、E2E 与自检统计。
- 新增用例验收角色 `case_verifier_role`：只判卷不改写，按需求覆盖、原子质量、方法匹配、优先级、13 字段、预期可判定、E2E/冲突、一致性八组清单判 `passed`，驳回意见必须逐条可执行。
- 两个角色复用 SOP 的「执行者 + 验收者 + 最多两次尝试」：验收不通过就把驳回意见原样退回，编写角色在同一步重写；两次都不过则该步失败。
- 两份提示词放 `engines/agents/prompts/`，正文提炼自技能；技能原文仍是方法论维护基准。
- 两个角色都是纯文本、无工具：需求正文与已有用例索引由调用方放进开场输入，不读写文件、不操作设备。

## Capabilities

### New Capabilities

- `appliance-case-authoring`：家电测试用例的编写角色、验收角色与成对运行口径。

### Modified Capabilities

无。

## Impact

- 新增：`engines/agents/prompts/case_writer_prompt.py`、`engines/agents/prompts/case_verifier_prompt.py`、`engines/agents/role/case_roles.py`、`engines/agents/workflow/case_authoring_workflow.py`。
- 修改：`engines/agents/prompt_config.py`（导出两份提示词）、`engines/agents/tools_config.py`（空工具包）、`engines/agents/workflow/__init__.py`（导出入口）。
- 测试：`tests/graybox/unit/test_case_authoring_prompts.py`、`tests/graybox/unit/test_case_authoring_roles.py`。
- 不影响后端接口、前端、数据库、设备执行链路与现有 executor / verifier 角色。
