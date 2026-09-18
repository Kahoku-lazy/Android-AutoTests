## Why

三项实测缺陷：① **z-index 无体系** —— 27 处声明散落在 20 个文件，用了 13 个互不相关的裸值（`0/1/2/3/5/10/20/60/80/100/9990/9991`），没有任何登记，改一处层叠要全仓搜值；② **悬空令牌** —— `case-manager/components/ProjectTree.vue:684` 写 `z-index: var(--case-z-context)`，而该令牌**全仓无声明**（G5 门禁的盲区：不扫 `<style>` 块），于是该属性在 computed-value 阶段失效回落 `auto`，行为与作者意图不符（同类浮层在 `LocatorTree` 里写的是 `80`）；③ **跨模块同名类** —— `.project-list-page` 与 `.project-workspace` 在 case-manager 与 element-locator **各有一份**（scoped 属性目前掩盖了冲突，但同义异义的两个类名是维护陷阱）；④ 孪生组件 `.ex-btn` 规格分叉（case-manager 用字面量、element-locator 用令牌）。

## What Changes

- 在 `tokens.css` 登记 **7 档层叠令牌**（取值与现状**逐一相同**）：`--z-base: 1` / `--z-raised: 2` / `--z-header: 10` / `--z-popup: 60` / `--z-overlay: 80` / `--z-modal-backdrop: 9990` / `--z-modal: 9991`；把全仓与之**精确同值**的 `z-index` 声明替换为令牌（**零视觉变化**）；本轮未纳入档位的单例值（`0/3/5/20/100`）保留字面量并登记
- 修悬空令牌：在 `case-manager/tokens.css` 声明 `--case-z-context: var(--z-overlay)`（对齐同类浮层的 80），使浮层层叠真正生效
- 消除跨模块同名类：把 element-locator 的 `project-list-page` / `project-workspace` 改名为 `locator-project-list` / `locator-project-workspace`（含其模板与 CSS 选择器）
- 收敛 `.ex-btn` 分叉：把 case-manager `ProjectTree.vue` 的规格对齐到 element-locator `LocatorTree.vue` 的令牌写法
- **BREAKING**：无（除悬空令牌修复带来的层叠生效）

## 关联文档

- `dev_docs/DEV_TEST/前端UI风格一致性分析-2026-09.md` §4.6 与 §八·批次 E
- `dev_docs/DEV_TEST/前端UI一致性整改计划.md` 阶段 3 · `establish-zindex-and-name-scope`
- 既有要求：`openspec/specs/frontend-l0-design-tokens/spec.md`（层叠令牌）、`frontend-l2-page-region/spec.md`（模块页根命名）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l0-design-tokens`：新增要求「层叠顺序取自登记令牌」
- `frontend-l2-page-region`：新增要求「模块页根类名带模块前缀且跨模块唯一」

## Impact

- `frontend/src/shared/styles/tokens.css`（7 档层叠令牌）
- 全仓约 20 个文件的 `z-index` 声明改为令牌（精确同值，零视觉变化）
- `frontend/src/modules/case-manager/tokens.css`（修悬空令牌）、`case-manager/components/ProjectTree.vue`（`.ex-btn` 对齐）
- `frontend/src/modules/element-locator/{ProjectList,ProjectWorkspace}.vue`（页根类改名）
- 不影响：未纳入档位的单例 z-index、各浮层的既有层叠次序、接口与数据

## 登记为后续输入

- `report-generator/constants.ts` 死导出、令牌与死 CSS 清退（变更 14 移出部分）→ 另开批次