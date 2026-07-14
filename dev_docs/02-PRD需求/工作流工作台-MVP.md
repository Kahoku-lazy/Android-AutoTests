# PRD — 工作流工作台（平台集成 · MVP）

> 状态：已集成并完成元素/用例同步（2026-07）  
> 来源：`tests/workflow-demo` → `frontend/src/modules/workflow`

## 1. 目标

在平台侧边栏提供「工作流」入口，将 Demo 两大能力产品化，并与现有模块数据对齐：

1. **页面流**（Vue Flow）↔ **元素定位 · 元素管理**
2. **测试用例积木**（Blockly）↔ **测试用例 · 用例设计**

## 2. 本期范围

| 纳入 | 不做（下一期） |
|------|----------------|
| 前端模块 `/workflow` | Django `wf_` 表 / 图服务端 CRUD |
| 关联页面拉真实 pages/elements；刷新同步；xpath 解析 | 工作流图多用户协作 |
| 积木「打开用例 / 同步到用例库」 | 分支/循环写入用例结构 |
| localStorage 草稿备选 | 真实执行联动 |

## 3. 验收

- [x] `/workflow` 可进入
- [x] 右键关联来自 `/api/elements/pages`（失败才 Mock）
- [x] 积木可读写 `/api/cases/definitions`
- [x] `npx vite build` 通过
