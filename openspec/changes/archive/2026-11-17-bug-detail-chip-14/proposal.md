# BUG 单详情：分类/状态标签回到 14px

## Why

上一变更把头部行整行（编号 + 分类标签 + 状态标签）统一提到 16px。实看下来标签字形只有 4~5 个字，16px 时描边内的留白被撑满，两个标签像"贴纸"一样压过编号与标题。需求方要求：`BUG-0066` 保持 16，**「UI 自动化」「待处理」两个标签改回 14**。

## What Changes

- `.bug-badge` / `.bug-status` 字号 16px → 14px（`--app-size-sm`）。
- `BUG-0066` 编号保持 16px；单据标题、小节标题保持 16px；元信息、错误正文、按键保持 14px/自身规格。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `bug-ticket-management`：修改「BUG 单详情抽屉的字号两档」（标签从 16 改回 14）。

## Impact

- 前端 `bug-manager`：`components/BugDetailDrawer.style.css`（一处 `font-size`）。
- 不动令牌、不动模板、不动接口。
