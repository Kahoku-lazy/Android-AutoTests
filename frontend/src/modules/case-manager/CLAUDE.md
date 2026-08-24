# case-manager 模块 CLAUDE.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../CLAUDE.md`；本文只写本模块增量，冲突以全局为准。

## 红线（全局表 case-manager 行的展开）

| 只做 | 禁止 |
|------|------|
| 四类用例定义与步骤编排（拖拽排序/选 XPath/YAML 导入导出/编辑锁） | 执行用例（唯一例外：单步调试经 `/runner/run-step`）/ 步骤类型定义落地前端 |

- **步骤 JSON 结构不能破坏**；`steps_data` 序列化字段名与 StepType 枚举对齐，否则用例保存后执行失败。
- 步骤类型定义以后端 `/cases/step-types` 为准，禁止前端落地新类型。

## 本模块契约（真相源：`api/` 子目录 uiAutomation / storage / apiTesting / webAutomation / directories；根 `api.ts` 只是 re-export facade。端点有增删必须同改）

- 用例：`/cases/definitions*`（四类共用）· `/cases/step-types?target=` · `/cases/export/yaml` · `/cases/exports`
- 锁与可见性：`/cases/definitions/{id}/{lock|unlock|case-lock|case-unlock|visibility}`（`unlock` body `{ force }`；`visibility` body snake_case `permitted_users`）
- 跨模块：`/devices`（调试）、`/devices/{serial}`（`{ activate: true, mode: "observe" }`）、`/devices/{serial}/disconnect-observe`、`/elements/pages`、`/runner/run-step`（单步调试唯一入口）

## 本模块协议要点

**WS 编辑锁（本模块专属，全项目仅 2 个 WS 消费点之一）**：

- 连接经 `useCaseEditingSocket.ts`，URL 走 `wsUrl('/ws/case-editing/{id}?token=…')`（Vite 代理，禁直连端口）；只监听 `case_updated` 事件，用于外部（如 AI）改用例后自动刷新。
- 有未保存修改时先询问用户（`isDirty`），loading/saving 时跳过（`shouldIgnore`），禁止静默覆盖；断线重连最多 5 次。
- REST 编辑锁（`acquireEditLock`/`releaseEditLock`）与 case 锁（`caseLock`/`caseUnlock`）是另一套机制，与 WS 锁不可混用。

## 关单附加项（全局清单的 delta）

```
[ ] 步骤 JSON 结构完整；steps_data 字段名与 StepType 枚举对齐
[ ] 编辑锁：锁态只读禁用；WS 脏数据先问后刷；无静默覆盖
[ ] 单步调试走 /runner/run-step，不旁路执行引擎
[ ] 四类用例共用 api.ts facade，不直接 import 子目录实现
```
