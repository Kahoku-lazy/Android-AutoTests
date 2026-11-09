## Why

现有表纸为了“无网格”，把所有行列线都写成 `transparent`：表头靠 2px 墨线压住，行与行之间没有任何分隔。数据一多，行与行糊在一起；表头也因为带底色 + 2px 粗线，显得比内容还重。需求方给了「Key contacts」参考：表头无底色、用 1px 细线分行、单元格留白更大，读起来是“一条条笔迹行”。

## What Changes

- 表头：去掉底色，1px `ink 14%` 细线收底；字号仍 12px，字重 700 → **600**，颜色改次要色，字距 0.08em。
- 数据行：新增 1px `ink 8%` 行分隔线（不用模块色、不用白色）；单元格上下内距加大到 `--app-space-md`，行更高。
- 行悬停：`ink 3%` 浅底。
- 表头/行线仍由共享皮肤（`workbench-theme.css` 的 `.ac-table`）唯一定义，模块不得覆写。

## 关联文档

- 参考图：用户提供的「Key contacts」列表卡片。
- 本条修改 `frontend-l4-data-surface` 中「Tables draw no visible grid lines」的要求：从“禁止可见行列线”改为“允许 ink 系 1px 行线、禁止列线与模块色线”。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `frontend-l4-data-surface`：表格行分隔与表头排版要求调整。

## Impact

- 前端：`shared/styles/workbench-theme.css` 的 `.ac-table` 表头/单元格/悬停规则（`wb-shell` 与 `workflow-workbench` 两个作用域）。
- 后端 / 接口：无改动。
