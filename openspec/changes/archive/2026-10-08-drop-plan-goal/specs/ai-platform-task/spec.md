## MODIFIED Requirements

### Requirement: 平台任务按三模型工作流执行
平台任务 SHALL 复用 planner → executor ↔ verifier 三模型工作流；planner 一次规划多目标，逐目标由 executor 编排工具执行、verifier 二次确认，失败退回重试，max_loops 用尽返回「任务失败」。planner 产出的计划 MUST 只含步骤列表（每步含 `action` / `assert` / `log_check`），MUST NOT 再回述目标（目标由任务自身的「任务目标」承载）。

#### Scenario: 单目标平台任务
- **WHEN** 用户提交一个平台任务（如「生成 govee 用例」）
- **THEN** planner 产出至少一个只含步骤的计划（每步 `action` / `assert` / `log_check`），executor 用平台工具完成这些步骤，verifier 用查询工具确认 pass

#### Scenario: 失败重试
- **WHEN** verifier 判定 fail
- **THEN** 同目标退回 executor 重试，直到 pass 或 max_loops 用尽返回「任务失败」
