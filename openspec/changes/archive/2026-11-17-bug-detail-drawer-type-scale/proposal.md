# BUG 单详情抽屉：字号收成 16 / 14 两档

## Why

BUG 单详情抽屉里字号是四档混排：编号 14、分类/状态标签 12、标题 24、「错误内容」小标题 14、错误正文 12，同一屏里既有比正文还小的标签，也有比抽屉标题大一号的标题，视线没有落点。需求方要求收成两档：**头部行、标题、小标题都 16，其余 14**；「标记已解决 / 忽略」这类按键字号不动。

## What Changes

- `BUG-0066` 那一行（编号 + 分类标签 + 状态标签）字号统一到 16px。
- 单据标题（`UI 自动化任务失败：Android-UI-SOP`）从 24px 收到 16px。
- 「错误内容」这类小节标题从 14px 提到 16px。
- 错误正文（`<pre>`）从 12px 提到 14px。
- 元信息块（关联任务 / 任务状态 / 创建时间 / 解决时间）保持 14px；抽屉标题「BUG 单详情」本来就是 16px，不动。
- 按键（`DoodleBtn`：标记已解决 / 忽略 / 重新打开）字号不动。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `bug-ticket-management`：新增「BUG 单详情抽屉的字号两档」要求。

## Impact

- 前端 `bug-manager`：`components/BugDetailDrawer.style.css`（五处 `font-size`）。
- 不动模板、不动数据、不动接口；抽屉标题与按键不受影响。
