## Why

上一单 `fix-dangling-snapshot-media` 用「删除时判定引用」止住了继续丢，但**两个模块的资产仍然共命**：元素定位的 `Page.screenshot_path` / `Element.thumbnail_path` 依旧指向检查器的 `inspector/**` 路径。只要还有别的删除/清理路径（或人工清盘），同样的问题会以另一种形式复现；而判定逻辑本身也要求检查器读对方的数据表。

**根治办法（C 方案）**：导入时把媒体**复制**到元素定位自有目录，让元素定位记录不再引用检查器的媒体路径。此后：

- 删快照按原规则清理 `inspector/**`（不再需要为别人的页面「留一手」），跨模块的隐式耦合消失；
- 元素定位的资产与检查器快照各自独立演进（检查器将来换存储布局也不影响已保存页面）。

## What Changes

- `apps/element_locator/api_snapshot.py` 的 `import_snapshot_page`：写入页面/元素记录前，把整屏截图与元素缩略图复制到 `locator/pages/<page_id>/` 下，记录里存**副本路径**
  - 截图副本：`locator/pages/<page_id>/screen.png`（沿用既有「已有页面不覆盖截图」规则，只在本次填充时复制）
  - 缩略图副本：`locator/pages/<page_id>/el_<resource_id 安全前缀>_<key 哈希8>.png`，文件名由 upsert 键 `(page, resource_id, bounds)` 派生 —— 与元素行 1:1，重复导入不会把 A 行的文件覆盖成 B 的内容
  - 源文件不存在时**保留原路径**并写告警（MUST NOT 伪造一个不存在的副本路径）
- 保留 `fix-dangling-snapshot-media` 的「删除时判定引用」逻辑：它继续保护**存量**记录（仍指向 `inspector/**` 的那批），新导入的记录不再命中该判定
- **BREAKING**：无（对外契约不变：`import_snapshot_page` 的入参、返回值、端点与响应形状均不动）

## 明确移出本变更范围

- **不做成批存量回填**（不写迁移、不扫描历史行）：已有页面的路径保持原样，仍由「删除保全」+ 前端「失效媒体降级」兜底；但同一页面**再次导入**时会就地自愈（源文件存在则复制并改指副本）。若需一次性回填，另开管理命令（需部署环境能访问 `MEDIA_ROOT`）
- 不恢复已丢失的 16 张缩略图 / 2 张截图（源文件已不存在，无法复制）
- 不做孤儿副本回收（重复导入后不再被引用的旧副本会留在磁盘；登记为后续项，与「媒体回收」一并做）
- 不改 `get_page_full` / 端点契约（副本路径对检查器透明）

## 关联文档

- 需求编号：`PRD-03-设备检查器`
- 上一单（本单的前置）：`2026-09-21-fix-dangling-snapshot-media`（删除保全 + 前端降级）
- 承接的能力：`device-inspector-snapshots`（媒体生命周期契约的唯一归属）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `device-inspector-snapshots`: 新增「导入到元素定位时复制媒体到元素定位自有目录」（补齐该契约的另一半：先把资产复制过去，而不是靠删除时留手）

## Impact

- 后端 1 文件：`apps/element_locator/api_snapshot.py`（新增复制步骤与命名派生）
- 测试：扩展 `tests/graybox/integration/test_inspector_snapshot_media.py`（+3 例：路径改指自有目录 / 删源快照后副本仍可用 / 源缺失保留原路径）
- 规格：`device-inspector-snapshots` +1 条要求（3 个场景）
- 磁盘：每次导入多一份截图 + 每个元素一份缩略图（元素定位自有副本）
- 数据迁移：无
- 兼容：检查器与元素定位的既有接口、页面回看链路不变