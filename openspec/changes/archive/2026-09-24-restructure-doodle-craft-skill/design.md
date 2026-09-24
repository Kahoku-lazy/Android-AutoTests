## Context

技能的加载机制是三层渐进披露：**元数据（name + description）永远在上下文；SKILL.md 在触发时进上下文；references 按需读**。当前 Doodle Craft 的 SKILL.md 与三个参考都不小（`components.md` 311 行 / `tokens.md` 218 行 / `layout.md` 136 行），入口自身还夹带了模块色表、图标映射、自检清单。触发一次就要背一整套，而真要改某个组件时又得翻到 `components.md` 的中段。

同目录族里 `animal-island-ui-style` 已经给出了这个仓认可的答案：入口做路由，类目拆文件，硬规则钉在入口。

## Goals / Non-Goals

- Goals：入口能在 150 行内说清「用哪套、去哪查、别踩什么」；一个组件类目一个文件，改什么读什么；所有现存内容零丢失；链接全可达。
- Non-Goals：不改令牌值、不改平台代码、不新增视觉规则、不生成英文版、不复制技能副本到别处。

## Decisions

### D1：目录结构对齐 `animal-island-ui-style`

```
doodle-craft/
├── SKILL.md                     # 入口：口径 / 场景 / 一段话 / 令牌指针 / 组件目录 / 硬规则 / 自检
├── README.md                    # 技能是什么、被谁加载、目录结构、维护规则
└── references/
    ├── vue-project.md           # 场景一：平台内 Vue 页面/组件（真实代码）
    ├── standalone-html.md       # 场景二：单文件 HTML 预览稿 / 原型
    ├── tokens.md                # 视觉皮肤层检索表（含动效与降级）
    ├── page-layout.md           # 页面层：L0–L5 / 骨架 / 滚动 / 宽度 / 变体
    ├── known-gaps.md            # 已知缺口 + 已退役写法（别照抄）
    └── components/              # 组件规格，按类目拆（8 个文件）
        ├── general.md           # 按钮族 / 标签
        ├── layout.md            # 页头 / 面包屑 / 侧栏 / 分区 / 标签页
        ├── cards.md             # 钉板卡 / 撕纸卡 / 指标卡 / 涂鸦条目卡
        ├── form-controls.md     # 输入 / 选择 / 开关 / 分段控件
        ├── data-display.md      # 表格皮肤 / 表纸 / 分页
        ├── overlays.md          # 弹窗 / 抽屉 / 确认框
        ├── feedback.md          # 三态 / 消息提示
        └── decorative.md        # 纸面涂鸦 / 微旋转 / 图钉胶带
```

替代方案（保留单个 `components.md`）被否：那正是当前"定位靠翻文件"的病根，且与同族技能结构不一致。

### D2：入口只做路由与铁律，不复述值

`animal-island-ui-style` 的做法是**令牌值刻意不写进技能**，只给分组与指针（它的值在库的设计文档里）。Doodle Craft 的对应事实是：**值在 `tokens.css`，检索表在 `references/tokens.md`**。因此入口的令牌段只写三件事：分组有哪些、什么时候用哪个文件、值以谁为准。

例外：**8 个模块色**保留在入口。理由与 animal 入口里保留 `50px pill` / `12px 圆角` 同理——它是"记错了就明显穿帮"的语义映射，且是其它技能（如 `frontend-change-plan`）跨技能对齐的对象。

### D3：硬规则从"自检清单"升级为入口的编号铁律

原入口把约束放文末自检清单里（勾选项语气）。改成 `animal-island-ui-style` 的 **Hard rules（违反即 bug）** 编号列表，并把机械门禁（`npm run lint:styles` 的 G1–G5）与人工判定项分开表述：能被工具判定的写进铁律并注明门禁编号，判不了（如"卡片网格禁止 0° 排排坐"）注明由人复核。自检清单保留，但只做"提交前逐条过一遍"的操作化短表。

### D4：页面层与组件层不再同名

原 `references/layout.md`（页面骨架）与新的 `references/components/layout.md`（布局类组件）同名会让人按错文件。页面层那份改名 `page-layout.md`，并在入口参考表里把两者的一句话职责写清楚。

### D5：新增 `known-gaps.md` 而不是留在组件规格里

「已知缺口登记」与「已退役写法」是**反面清单**（别照抄），和"照抄对象"（组件规格）混在一个文件里，实测最容易被误读成规格的一部分。独立成文件后，入口的硬规则段可以明确指过去。

### D6：单文件 HTML 场景写成"可复制配方"

`references/standalone-html.md` 不写空话，直接给：`:root` 令牌子集模板（从 `tokens.css` 抄值）、页面骨架 HTML 结构、四类卡片的 CSS 配方、以及两条实测踩坑（`var()` 未声明会让 SVG 描边整条消失；`.main__body` 用 `flex:1 1 0 + min-height:0` 后滚动条落在这层、window 不再滚动——截图/调试时要找对滚动容器）。

## Risks / Trade-offs

- **文件数变多**（3 → 11）：换来"改什么读什么"。代价是新增规则时要判断归属，入口的参考表就是归属判据。
- **拆文件可能丢内容**：以"逐条迁移、宁可重排不可删减"为验收口径，任务清单里对每个文件列出必须保留的条目。
- **技能名与触发描述不动**：`name: doodle-craft` 与 description 保持，避免影响其它技能与既有触发。

## Migration Plan

纯文档重排，无运行时迁移。落地即生效（技能文件被读取时生效）。仓内对 `doodle-craft` 的引用均为技能名引用，无需改动。

## Open Questions

（无）
