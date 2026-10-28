## 1. 重试预算

- [x] 1.1 `CASE_MAX_ATTEMPTS` 改为 3，注释与 docstring 同步为「首稿 + 两次重写」。验证：单测断言默认值与三次调用。**验证结果**：默认 3、三次调用均发生；`CaseAuthoringWorkflow` 测试通过。
- [x] 1.2 验收提示词：问题上限 20 → 40；首轮必须一次列全阻断，后轮不得把首轮已存在的内容当新阻断。验证：prompt 纪律断言。**验证结果**：prompt 单测断言「最多 40 条」「首轮必须一次列全所有阻断」。

## 2. 验证与归档

- [x] 2.1 相关单测：模块工作流三次尝试、提示词、角色、空交付检测。验证：pytest。**验证结果**：30 passed（含 tag-only 交付判截断、长文档缺节只记不完整）。
- [x] 2.2 `python run.py check` 与 `openspec validate raise-case-authoring-retry-budget --strict`。验证：退出码 0。**验证结果**：门禁 22/22 阻塞项通过；变更校验 valid。
- [x] 2.3 用 152 同款 PRD 重跑一次，观察是否在第三次内收敛。**验证结果**：任务 163 首稿 44,146 输出被驳回；重写 64,367 触发 60K 截断，自动拆成 ALLA/ALLB；ALLA 三次尝试均被驳回（首轮验收输出 26,930，已列全阻断；第二轮出现空 submission，第三次仍剩内容阻断），随后手动取消。结论：三次预算与截断拆分已生效，但 152 的内容正确性仍未收敛，需要下一轮做确定性校验或更细的模块切分。
- [x] 2.4 归档变更。**验证结果**：已归档到 `openspec/changes/archive/2026-10-27-raise-case-authoring-retry-budget/`。
