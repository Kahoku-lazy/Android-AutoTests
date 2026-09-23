## 1. PRD-03 头部与页面骨架节

- [x] 1.1 头部：版本 v1.0 → v1.1（2026-09-22，状态「刷新」）；后端「7 端点」→ 8 端点；算法指针 `algorithms/xpath.py`（分区与 XPath）→ `algorithms/element_layers.py`（两级分组与主定位）+ `algorithms/xpath.py`（XPath）；规格真相源补 `device-inspector-layers` / `device-inspector-snapshots` / `element-layering`。验证：头部四行指针均可在仓库定位
- [x] 1.2 工具条口径改「N 元素（当前分组）」+ legacy 提示；**删除筛选栏整条**；工作区由「三栏：页面分区列 → 元素档案表 → 手机屏幕」改为「两栏：左＝元素分组 + 元素档案表面板，右＝手机屏幕」；样式指针「筛选栏」→「分组筹码」。验证：`grep 筛选` 在 PRD 命中 0
- [x] 1.3 骨架常驻清单去掉筛选栏与页面分区列、改「元素分组列表」；保存键双重前提 → 「两个入口冻结」；响应式改「工作区折成上下两行」。验证：与 `store.ts` 的两个冻结开关、`index.vue` 的 `.workspace` 栅格一致

## 2. 获取快照 / 历史快照与回看

- [x] 2.1 「获取」后动作改「自动取一次分层数据」；复位清单改「勾选集合 / 当前分组 / 内联重命名」；指针 `applySnapshot` → `applyLayers`。验证：与 `store.capture` / `applyLayers` 一致
- [x] 2.2 历史快照：总数口径改「保留上限 10 + 总数如实 + 一键清空（二次确认 / 不可恢复 / 空列表禁用）」；回看改「取分层数据」；出口补 `/layers/` 与 `/clear/`，指针 `apiGetSnapshot` → `apiGetLayers` / `apiClearSnapshots`。验证：与 `api.ts` / `SnapshotListDrawer.vue` 一致
- [x] 2.3 列表契约：`limit` 上限 100 → 服务端按保留上限 10 封顶；补「保留近十条」与「一键清空」两条业务规则；排序补「同一时间再按 ID 倒序」。验证：与 `api.SNAPSHOT_RETENTION` / `list_snapshots` / `clear_snapshots` 一致

## 3. 「结构分析」节重写为「元素分组（分层查询）」

- [x] 3.1 产品功能一节：标题改名；模版改为「左＝元素分组列表（五项固定顺序、无「全部」复位项、每项带计数）+ 元素档案表（15 列）」；业务逻辑 14 条改写（分组联动 / 两组写入选中的入口 / 名称口径 / 主定位 / 交互标志七项 / 缩略图 66px / 勾选跨分组 / 固定 14 行 / 空态一句 / 无 WebView 提示 / 分组色圈选 / 首列冻结 / legacy 标注）。验证：每条都能指向 `constants.ts` / `StructureAnalysisPanel.vue` / `store.ts` 的具体行
- [x] 3.2 API 契约改为「分层查询」：入口与 8 个查询参数、6 条业务规则（不落库不碰设备 / 只查本人 / 摘要全量与 total_matched / 缺省不截断且显式按 500 封顶 / 降级 source=legacy / 非法值 400）、返回顶层字段、5 类校验。验证：与 `views.snapshot_layers` / `api.list_layers` 一致
- [x] 3.3 数据表单写明输入 `nodes_json`（降级 `dump_json.elements`）与不写库，并如实标注**前端未使用服务端筛减参数**（本地按分组过滤）。验证：`store.fetchLayers` 不传 params

## 4. 保存 / 回看 / 删除 / 跨模块 / 重试节

- [x] 4.1 「保存到元素定位」与「已保存页面只读回看」两节各加**冻结说明**（入口禁用、点按只提示原因、不发请求；端点与代码路径保留）。验证：与 `store.ts` 的 `SAVE_TO_ELEMENTS_FROZEN` / `SAVED_PAGE_FROZEN` 及 `constants.ts` 原因文案一致
- [x] 4.2 回看态口径改为「分组列按后端摘要 + 无指标列 + 六列口径」，「不调分析端点」→「不调分层端点」；删除节与重试节的「分区」表述改「分组」。验证：`grep 分区` 在 PRD 命中 0
- [x] 4.3 跨模块节的 `api.py __all__` 计数按当前白名单修正（11 个函数 + 1 个常量）。验证：`grep -c` 与 `api.py:7-21` 一致

## 5. 测试一节刷新

- [x] 5.1 开头「现状」段：改为「接口层 + 灰盒单元层 + 灰盒集成层 + 前端 P0 四层；端到端层为 0」
- [x] 5.2 「元素分组（分层查询）」测试节整体重写：13 条 UI 场景 + 7 条业务功能场景 + 对应规格（`device-inspector-layers` · `element-layering` · `device-inspector-page`）+ 四条现存覆盖 + 新缺口（canvas 绘制无自动化）
- [x] 5.3 「怎么跑这些测试」改为当前可执行命令（接口 YAML 14 条 / 灰盒单元 / 灰盒集成 / 前端 P0 4 文件 19 例）
- [x] 5.4 附录「已知缺口」：第 8 条重写为当前资产与三块空白；新增第 9 条（快照详情端点已无前端调用方）与第 10 条（「保存到元素定位」前端冻结而规格仍按可用描述）

## 6. 门禁与归档

- [x] 6.1 `npx openspec validate align-inspector-prd-with-layers --strict`；验证：通过（`skip_specs: true`，specs 跳过）
- [x] 6.2 改动面核对：只改 `dev_docs/ARCH_PRD/PRD-03-设备检查器.md`；验证：见 §7 留痕
- [x] 6.3 归档：`npx openspec archive align-inspector-prd-with-layers -y`；验证：归档成功、`npx openspec validate --specs --strict` 仍全绿

## 7. 验收留痕（apply 期实测）

- **取证方式**：刷新前先派一个只读子代理产出「设备检查器当前行为事实清单」（7 节、每条带 `路径:行号`），再由父 Agent 对关键结论逐条 grep/read 复核（`constants.ts` 五项分组与 14 行、`StructureAnalysisPanel.vue` 15 列与缩略图格、`store.ts` 的两个冻结开关与 `retry()` 四个来源、`views.snapshot_layers` 的 8 个查询参数、`api.list_layers` 的返回字段）。PRD 中每处新表述都对应这些证据。
- **刷新后的自查**：`grep '分区|筛选|固定 7|7 行|指标列|WebView|analyzeSnapshot|applyFilters|986|8 列|applySnapshot|已显示最近'` 在 PRD 中**只**命中三处刻意保留的否定式表述（「工具条上没有『结构分析 / 返回元素列表』」×2、「不判定也不提示 WebView」×1）。
- **改动面**：`git status` 显示本次除变更工件外只动了 `dev_docs/ARCH_PRD/PRD-03-设备检查器.md`；但该文件与 `ARCH-平台总体架构.md` 都是**未跟踪**文件，故 `git diff` 不体现其变化，只能靠 read 核对。
- **实施中修正的自身错误**：首轮 §页面骨架 的多行替换因漏掉行首缩进而失败，已按 read 到的原文重做；一次读取工具返回的行数组与文件行号错位，导致我一度以为 §业务功能侧 被清空 —— 改用 `grep` 复核后确认内容完好，后续一律按 `l.number` 打印。
- **既有噪声**：`apps/device_inspector/urls.py:1` 的 docstring 仍写「6 端点」（实际 8 条路由）。那是**代码注释**，本变更为纯文档变更、不改代码，登记在报告里另议。
