## Why

需求方要「新建模型」表单按两张参考图（按钮五态 / 输入四态）重做外观：按钮改成手绘虚线描边 + 填充态实线硬影，输入框改成浅墨虚线边 + 小字 label。这套外观与仓内主线皮肤（`DoodleBtn` 实线硬影 + `el-input` 实线墨边）不是同一套语言，且虚线在 `doodle-craft` 里原本只准许 `AgentRouteCard` 一个组件使用，直接落地会同时踩中规则与门禁。

需求方已明确授权：**把这类样式收敛成一个新的设计分类 `Sketched UI Kit`，虚线白名单从「只属于助手角色卡」扩到「控件级：按钮描边态 + 输入框」，并留档**。

## What Changes

- 技能新增分类：`.agents/skills/doodle-craft/references/components/sketched-ui-kit.md`（按钮五态 + 输入四态 + label + 用法 + 反模式）。
- 技能入口同步改规则：`SKILL.md` §线型规则 增加「手稿控件皮肤」为第二个合法虚线来源，判据加一条，硬规则 11 增补「已登记的分类是唯一例外」；`README.md`、`references/tokens.md` §1.6/§1.18、`components/general.md`、`components/form-controls.md` 同步。
- 新样式表 `frontend/src/shared/styles/sketched-kit.css`：作用域根类 `.sketch-kit`，提供按钮五态、输入框四态、label、`.sketch-form` / `.sketch-field` 骨架；`main.ts` 引一次。
- 令牌：`tokens.css` 增加 `--comp-kit-*` 颜色 / 几何原语；虚线边框组合值声明在 `sketched-kit.css` 的 `.sketch-kit` 作用域内（虚线口径只允许由白名单文件声明）。
- 门禁：`frontend/tests/check-dashed-whitelist.mjs` 的 OWNERS 增加 `shared/styles/sketched-kit.css`，头注释与报错文案同步。
- 首个消费方：运营后台「新建模型」抽屉（`modules/ops-console/model-configs.vue`）整体切到 kit。

**BREAKING**：无。未挂 `.sketch-kit` 的页面外观零变化；`DoodleBtn` 组件本身不改（kit 通过作用域覆盖）。

## Capabilities

### New Capabilities

- `frontend-doodle-sketched-ui-kit`: 手稿控件皮肤分类——作用域、按钮五态、输入四态、虚线白名单与门禁、可达性与减动效。

### Modified Capabilities

- 无（既有 `frontend-doodle-button` / `frontend-l3-container` 等规格描述的仍是主线皮肤，本分类不改它们）。

## Impact

- 前端：`shared/styles/sketched-kit.css`（新增）、`main.ts`（一行 import）、`shared/styles/tokens.css`（`--comp-kit-*` 段）、`modules/ops-console/model-configs.vue`、`tests/check-dashed-whitelist.mjs`。
- 技能文档：`SKILL.md`、`README.md`、`references/tokens.md`、`references/components/{general,form-controls,sketched-ui-kit}.md`。
- 后端 / 接口 / 数据：无改动。
- 回退：删 `sketched-kit.css` + `main.ts` 的 import + `model-configs.vue` 的 `.sketch-kit` 类回主线；门禁 OWNERS 去掉一行；`tokens.css` 的 `--comp-kit-*` 段可整段删除（无其它消费方）。
