---
name: quality-retrospective-case-manager
description: case-manager 质量回顾：漏测根因、Bug 根因、系统性改进措施
metadata: 
  node_type: memory
  type: project
  originSessionId: 921bc6d5-c227-471c-a6f0-467192f54b52
---

case-manager 模块暴露出开发→审查→测试→验收全链路的系统性问题。

## 漏测根因

**测试思维 = 组件存在检查，不是用户操作流验证。**

| 我写的（错误） | 应该写的（正确） |
|--------|---------|
| `.is_visible()` | 填表→保存→退出→断言不弹对话框 |
| 检查元素存在 | 模拟完整用户流程→验证最终状态 |

**三个系统性原因**：
1. 没按 PRD 用户故事写测试（每条 US 有验收标准，测试应该 1:1 映射）
2. 只测单组件，不测组件间数据同步（树计数 vs 面板列表）
3. 只测正向路径，不测取消/失败/边界分支（每个操作至少 3 条路径）

## Bug 根因

发现的 5 个 Bug 全是"读代码看不出问题，跑起来才有问题"：
- **时序 Bug**：`router.replace` 在 `initialForm` 重置之前
- **交互缺失**：`goToElementLocator` 无确认直接跳转
- **数据流断裂**：`remove()` 只刷新列表不同步树
- **类型转换**：HTML `:value` 默认字符串
- **设计偏差**：孤儿用例 (directory_id=null) 无处理

**Code Review 盲区**：逐行读代码无法发现跨组件同步、时序依赖、类型隐式转换。

## 系统性改进（4 项铁律）

1. 🔴 **每条 PRD 用户故事至少 3 条测试**（正向 + 取消 + 边界/错误）
2. 🔴 **Code Review 必须查数据流一致性**（写操作是否更新了所有相关视图？）
3. 🔴 **E2E 测试必须可降级执行**（无设备时跑 UI 层，不全跳过）
4. 🔴 **每次修 Bug 必须补测试**（复现 → 修复 → 回归 → 截图留痕）

**关联**：[[test-plan-workflow]] [[ui-test-screenshot-on-failure]] [[prd-first-workflow]] [[agent-must-be-used]]
