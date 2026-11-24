# device_pool · 设备池写库边界

> 归属模块：`backend/apps/device_pool` ｜ 类型：模块功能开发说明
> 代码真相源：`backend/apps/device_pool/{urls,views,api,manager,pool,models,contracts}.py`
> 上级约束：`backend/AGENTS.md` ｜ 模块索引：`backend/apps/AGENTS.md`

## 职责

设备池的**登记、占用与锁**：`dp_devices`（设备）、`dp_device_locks`（锁记录）。
10 个端点，全部挂在 `/api/devices/` 下（带尾斜杠）。

设备的**物理连接与操作已全部下沉 `engines/device/`**；本 App 只管「谁占着哪台设备」。
`pool.py` 的 `DevicePool` 只保留**当前激活设备指针**（`current_serial`），
连接类型与地址直接从 `Device` 表读，不再进程内缓存。

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `""` | 设备列表 |
| POST | `scan/` | 扫描新设备 |
| GET | `current/` | 当前激活设备信息（**有副作用，见下**） |
| POST | `heartbeat/` | 心跳 / 锁过期回收 |
| POST | `<serial>/` | 连接 + 采集信息 + 自动激活（`mode=observe` 时置观察占用） |
| POST | `<serial>/disconnect/` | 断开（释放锁、删记录） |
| POST | `<serial>/disconnect-observe/` | 轻量断开（不删记录，释放观察占用） |
| POST | `<serial>/activate/` | 切换当前激活设备 |
| POST | `<serial>/lock/` | 加锁占用 |
| POST | `<serial>/release/` | 释放占用 |

## 写库边界：现状 vs 目标

**⚠️ 现状（2026-11-23，对本仓库代码实测）**：写库**尚未**收敛到 `api.py`。
`api.py` 目前只有读与占用相关的 7 个函数（`get_online_devices` / `list_devices` / `ensure_device` /
`acquire_device` / `release_device` / `release_device_locks_for_device` / `use_device`），
而真正的 ORM 写点在 `manager.py`（20 处 `.save()` / `.delete()` / `objects.create|update`），
View 经 `manager` 的 `registry` / `state_machine` / `detector` / `serializer` 触达写库。

**目标态**（`openspec/changes/converge-device-pool-writes-to-api`，**尚未合并**）：
写库层收敛到 `api.py`，`manager` / `registry` / `state_machine` 降为**内部实现**，View 一律经 `api.py`。

> 本文件写在收敛**之前**，因此上面「现状」一列会随该变更合并而过期。
> 合并后请按目标态重写本节，并删掉现状说明——不要两份并存。

## 当前激活指针语义

- `pool.py::device.current_serial`：**进程内**的单值指针，`switch_to(serial)` 切换，`remove_device(serial)` 在断开时清空。
- 它**不落库**，重启即空；每台设备的连接信息与状态以 `Device` 表为准。
- `GET /current/` 读的是这个指针；指针为空直接返回空信息。

## GET 的副作用（如实登记）

`GET /api/devices/current/` **不是一个纯读接口**：为了拿分辨率和前台应用，它会**连一次 ADB**，
并对同一设备 **10 秒内复用上次结果**，避免轮询把请求线程拖在 shell 上。指针指向的设备记录不存在时降级为空信息。

## 锁模型

`dp_device_locks` 关键字段：`device` / `user_id` / `lock_type` / `status`（`active|released|expired`）/
`locked_at` / `released_at` / `timeout_seconds`（默认 300）/ `release_reason` / `last_heartbeat`。

- `lock_type` 实际取值含 `user`、`process`、**`observe`**（字段注释只写了前两个，观察锁是后加的）。
- 释放在 `manager`：`release_device_locks_for_device()` 按设备批量释放，并写 `release_reason`
  （`LockReleaseReason`：`MANUAL` / `DISCONNECT` 等，见 `contracts.py`）。
- 心跳巡检回收过期锁（`last_heartbeat` 参与判定）。

## observe 链

- `POST /api/devices/<serial>/` 带 `mode=observe` → `state_machine.occupy_observe(dev, user_id)`：
  置 `BUSY` + `occupied_by`，并建 `lock_type="observe"` 的锁。
- `POST /api/devices/<serial>/disconnect-observe/` → `state_machine.release_observe(dev)`：
  只释放观察占用，**不删设备记录**。
- `OBSERVE_LOCK_TTL = 1800`（`manager.py:44`）：关页/崩溃没释放时，由心跳在 30 分钟后兜底回收。
  （来源：`fix-observe-leak` —— 原实现不建锁，导致设备永久 BUSY。）

**待裁决**：`observe` 占用与普通 `user` 锁的互斥关系、以及 `disconnect-observe` 与 `disconnect`
在清 `current_serial` 上的行为差异，代码里没有统一注释说明；改动这块前先确认语义，不要凭直觉。

## 关单附加项

```
[ ] python manage.py check
[ ] python manage.py makemigrations --check
[ ] python -m pytest -c tests/pytest.ini tests/device -q
[ ] python manage.py spectacular --validate
[ ] 涉及跨模块 → python utils/gen_arch_stats.py --check-boundaries
```

全局关单清单见 `backend/AGENTS.md` §3。
