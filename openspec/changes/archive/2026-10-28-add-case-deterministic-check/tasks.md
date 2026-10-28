## 1. 解析与校验

- [x] 1.1 新增 `workflow/case_document_check.py`：解析原子表/用例表/E2E/七节，校验 ID、字段、方法数、P0 占比、覆盖率与模糊词。验证：单测。**验证结果**：6 个校验单测通过；真实 CLN 模块文档解析出 15 原子 / 14 用例 / 4 E2E，确定性问题 0。
- [x] 1.2 `fix_case_statistics`：按表格实际数据重写第六节统计。验证：单测。**验证结果**：真实文档第六节被重写为 15 原子 / 14 用例 / P0=1（7.1%）/ 已判定 13/15 / 已登记 15/15 / E2E 4。

## 2. 接入 GoalPipeline

- [x] 2.1 `run_goal_module` 每轮写完后执行 `check_and_fix_document`；确定性问题追加判决并进入下一轮，修正后的文档回写存储。验证：单测。**验证结果**：确定性问题阻断单测通过；判决列表最后一条为 `case_deterministic_check`。
- [x] 2.2 提示词补充「平台会用代码复核并回写第六节」。验证：prompt 单测。**验证结果**：编写提示词第六节说明已加入，`ruff format engines/agents` 通过。

## 3. 验证与归档

- [x] 3.1 相关单测全绿。验证：pytest。**验证结果**：用例编写相关 45 passed。
- [x] 3.2 真实任务：观察确定性问题是否在下一轮被修复、第六节是否被回写。**验证结果**：真实 CLN 文档确定性校验 0 问题、第六节成功回写；真实任务 166/169 的事件流可见保存/读取/判决，但任务被后端热重载打断，未形成 completed 终态。
- [ ] 3.3 `python run.py check` 与 `openspec validate add-case-deterministic-check --strict`。**验证结果**：变更校验 valid；门禁 17/22，失败项仍为 knowledge-assistant 的 OpenAPI 与前端格式，以及既有文件 prettier，均不在本变更范围。
- [x] 3.4 归档变更。
