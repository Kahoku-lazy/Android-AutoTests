## Context

现状：`marker` 缺省 `cross`，执行者提示词（角色 `202611169yh`）第 104–105 行仍写「3×3 网格、9 个带序号的十字准星」，SOP 任务绑 workflow 9 的 release v1 快照，因此模型每次显式传 `marker="cross"`。环点阵代码已存在（`_annotate_rings`、`step_y`、行列号），只差默认值和提示词接线。

## Goals / Non-Goals

**Goals:**

- `adb_screenshot_grid` 只画空心圆环点阵，`adb_screenshot` 的多标记也不再出现十字。
- 旧调用 `marker="cross"` 不报错，按环点阵渲染。
- 执行者提示词切换为环点阵，并发布 workflow 9 新 release。

**Non-Goals:**

- 不改坐标换算、返回体的 `index/nx/ny/row/col` 契约。
- 不改 `size` 只允许 3/5/7、两轴步长语义。
- 不回改历史报告里的截图。
- 不改验收者提示词。

## Decisions

### 决策 1：废弃别名而不是拒绝 `cross`

`_marker_style` 把 `"cross"` 归一为 `"ring"`，`marker` 缺省 `"ring"`。旧提示词/旧 release 重跑时仍传 `cross`，工具继续可用，只是图上不再有十字。

备选：直接删 `marker` 参数会让旧任务重跑直接 TypeError；拒绝 `cross` 会让旧任务报错。均否决。

### 决策 2：`adb_screenshot` 的 marks 改为圆环加序号

`_annotate` 删除十字绘制分支，统一画空心圆环：单点大环 + 中心点，多点小环 + 序号。`style` 只保留 `point`（截图 marks）与 `ring`（点阵）两种内部形态，模型侧不再看到 `cross`。

### 决策 3：提示词与 release 一起换

提示词是模型行为的实际开关。只改代码默认值，模型仍会按旧提示词显式传 `cross`；只改角色提示词，SOP 仍绑 release v1。因此：改角色提示词 → 将 workflow 9 置回 draft → `publish_workflow` 生成 v2 → 新任务使用 v2。重跑旧任务仍复制旧 release，靠决策 1 的别名保持可用。

### 决策 4：视觉验证用真机截图

工具渲染属像素级行为，单测价值低。用真机 `R5CT62RH88F` 调一次 `adb_screenshot_grid`（缺省参数与 `marker="cross"` 各一次），把 PNG 存到 `temps/` 人工核对：只有圆环、无十字、行列号各一组；验证完删除脚本。

## 模块防火墙自检

- 跨 App import：无新增；工具在 `engines/ae_harness`，不 import backend。
- 写库：代码零写库；角色提示词与 release 属运营配置，用一次性脚本更新并备份旧提示词到 `temps/`。
- DB：无迁移。
- 前端：不动。

## Risks / Trade-offs

- **[旧任务重跑体验变差]** → 旧提示词按「序号」选点，环点图只有行列号；返回体仍带 `index`，模型可据 `marks` 把序号映射到行列。接受，重跑旧任务本身就是低频操作。
- **[发布失败]** → workflow 已 published 时 `publish_workflow` 会拒绝；脚本先把 `release_state` 置回 draft 再发布，失败则保留旧 release 与旧提示词，不影响存量任务。
- **[只影响新运行]** → 历史报告里的截图不会重绘；需在交付说明里写清。

## Migration Plan

- 代码发布后新运行即环点阵；旧 `cross` 调用自动按环点。
- 提示词更新后发布 workflow 9 v2；单智能体直接读角色提示词，SOP 新任务读 v2。
- 回退：还原 `tools.py` 与提示词备份，发布 release 不可删但可继续用旧版本跑旧任务。
