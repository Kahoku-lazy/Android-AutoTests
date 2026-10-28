## Context

标题拼装已经离开组件，落在 `helpers/task-detail.ts` 的 `roundTitleLead` / `roundTitleTail`：前段给「第 2 次 执行模型」，尾段给「：动作」；组件在类别后渲染 `round.role` 徽章。序号由模板算 `roundOffset + roundIndex + 1`，即**该用例分页后的位置**，执行轮与验收轮都占号。

## Goals / Non-Goals

**Goals:**

- 标题不再有角色类别文字，只剩「序号 · 标记 · 角色徽章 · 结果徽章 · 动作」。
- 序号只标执行步骤；同一执行步骤的重试共号，换页不跳号。
- 两角色的徽章一眼可分（底色不同），且各有一个固定前置标记。

**Non-Goals:**

- 不改报告接口字段、事件聚合与折叠/分页行为。
- 不改 PASS / FAIL 徽章的配色与语义。
- 不给验收轮编号，也不把验收结果并入执行步序号。

## Decisions

**1. 序号按 `step_seq` 去重，而不是按轮次位置。**

同一执行步骤重试两次会产生两轮，位置法会给 1、2 两个号，读起来像两个步骤。改为：在该用例内遍历执行轮，按 `step_seq` 首次出现顺序发号（同一 `step_seq` 复用号）；`step_seq` 缺失的旧数据退化为按轮次发号。跨分页不变，因为号在整份用例的轮次列表上算。

**2. 固定标记放标题起始，与序号同处一个文本串。**

`roundTitleLead(round, execNo)` 一次给出 `「2. ➡️ 」` / `「✅ 」` / `「第 2 次 ✅ 」`：序号、重试、标记三者的相对次序只在一处决定，模板不必再拼。标记用 emoji（`➡️` / `✅` / `❌`），与用户给定的格式一致；余下元素（角色徽章、结果徽章）仍是 DOM，便于各自上色。

**3. 角色配色取既有语义令牌，并与该轮左侧强调色同源。**

执行 `--c-ai`（紫）、验收 `--c-workflow`（蓝）。验收轮的 `--round-accent` 一并由 `--c-report` 改为 `--c-workflow`，避免同一角色在左侧竖线与徽章上出现两种颜色。PASS 徽章仍是 `--app-status-success-bg`（淡绿）、FAIL 仍是 `--c-runner`（淡红），与角色色互不混淆。

**4. 结果徽章保留在角色徽章之后。**

标题形如「✅ `verifier_role` PASS：前台为 govee」：`✅` 是快速扫读的标记，PASS/FAIL 徽章是规格里已经存在的判决标注，两者并存是需求方给出的目标格式。

## 模块防火墙自检

- 只改 `frontend/src/modules/task-list` 与其 `helpers/`、`tests/task-list/`；无跨模块 import。
- 组件只保留「把 `execNo` 传进 helper、渲染徽章」，发号算法在 helper。

## Risks / Trade-offs

- [emoji 在 Windows/Chromium 之外渲染不一致] → 只作前置标记，语义仍由徽章与 PASS/FAIL 承担；缺字形不影响判读。
- [一屏徽章变多] → 已省掉「执行模型/验收模型」六个字与每行的模型名，净宽仍变短。
- [旧数据 `step_seq` 缺失] → 退化为按轮次发号，不会出现重复号或空号。
