# device-inspector 模块 AGENTS.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。

## 红线（全局表 device-inspector 行的展开）

| 只做 | 禁止 |
|------|------|
| 快照抓取与回看（dump/OCR、筛选后保存） | 元素资产持久化 / XPath 生成 / OCR（后端算法职责）；无 WS 截图流 |

- 截图流已快照化，**禁止恢复 WS 截图流**（全局通道收敛硬约束）。
- 保存到元素定位走 `save-elements` 端点，由后端落库，本模块不做元素资产持久化。

## 本模块契约

- 抓取：`POST /inspector/capture`（body snake_case：`serial` / `method`）
- 快照：`GET /inspector/snapshots`（`offset` / `limit`）· `GET /inspector/snapshots/{id}` · `GET /inspector/snapshots/{id}/analyze` · `DELETE /inspector/snapshots/{id}/delete` · `POST /inspector/snapshots/{id}/save-elements`
- 结构分析（只读，纯规则分区）：`GET /inspector/snapshots/{id}/analyze`（展示层不碰 HTTP，经 store `analyzeSnapshot`）
- 页面回看（只读）：`GET /inspector/pages/{pageId}`
- 跨模块：`GET /devices`（device-pool 设备列表）

## 本模块协议要点

- 模块状态集中在 `store.ts`（Pinia store `device-inspector`）。
- 设备占用判定走 `EXEC_PREFIXES`（与 device-pool 的 `RUNNER_OCCUPIED_PREFIXES` 同口径，改动须两处同步）。

## 关单附加项（全局清单的 delta）

```
[ ] 无新增 WS 通道；截图走 REST 快照
[ ] 保存到元素定位经 save-elements，由后端落库
[ ] capture body snake_case；快照分页 offset/limit
[ ] EXEC_PREFIXES 与 device-pool 占用前缀口径一致
```
