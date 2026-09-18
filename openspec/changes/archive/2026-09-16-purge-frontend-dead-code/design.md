## Context

- `AppTable.vue:13` 定义 `striped`（默认 false），:121 映射为 EP 的 `:stripe="striped"`；调用方写裸 `stripe` 时该 attr 未被声明 → 透传到 `el-table` 的也是 `striped`（EP 不认）→ 斑马纹不渲染。`device-pool/index.vue:156` 与 `report-generator` 三处均正确使用 `:striped`。
- 零引用判定：在 `frontend/src` 的 `.vue` / `.ts` 中检索文件基名（`AgentModelConfig` / `WorkflowFileBrowser`），命中数分别为 0。
- **本轮事故**：清退 `constants.ts` 死导出时，我按 `;` 判定声明结束，但本项目不使用分号，导致从第一个匹配项起吞到文件末尾。已 `git checkout --` 完整恢复，并把该项移出本变更范围（见 proposal 的"移出范围"段）。

## Goals / Non-Goals

**Goals**

- 恢复 element-locator 页面元素表的斑马纹
- 删除两个零引用组件
- 零行为变更（除斑马纹恢复）

**Non-Goals**

- 不清退 `constants.ts` 死导出（需不依赖分号的删除策略，另开批次）
- 不清退令牌与死 CSS 规则
- 不改 `AppTable` 自身 prop 契约

## Decisions

**D1 `stripe` 改为 `:striped="true"`，不给 `AppTable` 加 `stripe` 别名**
理由：`striped` 是既定契约且已有 4 处正确消费；加别名会让同一语义有两套写法。

**D2 零引用组件直接删除，git 历史即恢复方式**
理由：规格要求无引用文件不得留在源码树。

**D3 `constants.ts` 清退**从本变更移除**（而不是用有缺陷的脚本硬做）**
理由：验证手段（构建）不足以在脚本误删时保护文件；应有确定性更强的策略（按顶层声明边界删除、删除后比对导出数与引用数、并先备份）。宁可不做，不做坏。

## Risks / Trade-offs

- [删除 `WorkflowFileBrowser.vue` 后若存在外部引用会在构建期报错] → 构建即验证；已确认 0 引用
- [斑马纹恢复改变 element-locator 表格观感] → 这是修复目标，非副作用

## Migration Plan

1. prop 修复 → 删文件 → 构建验证
2. 回滚：文件删除用 `git checkout`；prop 用 `git revert`；无数据迁移

## Open Questions

（无）