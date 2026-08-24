# device-pool 模块 CLAUDE.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../CLAUDE.md`；本文只写本模块增量，冲突以全局为准。改 UI 另读 `../../../../dev_docs/05-开发与测试/设计-设备管理前端UI规范与checklist.md`。

## 红线（全局表 device-pool 行的展开）

| 只做 | 禁止 |
|------|------|
| 设备生命周期管理 UI（连接/锁定/释放/30s 心跳轮询） | 设备物理操作 / 执行调度 / 快照（那是 inspector） |

- **设备状态只有 2 种（ONLINE / BUSY）**，离线即删、无 OFFLINE 墓碑态；状态标签渲染错误会导致页面误导用户。
- 执行引擎占用识别走 `RUNNER_OCCUPIED_PREFIXES`（`ai_agent` / `runner-` / `task-` / `run-`），禁止硬编码判断。

## 本模块契约

- 8 端点：`/devices`（列表）· `/devices/scan` · `/devices/{serial}`（连接，body `{ activate }`）· `/devices/{serial}/activate` · `/{serial}/lock`（body `{ locked }`）· `/{serial}/release` · `/{serial}/disconnect` · `/devices/heartbeat`；DTO 类型在 `@/shared/types/device`

## 本模块特殊布局/样式（`constants.ts` 为唯一真相源，禁止散落魔法字符串）

- 心跳轮询 `HEARTBEAT_INTERVAL = 30000`（30s，改这里即改全局行为）
- 表格列 `COLUMNS`、筛选 `FILTER_TABS`、状态文案 `DEVICE_STATUS_MAP`、连接类型 `CONNECTION_TYPE_LABEL`

## 本模块协议要点

- 心跳轮询由 `useHeartbeat.ts` 统一管理，禁止组件内另起轮询定时器。

## 关单附加项（全局清单的 delta）

```
[ ] 状态渲染只认 ONLINE/BUSY 两态；占用前缀判断走 constants
[ ] 心跳轮询 30s 间隔未改；无组件内自建轮询
[ ] 连接/锁定/释放/断开全走 api.ts 8 端点，无旁路
[ ] 改 UI 已对照 dev_docs/05 设备管理规格
```
