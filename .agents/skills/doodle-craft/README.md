# Doodle Craft 技能

一套写给 AI coding agent 的前端 UI 技能：让 agent 在**本仓（Android-AutoTests）**里按 Doodle Craft 主题做页面、做组件、改样式——而不是每次重新发明一套视觉。

风格一句话：**极简几何 · 粗线涂鸦 · 彩绘卡通 · 手稿纸**。暖白纸面、墨色粗线、硬边纸片、八支模块彩笔。

## 这是什么

- 它是本平台前端的**默认设计方案**：需求方没有主动提出新设计时，一律按本技能落地。
- 它不是设计稿，也不是组件库：真实样式由 Element Plus 全局覆盖（`frontend/src/style.css`）+ 共享皮肤（`shared/styles/workbench-theme.css`）+ 共享组件（`shared/components/**`）提供，本技能负责**说清口径、指到落点、钉住红线**。
- 令牌值的唯一真相源是代码：`frontend/src/shared/styles/tokens.css`。本技能只做检索表与规则，**值以代码为准**。

## 谁读它

| 读者 | 读什么 |
| --- | --- |
| 本仓的 AI agent（DSH / Claude Code 等） | 触发时读 `SKILL.md`，按需读 `references/**` |
| 人（review 技能、对齐口径） | 本 README + `SKILL.md` + `references/` |

技能放在 `.agents/skills/doodle-craft/`，由 agent 运行时的技能目录加载（本仓唯一落点，不复制到 `engines/ai/skills/` 或 `dev_docs/`，避免副本漂移）。

## 目录结构

```
doodle-craft/
├── SKILL.md                     # 入口：默认口径 / 场景 / 一段话风格 / 令牌指针 / 组件目录 / 硬规则 / 自检
├── README.md                    # 本文件
└── references/
    ├── vue-project.md           # 场景一：平台内 Vue 页面与组件（真实代码）
    ├── standalone-html.md       # 场景二：单文件 HTML 预览稿 / 原型
    ├── tokens.md                # 视觉皮肤层检索表（色板 / 字号 / 圆角 / 阴影 / 动效 / EP 映射）
    ├── page-layout.md           # 页面层：L0–L5 归属 / 骨架 / 纸面 / 滚动 / 宽度 / 页面变体
    ├── known-gaps.md            # 已知缺口 + 已退役写法（别照抄的清单）
    └── components/              # 组件规格，按类目拆分
        ├── general.md           # 按钮族（EP + wb-btn + DoodleBtn + ConfirmButton）、Tag
        ├── layout.md            # 页头 / 面包屑 / 侧栏 / 分区 / 标签页
        ├── cards.md             # 钉板卡 / 撕纸卡 / 指标卡 / 涂鸦条目卡
        ├── form-controls.md     # 输入 / 选择 / 开关 / 分段控件
        ├── data-display.md      # 表格皮肤 / 表纸 / 分页
        ├── overlays.md          # 弹窗 / 抽屉 / 确认框
        ├── feedback.md          # 加载 / 失败 / 空三态、消息提示
        └── decorative.md        # 纸面涂鸦 / 微旋转 / 图钉胶带
```

## 怎么用

1. 先读 `SKILL.md` 的「默认设计口径」与「先选场景」，确定是平台内 Vue 开发还是单文件 HTML。
2. 按场景进 `references/vue-project.md` 或 `references/standalone-html.md`。
3. 具体到某个组件/视觉属性时，才去读对应的 `references/components/*.md` 或 `references/tokens.md`——**改什么读什么**，不必整包读完。
4. 收尾走 `SKILL.md` 的「提交前自检」，机械项交给门禁：`cd frontend && npm run lint:styles`。

## 维护规则

- 改令牌值：**先改 `tokens.css`**（唯一真相源），再同步 `references/tokens.md`；两者冲突时以代码为准。
- 新增组件规格：写进 `references/components/` 对应类目；没有合适类目时先在本 README 的目录结构里登记新类目，再建文件。
- 新增设计规则：只有当需求方**明确提出**新设计时才允许；落地后必须登记回 `references/tokens.md` + `tokens.css`，涉及组件或版式时同步对应参考文件。
- 仓内其它技能（`frontend-change-plan`、`vue-frontend-check`）以**技能名**引用本技能，不深链内部文件——重组 references 不会断链，但仍应在重组后跑一次链接自检。
