## Why

`adb_screenshot_grid` 的十字形态在真机报告里仍以「3×3 井字」出现：工具默认 `marker="cross"`，执行者提示词也明确教「9 个带序号的十字准星」，模型逐次显式传 `marker="cross"`。十字臂与目标同宽时会遮住小控件，空心圆环点阵才是要采用的核对形态。2026-11-25 的 `harness-adb-grid-ring-marker` 只新增了 `ring` 可选值，没有切换默认与提示词，于是本次要真正落地「只用环点阵」。

## What Changes

- `adb_screenshot_grid` 的 `marker` 缺省改为 `ring`，只渲染空心圆环点阵；不再绘制任何十字。
- `marker="cross"` 保留为**已废弃别名**，收到时按 `ring` 渲染，保证旧提示词/旧任务重跑不报错。
- `adb_screenshot` 的 `marks` 多标记改画圆环加序号，不再出现十字。
- 执行者提示词（角色 `202611169yh`）把「3×3 网格 / 十字准星 / 序号」改为「环点阵 / 行列号 / 点数与两轴步长」。
- 发布 workflow 9 新 release，使 SOP 任务拿到新提示词；旧报告图不回改。

**BREAKING**：`marker="cross"` 不再产生十字（视觉行为变更），但调用不报错。

## 关联文档

无 PRD/ARCH 关联：引擎截屏工具的标记渲染与提示词口径调整，不改产品流程与坐标契约。

## Capabilities

### New Capabilities

<!-- 无新增能力。 -->

### Modified Capabilities

- `harness-adb-grid-marker`: 标记形态由「十字或环点、缺省十字」改为「只用环点、缺省环点」，并明确废弃别名的处理与点数上限。

## Impact

- 代码：`engines/ae_harness/tools/adb/tools.py`（`_render` / `_annotate` / `_screenshot_with_points` / `marker` 校验）。
- 配置：`AIRole` 角色 `202611169yh` 的系统提示词；workflow 9 发布新 release。
- 文档：`.agents/docs/engines/ae_harness_tools/ae_harness_tools_domain_tools.md`。
- 报告：只影响新运行；历史 HTML 内的截图保持原样。
