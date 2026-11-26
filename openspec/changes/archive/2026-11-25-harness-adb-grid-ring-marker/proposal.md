# Proposal: harness-adb-grid-ring-marker

## Why

`adb_screenshot_grid` 是执行模型在「没有文案的控件」上做视觉定位的兜底工具，但它现在只有一种标记形态，实测在同一台 1080×2340 设备、同一个 49×48 px 的右侧箭头徽标上有两个硬伤：

1. **十字臂和目标一样大**：臂长 `max(10, 短边×0.012)` 在 473×1024 返回图上是 10 px，折回设备约 46 px，而目标只有 49 px。5×5 时十字互相重叠，图上糊成一片，只能靠猜。
2. **单一步长使 y 方向必然更粗**：`step` 是归一化值，x 间距 = step×1080、y 间距 = step×2340。默认 0.03 得到 32.4 / 70.2 px，y 比目标高 48 px 还大，**粗估点偏离 24~46 px 时三个候选点全部落空**（占每个周期的 32%）。

实测对照（同一张真机截图）：十字 5×5@0.015 只有 3 点压中且不可判读；**环点阵 5 列×7 行、x 0.02 / y 0.01** 有 4 点压中，目标在圆环里透出来，可以按行列索引直接取坐标并完成点击验证。缺的只是工具支持：环点形态、两轴独立步长、行列索引。

## What Changes

- `adb_screenshot_grid` 新增 `marker`：`"cross"`（默认，行为与现在完全一致）| `"ring"`（空心圆点阵）。
- 新增 `step_y`：y 方向归一化步长，`0` 表示与 `step` 相同（默认值即旧行为）。
- `size` 由只允许 `3 / 5` 放宽到 `3 / 5 / 7`（7 用于纵向覆盖一行以上的搜索窗口）。
- `ring` 形态改用**行列轴标注**（列号在首行上方、行号在首列左侧），不再给每个点写序号；圆环半径按点间距自动收敛，保证环与环不相交、目标能从环心透出。
- 返回体 `marks` 每项增补 `row` / `col`（`index` / `nx` / `ny` 保留），`grid` 回显 `marker` 与生效的 `step_y`。
- 同步 `.agents/docs/engines/ae_harness_tools/ae_harness_tools_domain_tools.md` 的「网格核对」与「视觉定位精度」两处口径。

**BREAKING**：无。默认参数下工具行为、返回字段与坐标语义均不变，只是多出可选字段。

## 关联文档

无 PRD/ARCH 关联：本变更是引擎工具层的标记渲染与入参扩展，属工具链改动，不涉及产品需求与架构分层。

## Capabilities

### New Capabilities

- `harness-adb-grid-marker`: 截屏候选点标记的形态、两轴步长与行列索引契约——决定模型在图上能否辨认「哪个候选点压中了目标」。

### Modified Capabilities

（无 —— 现有 `ai-screen-vision` 约束的是平台侧 `mark_dot` 核对工具与 OCR，`ai-device-action` 约束的是平台侧设备动作，均不覆盖 `engines/ae_harness/tools/adb` 的候选点网格。）

## Impact

- 代码：`engines/ae_harness/tools/adb/tools.py`（`_grid_points` / `_render` / `_annotate` / `_screenshot_with_points` / `adb_screenshot_grid`）。
- 文档：`.agents/docs/engines/ae_harness_tools/ae_harness_tools_domain_tools.md`。
- 工具目录与角色装配：`build_adb_tools()` 名单无变化（仍是同一个工具），`list_tool_catalog()` 由构建器派生，只描述文案变化。
- 调用方：`backend_bridge` 与提示词无需改动；不新增长期单元测试（按 `tests/AGENTS.md` 口径，验证脚本留在 `temps/`）。
- 依赖：无新增（Pillow 已是现有绘制依赖）。
