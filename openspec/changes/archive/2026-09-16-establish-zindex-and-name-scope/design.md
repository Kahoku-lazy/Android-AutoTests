## Context

- 现状层叠值分布（27 处）：`1`×6、`2`×6、`10`×3、`60`×3、`9990`、`9991`、`80`、`100`、`20`、`3`、`5`、`0`，另有 1 处悬空令牌。
- 悬空令牌机制：`var(--case-z-context)` 无声明 → computed-value 阶段失效 → `z-index` 回落 `auto`（与"整条声明被丢弃"不同，见变更 4 的结论）。
- 同名类：`project-list-page` / `project-workspace` 在 case-manager 与 element-locator 各一份；`<style scoped>` 的 `[data-v]` 属性目前避免了实际串扰，但两个模块的同名类语义不同，是维护陷阱（一旦某处改为非 scoped 即泄漏）。
- `.ex-btn` 分叉：`ProjectTree.vue:557` 与 `LocatorTree.vue:326` 两份规格（前者部分用字面量）。
- 动机见 `proposal.md`。

## Goals / Non-Goals

**Goals**

- 层叠有 7 档登记令牌，精确同值替换（零视觉变化）
- 消除悬空层叠令牌，让 `case-manager` 上下文菜单层叠真正生效
- 消除跨模块同名页根类
- `.ex-btn` 孪生规格收敛到令牌来源

**Non-Goals**

- 不重新设计层叠次序（只登记现状档位；未纳入档位的单例保留）
- 不改各浮层的 `position` / `inset` 等几何
- 不动 element-locator 的 `file-view`（该名未被别的模块占用）
- 不提级"element-locator 页根统一"以外的事项（变更 13 已完成 `locator-workbench`）

## Decisions

**D1 层叠令牌取现状精确值（零视觉变化）**
`--z-base:1` / `--z-raised:2` / `--z-header:10` / `--z-popup:60` / `--z-overlay:80` / `--z-modal-backdrop:9990` / `--z-modal:9991`。理由：建立体系不应顺带改变层叠结果；改值需视觉确认，另议。
备选：把 `60/80` 合并为一档 —— 否决，会改变浮层相对次序。

**D2 悬空令牌用声明而非改成字面量**
在 `case-manager/tokens.css` 声明 `--case-z-context: var(--z-overlay)`。理由：保留模块语义名，同时对齐同类浮层（`LocatorTree` 用 80），并让"模块令牌引用全局令牌"的口径成立。
备选：直接写 `z-index: 80` —— 可行但丢掉语义名。

**D3 改名 element-locator 的页根类而非 case-manager 的**
理由：变更 13 已为 element-locator 引入 `locator-` 前缀的模块根类，方向一致；case-manager 的 `case-` 前缀体系更完整。

**D4 孪生 `.ex-btn` 以 element-locator 版本为基准**
理由：该版本已全部使用令牌（`--app-radius-sm` / `--paper`），符合规格；case-manager 版本含字面量。

## Risks / Trade-offs

- [批量替换 `z-index` 可能命中非层叠声明] → 替换限定在 `z-index` 值且仅映射精确同值项；脚本用 UTF-8 安全 API 且内容为纯 ASCII
- [页根类改名若遗漏某处选择器会导致样式失效] → 两个文件内该类的出现处全部改；tasks 含改名后检索与新名生效断言
- [`.ex-btn` 对齐会改变 case-manager 树内按钮观感] → 方向是"向令牌基准收敛"；tasks 含计算样式断言

## Migration Plan

1. 先登记令牌与修悬空引用，再做批量替换，最后改名与对齐
2. 回滚策略：纯样式/类名改动，回滚即 `git revert`；无数据迁移

## Open Questions

（无）