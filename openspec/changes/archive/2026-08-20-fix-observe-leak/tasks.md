## 1. 后端

- [x] 1.1 `service.py`：`OBSERVE_LOCK_TTL=1800` 常量；`occupy_observe` 建 observe 锁；`heartbeat_sync` 过期 observe 锁回收；验证 `python manage.py check && python -m ruff check apps/device_pool/service.py`
- [x] 1.2 新增 `tests/device_pool/test_observe_lock.py`（django_db）：occupy 建锁、release_observe 释放、runner 前缀保护、heartbeat 过期回收；验证 `python -m pytest tests/device_pool/test_observe_lock.py --nomigrations -q`

## 2. 前端

- [x] 2.1 `useDebugDevice.ts`：`onUnmounted` 钩子（best-effort disconnect）；验证 `npm run typecheck` 我方区域零错误 + `npm run build`

## 3. 回归

- [x] 3.1 全量后端：`python -m pytest -m "unit or integration" --nomigrations -q`（基线 317 + 5 = **322 passed**）；前端 `npm run build` 通过
- [x] 3.2 真机：连接调试设备（BUSY/admin）→ **SPA 侧边栏导航离开** → 观测到 `POST /disconnect-observe` 请求 → 设备恢复 **ONLINE** ✅（注：page.goto 整页导航不触发 keep-alive 钩子，非真实用户路径；后端 30min 超时兜底覆盖崩溃场景）
