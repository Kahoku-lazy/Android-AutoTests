## 1. 代码

- [x] 1.1 `engines/ae_harness/tools/adb/tools.py`：`_marker_style` 把 `cross` 归一为 `ring`、缺省 `ring`；`adb_screenshot_grid` 的 `marker` 缺省改 `ring`，docstring 同步；验证：`python -m` 跑 `temps/` 脚本断言 `marker="cross"` 与缺省都返回 `grid.marker == "ring"`
- [x] 1.2 `_annotate` 删除十字分支，改为圆环（单点大环+中心点、多点小环+序号）；`_render` / `_screenshot_with_points` 内部形态改为 `point` / `ring`；验证：真机出图只有圆环、无十字
- [x] 1.3 `adb_screenshot` 的 `marks` 多标记走圆环加序号，不再出现十字；验证：同 1.2 的截图 marks 场景

## 2. 提示词与发布

- [x] 2.1 备份角色 `202611169yh` 的旧提示词到 `temps/`，把「3×3 网格 / 十字准星 / 序号」改为「环点阵 / 行列号 / 点数与两轴步长」；验证：DB 里 `ring` 出现、`十字` 消失
- [x] 2.2 将 workflow 9 置回 draft 并 `publish_workflow` 生成新 release；验证：最新 release 的执行者 prompt 含 `ring`、不含 `十字`，且 `version` 递增

## 3. 文档与门禁

- [x] 3.1 更新 `.agents/docs/engines/ae_harness_tools/ae_harness_tools_domain_tools.md` 的「网格核对」与「视觉定位精度」两处口径为环点阵唯一形态；验证：文档不再出现 `cross` 作为可用形态
- [x] 3.2 跑 `python -m scripts.docstrings check`、`python -m scripts.check_engines_agents_style`、`ruff check engines/ae_harness/tools/adb/tools.py`；验证：0 error / 0 违规

## 4. 真机验收

- [x] 4.1 在设备 `R5CT62RH88F` 上分别用缺省与 `marker="cross"` 出图，人工核对圆环、行列号、目标透出；验证：截图存 `temps/` 并肉眼确认
- [ ] **skipped（2026-11-27 需求方决定：真机验证不做）** 4.2 新建一条 SOP 任务确认报告里是环点阵（不是旧十字）；验证：报告截图人工核对，旧报告不作要求
