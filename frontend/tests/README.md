# Frontend Vitest — 总注册表

优先级约定见 **[PRIORITY_TEMPLATE.md](./PRIORITY_TEMPLATE.md)**；分类设计见 **[DESIGN-module-classification.md](./DESIGN-module-classification.md)**。

目录按「模块 × 优先级」分类：

```
tests/<module>/
  p0/   # 必测 *.spec.ts
  p1/   # 建议测 *.spec.ts
  p2/   # 默认不测（仅 README 登记）
```

`helpers/`（挂载工具）与 `reports/`（报告产物）不是模块。Vitest UI 按 `<module>/<prio>` 分栏自动生成，新增模块只需建目录。

## 模块注册表

| 模块 | 目录 | 状态 | P0 文件 | P1 文件 | 说明 |
|------|------|------|---------|---------|------|
| dashboard | `tests/dashboard/` | ✅ P0+P1 | 2 | 4 | 数据编排 / 统计卡 / 导航 / 任务面板 / 活动线 |
| login | `tests/login/` | ✅ P0+P1 | 8 | 3 | 表单校验 / 账号池 / 认证流程 / 卡片 |
| devices | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| inspector | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| elements | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| cases | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| runner | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| reports | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| ai-assistant | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| workflow | — | ⬜ 未开始 | 0 | 0 | 待开测 |
| digital-human | — | ⬜ 未开始 | 0 | 0 | 待开测 |

> 新模块开测流程：按 `PRIORITY_TEMPLATE.md` 的 Checklist 建目录与用例 → 更新本表状态列。

## 用例命名规范

```ts
describe('[P0] <被测单元>')    // composable / 组件 / 编排器
it('<场景>：<预期>')            // 场景=操作或输入；预期=断言结果；多预期用「，」并列
```

模块名不写进命名（由文件路径 + UI 分栏承载）。反例：`it('测试登录')`（无场景无预期）、`it('登录成功, 写token')`（半角逗号）。

## 命令

```bash
cd frontend
npm test                          # 全部（所有模块 P0+P1）
npm run test:p0                   # 跨模块只跑 P0
npm run test:p1                   # 跨模块只跑 P1
npm run test:module -- login      # 只跑指定模块
npm run test:report               # 终端 + JUnit + JSON + 按模块汇总
npm run test:report:html          # 静态 HTML 报告（tests/reports/html/index.html）
npm run test:ui                   # Vitest UI：左侧按 模块/优先级 分栏
```

底层入口：`node tests/run.mjs [default|module|prio|file|verbose|junit|json|all|html|watch|ui]`。
