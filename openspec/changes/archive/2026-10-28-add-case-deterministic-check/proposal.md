# 用代码做用例文档的确定性校验

## Why

GoalPipeline 让编写/验收循环更稳，但「用例数、P0 占比、方法数、覆盖率、追溯 ID」这些都可以从 Markdown 表格直接算出来。现在交给模型自检，结果经常与表格实际数字不一致；验收又只能看到自评，导致「统计不符」反复消耗重试预算。

把这些检查改成代码执行，并在每轮写完后用代码重写第六节统计，模型只需要负责内容，不再负责算术。

## What Changes

- 新增 `workflow/case_document_check.py`：
  - 解析需求原子表、用例表、E2E 表与七节标题；
  - 校验章节齐全、原子/用例 ID 唯一、追溯 ID 存在、原子覆盖、13 字段非空、状态枚举、复杂度方法数下限、P0 占比、E2E 条数与预期模糊词；
  - 用表格实际数据重写第六节「覆盖与门禁自检」（P0/P1/P2 数量与占比、已判定/已登记覆盖率、方法统计、E2E 条数）。
- GoalPipeline 每轮写完后先做确定性校验：
  - 有确定性问题时追加一条 `[确定性问题]` 判决，阻止本轮通过；
  - 下一轮输入同时带确定性问题和验收意见；
  - 第六节统计直接回写到 `ModuleStore`，验收角色读到的是修正后的文档。
- 提示词补充：不要依赖模型自评数字，平台会用代码复核并回写第六节。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `appliance-case-authoring`：新增「确定性校验」要求，第六节统计由平台代码重写。

## Impact

- 引擎：新增 `workflow/case_document_check.py`；`workflow/case_goal_workflow.py` 接入校验与回写。
- 测试：新增解析/校验/统计回写单测、GoalPipeline 确定性问题阻断单测。
- 无数据库、接口、前端变化。
