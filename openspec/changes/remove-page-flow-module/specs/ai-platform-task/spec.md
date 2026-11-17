## MODIFIED Requirements

### Requirement: 平台任务使用平台工具

平台任务的 executor SHALL 使用 REASONING_TOOLS（元素定位 / 用例管理 / 测试执行），verifier SHALL 使用 PLATFORM_VERIFIER_TOOLS（只读查询子集）。工具域 MUST NOT 再包含已退役的页面流（工作流）域。

#### Scenario: 元素定位职责

- **WHEN** 任务为「探索手机并保存元素定位」
- **THEN** executor 依次调用 capture_page / analyze_page / save_page_semantic / save_page_to_elements，verifier 用 fetch_page_elements 确认元素已写入

#### Scenario: 用例执行职责

- **WHEN** 任务为「执行用例集」
- **THEN** executor 调用 run_test 并轮询 get_run_status / get_run_results，verifier 用 get_run_results 确认 run 状态

### Requirement: 平台写工具自动放行

平台写工具（save_page_semantic / save_page_to_elements / save_case / save_api_test_case / run_test / stop_run）SHALL 加入 AUTO_ALLOW_TOOLS，用户下发任务即授权，不触发 HITL。已退役的页面流写工具（create_page_flow / save_page_flow）MUST NOT 再出现在放行清单中。

#### Scenario: 写工具无需确认

- **WHEN** executor 调用 save_case 保存用例
- **THEN** 工具直接执行，不触发 RequireUserConfirmEvent
