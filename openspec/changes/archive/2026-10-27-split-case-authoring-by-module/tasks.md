## 1. 模块规划

- [x] 1.1 新增 `prompts/case_module_planner_prompt.py` 与 `build_case_planner`：带行号输入、结构化输出模块区间；FLASH、无工具、max_iters=2。验证：角色单测 + prompt 纪律断言。**验证结果**：真实 PRD 规划出 10 个模块（PWR/PRTC/SCHD/BLE/WIFI/MEM/NTC/RND/LAMP/COMP），行区间 1~160 连续覆盖；单测通过。
- [x] 1.2 新增 `workflow/case_module_plan.py`：`ModulePlan` / `ModuleRange`、区间校验、覆盖率检查、按标题/固定行数回退、`split_module`、`build_module_document`。验证：单测覆盖切分、回退、拆分、拼接。**验证结果**：13 个模块测试通过；真实 153 PRD 规划 10 块、158 PDF 回退 5 块。
- [x] 1.3 `prompt_config.py` 导出规划提示词。验证：prompt 单测。**验证结果**：`CASE_MODULE_PLANNER_PROMPT` 已导出，prompt 单测 6 passed。

## 2. 模块化编写与截断

- [x] 2.1 编写提示词新增「模块化交付」：只处理片段、原子编号区段、E2E 模块前缀、自检只统计本模块；补充规模控制、未定判据状态与阈值来源。验证：prompt 纪律断言。**验证结果**：prompt 单测断言模块 KEY、原子区段、E2E 前缀、规模上限、已判定/已登记覆盖率。
- [x] 2.2 重写 `CaseAuthoringWorkflow`：单模块内首稿 + 一次按意见重写；重写时附上一版文档做定点修复；记录输出 token，达到 60,000 或空交付标记 truncated，并跳过验收。验证：单测 + 现有角色测试。**验证结果**：单测覆盖截断结果不通过、重写输入包含上一版文档与意见；真实单模块 CLN 24,704 输出/21,351 字符一次通过。
- [x] 2.3 新增 `run_case_authoring_modules`：规划 → 逐模块生成 → 截断拆分（最多两层）→ 拼接；单 ALL 模块保持整份模式。验证：单测覆盖拆分后通过、整份模式。**验证结果**：拆分后 3 次调用、2 个子模块、拼接含模块标题与 PASS；ALL 模式保持原文。
- [x] 2.4 `task_runner._run_case_authoring` 接入模块化流水线，结果新增 `modules` / `truncated` / `max_output_tokens`。验证：任务 runner 单测。**验证结果**：映射测试通过，摘要带模块数。

## 3. 验证与门禁

- [x] 3.1 后端相关单测：新增模块测试、提示词、角色、task runner、API 用例。验证：pytest 输出。**验证结果**：case authoring 相关 38+ passed。
- [x] 3.2 真实任务：用 153/158 同款大 PRD 提交一次，确认至少切成多块、单块输出低于 60K、事件流可见规划与逐模块过程。**验证结果**：153 同款 PRD 规划 10 块并按模块运行，事件流可见 planner / writer / verifier 与模块标题；CLN 单模块 24.7K 输出、21K 文档、一次验收通过。完整 10 模块任务因单模块重写耗时过长被手动取消；152 全量任务在内容正确性上仍被驳回（非截断），属于下一轮提示词/验收优化。
- [x] 3.3 `python run.py check` 与 `openspec validate split-case-authoring-by-module --strict`。验证：退出码 0。**验证结果**：门禁 22/22 阻塞项通过；变更校验 valid。
- [x] 3.4 归档变更。**验证结果**：已归档到 `openspec/changes/archive/2026-10-27-split-case-authoring-by-module/`。
