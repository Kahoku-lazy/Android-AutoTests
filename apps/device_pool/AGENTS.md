# device_pool App AGENTS.md

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.0 · 最后更新：2026-08-21 · v1.0：从已归档 `dev_docs/_archive/后端claude笔记.md` §0️⃣ 模块表迁出并展开。

## 红线（全局索引表 device_pool 行的展开）

| 只做 | 禁止 |
|------|------|
| 设备生命周期：扫描/连接/断开/激活/心跳（30s） | 直接执行用例（那是 test_runner） |
| 占用/释放锁（`lock` / `release`）经 `api.py` | 绕过状态机改设备状态 |

- 设备状态机（ONLINE ⇄ BUSY 等）唯一落点在 `pool.py` / `session.py`，**任何模块（含 test_runner 执行器、AI Tool）占用/释放设备必须走本 App `api.py`**，禁止直接 ORM 改设备状态——否则设备死锁或状态漂移。
- 30s 心跳口径与前端 device-pool 模块一致（前端以心跳判离线），改间隔必须双边同步。

## 本 App 契约（特例 + 真相源）

真相源：`apps/device_pool/urls.py`（10 端点：`scan` / `current` / `heartbeat` / `connect` / `disconnect` / `disconnect-observe` / `activate` / `lock` / `release` / 列表）+ `views.py` + `api.py`。

- 信封走全局标准 `{status, data}`；列表是 device-inspector 模块「设备列表」的数据来源（列表已内嵌 `current` 字段，前端经列表读取）。
- **预留端点**：独立 `current` 端点前端暂未消费（2026-08-21 校验确认），保留路由；前端新增消费时同步本文。
- `api.py` `__all__` 是其他 App 取设备/占设备的唯一入口：test_runner 设备锁、case_manager 调试选设备均经此。

## 本 App 协议要点

无 WS（心跳为 HTTP 轮询端点）。设备交互（ADB/u2）由 `service.py` 本模块编排，禁止被其他 App import。

## 关单附加项（全局清单的 delta）

```
[ ] lock/release 对称：异常路径不泄漏锁（执行结束/超时释放路径验证）
[ ] 状态迁移经状态机，无视图/consumer 直接改状态字段
[ ] 心跳间隔改动已同步前端 device-pool 模块
[ ] 跨 App 调用方（test_runner/case_manager）走 api，无 ORM 写
```
