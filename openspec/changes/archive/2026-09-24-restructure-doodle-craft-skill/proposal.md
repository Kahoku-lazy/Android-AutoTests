## Why

Doodle Craft 技能目前是「一个大入口 + 三个大参考」：`SKILL.md` 把风格口径、参考索引、工作流、模块色、图标映射、自检清单全塞在一起；`references/components.md` 一份文件装了 23 个组件的规格（311 行）。结果是：

- **入口太重**：SKILL.md 触达即全量进上下文，真正要用的时候又不够用（组件规格还在另一个 300 行文件里）。
- **定位靠翻文件**：改一个按钮要和改一个表格卡读同一份文件；按需加载无从谈起。
- **格式不对齐**：工作区里 `animal-island-ui-style` 已经跑通了「入口选场景 → 按类目查组件参考」的分层写法（SKILL.md 104 行 + 9 个类目文件），Doodle Craft 是同一类"设计系统型技能"，却没有这层结构。

## What Changes

- **SKILL.md 改成入口**：默认设计口径 → 先选场景（平台内 Vue / 单文件 HTML）→ 一段话说清风格 → 设计令牌（只给分组与指针，不复述值）→ 组件目录（类目表 + 选型判据）→ 硬规则（违反即 bug）→ 提交前自检。目标 ≤ 150 行。
- **`references/components.md` 按类目拆成 8 个文件**：通用 / 布局 / 卡片 / 表单控件 / 数据展示 / 浮层 / 反馈与三态 / 装饰。内容逐条保留，只重排归属与标题层级。
- **新增两个场景参考**：`references/vue-project.md`（平台内真实代码：四层不越界、改哪里、验证命令）与 `references/standalone-html.md`（单文件 HTML 预览稿/原型：令牌模板 + 骨架 + 反例）。
- **`references/layout.md` 更名 `references/page-layout.md`**：与新的 `references/components/layout.md`（布局类组件）区分开，页面层与组件层不再同名。
- **新增 `references/known-gaps.md`**：把原先夹在组件规格里的「已知缺口登记」与「已退役写法」归位——这两张表是"别照抄"清单，和被照抄的规格放一起容易被误当规格。
- **动效与降级**并入 `references/tokens.md` 的动效段（原 `components.md` §四），不再单独漂在组件文件里。
- **新增 `README.md`**：说明这是什么技能、被谁加载、目录结构、以及「改令牌先改 `tokens.css` 再同步本技能」的维护规则。
- **非目标**：不改任何平台代码（`frontend/src/**` 零改动）；不改令牌值；不改验收契约；不生成英文版（本技能入口保持中文）；不复制副本到 `engines/ai/skills/` 或 `dev_docs/`。

## 关联文档

- 格式参照：`engines/ai/skills/animal-island-ui-style/`（SKILL.md + README.md + references）
- 令牌唯一真相源：`frontend/src/shared/styles/tokens.css`
- 编码规范：`frontend/AGENTS.md`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）—— 本次只重构技能文档的组织形式，不改变任何产品行为或验收标准。

## Impact

- 技能：`.agents/skills/doodle-craft/` 内部文件重组（SKILL.md 重写、README.md 新增、references 由 3 个文件变成 11 个）。
- 引用面：仓内对 `doodle-craft` 的引用均为**技能名引用**（`frontend-change-plan` / `vue-frontend-check` / `DEV_DOCS_README.md`），无文件级深链，故拆分不会断链；技能自身内部的 `references/*.md` 链接随本次一并更新。
- 平台：零代码改动、零迁移、零接口变更。
