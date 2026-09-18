## Context

- 令牌刻度（`tokens.css`）：`--radius-sm: 4px 8px`、`--radius-md: 6px 10px`、`--radius-lg: 8px 14px`、`--radius-pill: 4px 10px 6px 8px`、`--radius-table: 4px 10px`；另有 `--comp-note-radius: 2px`、`--comp-sheet-radius: 2px 6px 2px 4px`、`--el-border-radius-small: 3px 6px`。
- 实测分布见 `proposal.md` 的 Why；关键点：CSS 的 2 值写法 `A B` 展开即为 `A B A B`，故 `4px 8px 4px 8px` 与 `var(--app-radius-sm)` **渲染完全相同**。
- `--app-radius-pill` 在 modules 内零引用，而 `999px` 有 19 处 —— 令牌存在但无人消费。
- 动机见 `proposal.md`。

## Goals / Non-Goals

**Goals**

- 可见盒子的圆角全部来自不对称规格令牌；对称字面量与等价展开形式清零（登记例外除外）
- 激活零消费的 `--app-radius-pill`

**Non-Goals**

- 不改 `50%` / `2px` / 细线图形量 / `0` 重置 / 方向性几何 / 登录页独立视觉
- 不统一 `WorkbenchHeader` 的 `8px 16px 6px 14px` 与 `SkeletonCard` 的 `3px 5px 3px 5px`（已不对称，档位统一另议）
- 不改布局、色彩、阴影与动效

## Decisions

**D1 等价展开形式映射到对应令牌（零视觉变化）**
`4px 8px 4px 8px → var(--app-radius-sm)`、`6px 10px 6px 10px → var(--app-radius-md)`、`3px 6px 3px 6px → var(--el-border-radius-small)`、`2px 6px 2px 4px → var(--comp-sheet-radius)`。
理由：渲染完全相同，属纯"第二真相源"消除。

**D2 对称单值按**幅度最近**映射到不对称令牌**
`4px` / `6px` → `--app-radius-sm`（4px 8px）；`8px` / `10px` / `12px` → `--app-radius-md`（6px 10px）；`14px` / `18px` → `--app-radius-lg`（8px 14px）。
理由：令牌按尺寸命名，取最近档不改变"这个盒子大概多圆"的观感，只把对称改成手绘不对称。
备选：全部映射到 `--app-radius-sm` —— 否决，会把大卡片压得过方。

**D3 `999px` 一律映射到 `--app-radius-pill`**
理由：设计语言明文点名 999px；`--app-radius-pill` 就是为此登记的，且当前零消费。

**D4 `!important` 后缀原样保留**
理由：这些位置的 !important 是覆盖 Element Plus 皮肤所必需（见变更 4 的结论），删除会改变生效结果。

## Risks / Trade-offs

- [`8px` 有 31 处、跨 workflow 节点/树/菜单等，改为 `6px 10px` 后形状变化] → 属"对称→不对称"的目标方向；tasks 含计算圆角断言与目视建议
- [批量替换可能命中非声明位置] → 替换限定在 `border-radius` 声明的值内、跳过注释与含 `var()` 者；脚本用 UTF-8 安全 API 且内容为纯 ASCII（吸取变更 12 的编码事故教训）
- [`2px` 被误改] → 映射表显式排除 `2px`；tasks 含 `2px` 计数不变的断言

## Migration Plan

1. 先做零视觉变化的 ① 类，再做 ② 类，最后复查保留项计数未变
2. 回滚策略：纯样式改动，回滚即 `git revert`；无数据、接口与路由迁移

## Open Questions

（无）