## Context

实测：`frontend/DESIGN_SYSTEM.md` 不存在；全仓 18 处提及中 7 处属**活文档指针**（doodle-craft 6 + checklist 1），其余落在 `openspec/changes/archive/**` 与另一个 in-flight 变更中，属历史记录。`tokens.css` 维度标题 9 处，序号为 一/二/三/四/五/六/七/**六**（重复）。

## Goals / Non-Goals

**Goals:** 活文档指针全部指向存在的来源；段号唯一且与文件头清单一致。
**Non-Goals:** 不重建 `DESIGN_SYSTEM.md`（内容已并入 checklist，重建会造出第二真相源）· 不追改历史记录 · 不改任何令牌与选择器。

## Decisions

### D1 · 改指针而非重建文档
`vue-frontend-check/references/checklist.md:179` 明确记载「原 DESIGN_SYSTEM.md 已归档并入」，故指向它就是指向原内容的现址。

### D2 · 段号改为「八」而非合并两段
「布局尺寸」（`--size-*` 骨架尺寸）与「布局」（分栏宽度 / 行比例 / 断点）职责不同，合并需搬动声明；本变更只改标题文本，零风险。

## 模块防火墙自检

| 红线 | 本变更 |
|------|--------|
| 跨 App import / 写库 / 前端直连数据库 | 不涉及（仅 Markdown 与 CSS 注释） |
| 新增依赖 | 无 |

## Risks / Trade-offs

- [checklist 以后搬家会再次悬空] → 指针统一写全路径，便于检索
- [修注释时误改字符] → 首轮把「阴影」误写成「阵影」，同轮自查发现并修正（`typo_fixed=true`）

## Migration Plan

1. 逐条替换 7 处活指针 + 2 处 `tokens.css` 标题/清单
2. 复核：活文档内 `DESIGN_SYSTEM` 命中 = 0；维度序号唯一
3. 回滚：改动集中在 5 个文件，`git revert` 单次提交

## Open Questions

- 无