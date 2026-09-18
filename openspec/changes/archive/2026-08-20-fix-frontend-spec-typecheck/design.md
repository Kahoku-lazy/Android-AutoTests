## Context

Step 6 门禁记录：typecheck 全量红 24 行（我方区域），vitest 76/76 绿，CI 只跑 vitest。错误全部位于 spec 文件，两类根因（mock 包装、字面量字段）。

## Goals / Non-Goals

**Goals:**

- `vue-tsc` 输出中 test-runner/report-generator 相关错误归零
- vitest test-runner 76/76 保持全绿（断言语义等价）

**Non-Goals:**

- 不修 ai-assistant/dashboard 区域（并发对话所有）
- 不改产品代码；不引入类型宽松化（any 滥用）

## Decisions

- **mock 包装**：`vi.mocked(apiFn)` 后链式 mock 方法；api 模块 import 命名保持一致
- **字面量补字段**：按被测代码实际读写的最小字段集补齐（不虚构无关字段）
- **不跑全量 typecheck 作为完成条件**（其他区域未清）；以"我方区域错误归零"为通过线

## 模块防火墙自检

- 纯测试文件改动，零产品代码触碰；通过

## Risks / Trade-offs

- [补字段引入假行为假设] → 仅补被测代码真实访问的字段，vitest 全绿验证
- [vi.mocked 影响断言语义] → 行为等价（同 mock 目标），vitest 回归
