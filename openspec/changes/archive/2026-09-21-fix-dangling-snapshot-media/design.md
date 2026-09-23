## Context

- 现状链路（读码 + 实测）：导入时元素定位照抄媒体路径（`apps/element_locator/api_snapshot.py` 的 `import_snapshot_page` 写 `Page.screenshot_path` / `Element.thumbnail_path`）；删除快照时 `apps/device_inspector/api.py:143-183` 的 `delete_snapshot` 调 `service.delete_snapshot_files`（`apps/device_inspector/service.py:186-207`：`unlink` 截图 + `rmtree` 缩略图目录）；两个模块的资产因此共命。
- 实测损失（dev 库 + 媒体目录）：`MEDIA_ROOT=D:\Govee\data\uploads`（仓库外）；`inspector/thumbs/20260908_180319_745832/` 与 `inspector/shots/capture_20260908_180319_745832.png` 均已不存在，且该 `ts` 的快照行已删除；**16/32 个元素、2/5 个页面的媒体文件缺失**。
- 前端现状：`ScreenshotView.vue` 的 `<img>` 只有 `@load`，`v-if="screenshotPath"` 使其在文件 404 时仍走「有截图」分支 → 图片 0 尺寸、画面空白且无空态；`StructureAnalysisPanel.vue` 的缩略图 `<img>` 与放大预览 `<img>` 都没有 `@error` → 浏览器破图图标。
- 既有语义：`delete_snapshot_files` 是「真删」，本身不需要改；要改的是**何时调用**。
- 跨 App 约束：`apps/AGENTS.md` §1.1「跨 App **读** Model ✅，写必须走对方 api.py」——本变更只读 `element_locator` 的 `Page` / `Element`。

## Goals / Non-Goals

**Goals:**

- 删快照不再破坏元素定位仍在引用的截图 / 缩略图
- 已失效的媒体在检查器里表现为可读的空态 / 占位，而不是空白与破图
- 用一条集成测试把「保留 / 清理 / 判定失败」三条路径钉住

**Non-Goals:**

- 不恢复已丢失的 16 张缩略图 / 2 张截图（不可能：快照已删）
- 不在导入时复制媒体（C 方案，见 D2 取舍）
- 不改模型的媒体字段与历史数据
- 不改删除的确认语义（仍走 `ElMessageBox.confirm`）

## Decisions

**D1 引用判定的归属：在 `device_inspector` 内直接读 `element_locator` 的 Model**
写一个私有函数 `_media_referenced(screenshot_path, thumbs_dir_rel)`，查 `Page.objects.filter(screenshot_path=...)` 与 `Element.objects.filter(thumbnail_path__startswith=...)`。依据：跨 App 读 Model 是允许的；判定逻辑只有两行查询，为它引入 element_locator 的新公开读函数属于过度设计。
备选：在 `apps/element_locator/api.py` 新增 `is_media_referenced()` → 否决（当前规模不划算），但若判定将来变复杂（多前缀、多目录、需事务锁）应提升为对方 api。

**D2 判定粒度：整批判定，不做逐文件判定**
截图或缩略图目录**任一**被引用 → 整批保留。理由：导入是整批进行的（同一 `ts` 的截图与缩略图一起被同一页面引用），实测数据也如此；逐文件判定要在删除时按文件名逐个比对引用，复杂度高而收益极小。代价：可能多留少量未被单独引用的缩略图（可接受，且不丢失任何资产）。
备选：逐文件判定 → 否决：需要把 `thumbs` 目录里每个文件与所有 `Element.thumbnail_path` 求差集，收益仅是磁盘，成本是每次删除的 N 次查询与更复杂的测试矩阵。

**D3 判定失败 → 不删任何文件（fail-closed），并把判定放在所有删除动作之前**
顺序：先算 `thumbs_dir_rel` → 再 `_media_referenced()`（可能抛错）→ 未引用才 `delete_snapshot_files()` → 最后 `snapshot.delete()`。判定抛错时异常向上传播成 500，文件与记录都还在。
备选：判定失败按老行为删除 → 否决：与「错误不应默默忽略」冲突，且媒体删了不可恢复。

**D4 前端降级复用既有空态骨架，但换成失效文案**
截图失效时走 `ScreenshotView` 既有的 `.no-signal` 空态（含两组光环与图标），标题改「截图已失效」、说明改「该页面的截图文件已不存在…」，与「暂无页面快照」区分；缩略图失效直接复用既有的 `sap-thumb-empty`（`—`）；放大预览失效时在预览区插入占位块，其余字段照常渲染。
备选：新增一套独立的「已失效」组件 → 否决：同一骨架两套实现，且视觉会分叉。

## 模块防火墙自检

- 跨 App import：`device_inspector` 读 `element_locator` 的 **Model**（`Page` / `Element`）——属规则允许的「跨 App 读」；**不写**对方任何表，也 **不 import** 对方的 `service` / `views` / 内部实现
- 写库收敛：快照记录的删除仍在本模块 `api.py`；本变更不新增写路径、不改 element_locator 的任何数据
- 前端不直连数据库：不涉及
- HTTP 出口：不变（不新增端点、不改信封、不改路径）
- 迁移：零（不改模型字段）
- 共享层：不动 `shared/**`；只改 `device-inspector` 的两个展示组件

## Risks / Trade-offs

- [保留被引用媒体后磁盘不释放] → 这是本变更的**有意取舍**（宁可不释放，也不破坏他人资产）；如需回收，应另开「引用计数 / 孤儿媒体清理」变更
- [判定漏判导致仍误删] → 判定用精确匹配 `screenshot_path` + 前缀匹配缩略图目录；集成测试覆盖两条路径；真机再验一次「删快照后页面图仍在」
- [路径分隔符 / 大小写差异导致前缀匹配失败] → 路径全部由本模块写入（`inspector/thumbs/<ts>/...`），统一用 `/`；测试里显式断言前缀命中
- [前端 `@error` 在 jsdom 不可靠] → 前端以真机走查验收（页面 39 的媒体已失效，是现成样本），不引入脆弱的 jsdom 断言
- [判定查询影响删除性能] → 两条带索引前缀的查询（`Element.thumbnail_path` 无索引，但数据量为单页元素级），实测删除路径耗时无感

## Migration Plan

1. 后端加 `_media_referenced()` 与 `delete_snapshot` 的顺序调整 → 集成测试三例
2. 前端两处 `@error` 降级 → 真机：失效页面（#39）与正常快照（#345）各走一遍
3. 门禁：`manage.py check` + `ruff` + `pytest`（新增测试）+ `lint:styles` + `vite build` + `vitest`
4. 归档：新 capability `device-inspector-snapshots` 首次建主规格 + `device-inspector-page` 写回 1 条新增要求
5. 回滚：单文件后端改动 + 两处前端改动，`git revert`；无数据迁移

## Open Questions

（无 —— C 方案的取舍已登记为 Non-Goal，另开变更时再决策）
