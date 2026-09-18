## Context

- 模块 tokens.css 现状：`ai-assistant` / `case-manager` / `workflow` 有；`element-locator` / `dashboard` / `device-pool` / `device-inspector` / `report-generator` 没有。`main.ts` 已注册前三个。
- `element-locator` 内联令牌：`--locator-header-icon-end: var(--color-indigo-84)` 在 `ProjectList.vue:73-75`（`.project-list-page`）、`ProjectWorkspace.vue:115-…`（`.project-workspace`）、`LocatorFileView.vue:154-156`（`.file-view`）各一次 —— 三个页根类互不相同，**没有共同模块根类**，这是必须先补的前提。
- `case-manager` 内联情况：`--case-icon-accent: var(--color-teal-67)` 在 3 个页根的 `.case-workbench` 块各一次（可安全上收）；`--case-sheet-*` 在 `.case-sheet__table` 上（表元素局部）；`--case-menu-shadow` 在浮层元素自身（Teleport 到 body 后模块根不再是祖先，**必须**留在元素上）。
- 动机见 `proposal.md`。

## Goals / Non-Goals

**Goals**

- `element-locator` 拥有模块 tokens.css 与统一模块根类
- `case-manager` 的 `--case-icon-accent` 只声明一次，落在模块 tokens.css
- 两个模块的模块级令牌全部有唯一落点

**Non-Goals**

- 不改 `--case-*` 的**色相**（现为 blue 族而模块色是 teal）—— 属设计决策，见「Open Questions」
- 不迁移 `--case-sheet-*` 与 `--case-menu-shadow`（元素局部登记是正确形态）
- 不处理 `report-generator` / `dashboard` 的同类碎片化（登记进变更 14）
- 不改任何颜色值（零视觉变化）

## Decisions

**D1 为 `element-locator` 引入统一模块根类 `locator-workbench`**
理由：模块令牌需要一个稳定的作用域选择器；现状 3 个页根类各不相同，无法用同一选择器覆盖。`case-manager`（`case-workbench`）与 `ai-assistant`（`ai-workbench`）已是此形态，本变更是对齐。
备选：在 tokens.css 里写 3 个页根类的选择器列表 —— 否决，会让"模块根类"这一概念在该模块缺位，后续新页面仍需记得加入列表。

**D2 `--case-icon-accent` 上收到 tokens.css，`--case-menu-shadow` 留在元素上**
理由：前者是页面级场景令牌（消费点在页头图标块，属于页面根之内）；后者是浮层元素自身登记，Teleport 后模块根不再是祖先，上收会导致变量丢失。

**D3 `main.ts` 注册顺序紧跟其他模块 tokens.css**
理由：保持既有注册块的可读性；模块 tokens.css 只做作用域声明，顺序不影响层叠。

## Risks / Trade-offs

- [给 3 个页根补类名可能与既有 CSS 选择器冲突] → `locator-workbench` 是新名字，全仓无既有引用；tasks 含检索确认
- [迁移后若消费点不在模块根之内会失效] → 两个模块的消费点都在页根之内（页头图标块是页根子节点）；tasks 含浏览器断言解析成功
- [漏删内联声明会留下重复声明] → tasks 含逐处检索

## Migration Plan

1. 先建 element-locator tokens.css 并在 main.ts 注册，再补类名，最后删内联声明；
2. case-manager 直接上收；
3. 回滚策略：纯令牌落点调整，回滚即 `git revert`；无数据、接口与路由迁移

## Open Questions

- `--case-*` 家族的**色相**问题（值取自 blue 族而模块色 `--c-case` 是 teal）属设计选择：改为 teal 会改变用例表表头与分隔线观感。本变更**不擅自改动**，留待确认后另开变更