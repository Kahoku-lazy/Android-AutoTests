## Purpose

平台任务线路：AI 编排平台工具，完成「探索手机→元素定位→页面图谱→用例生成→用例执行」测试资产生产流水线，区别于设备控制的「操作设备到状态」。

## ADDED Requirements

### Requirement: 平台任务按三模型工作流执行
平台任务 SHALL 复用 planner → executor ↔ verifier 三模型工作流；planner 一次规划多目标，逐目标由 executor 编排工具执行、verifier 二次确认，失败退回重试，max_loops 用尽返回「任务失败」。

#### Scenario: 单目标平台任务
- **WHEN** 用户提交一个平台任务（如「生成 govee 用例」）
- **THEN** planner 产出至少一个 GoalPlan（含 goal/steps/verification），executor 用平台工具完成 steps，verifier 用查询工具确认 pass

#### Scenario: 失败重试
- **WHEN** verifier 判定 fail
- **THEN** 同目标退回 executor 重试，直到 pass 或 max_loops 用尽返回「任务失败」

### Requirement: 平台任务使用平台工具
平台任务的 executor SHALL 使用 REASONING_TOOLS（元素定位 / 用例管理 / 测试执行 / 工作流），verifier SHALL 使用 PLATFORM_VERIFIER_TOOLS（只读查询子集）。

#### Scenario: 元素定位职责
- **WHEN** 任务为「探索手机并保存元素定位」
- **THEN** executor 依次调用 capture_page / analyze_page / save_page_semantic / save_page_to_elements，verifier 用 fetch_page_elements 确认元素已写入

#### Scenario: 用例执行职责
- **WHEN** 任务为「执行用例集」
- **THEN** executor 调用 run_test 并轮询 get_run_status / get_run_results，verifier 用 get_run_results 确认 run 状态

### Requirement: 平台写工具自动放行
平台写工具（save_page_semantic / save_page_to_elements / create_page_flow / save_page_flow / save_case / save_api_test_case / run_test / stop_run）SHALL 加入 AUTO_ALLOW_TOOLS，用户下发任务即授权，不触发 HITL。

#### Scenario: 写工具无需确认
- **WHEN** executor 调用 save_case 保存用例
- **THEN** 工具直接执行，不触发 RequireUserConfirmEvent

### Requirement: 平台任务全用文本模型
平台任务的 planner / executor / verifier SHALL 使用文本模型（vision=False），因为平台工具返回 JSON / 文本、无图片。

#### Scenario: 无图片上下文
- **WHEN** 平台任务执行
- **THEN** 三个 Agent 均以文本模型创建，不启用 vision
