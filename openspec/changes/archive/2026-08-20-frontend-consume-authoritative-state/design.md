## Context

后端 REST 列表已下发 `state`（Step 5）；前端在 `taskUtils` 渲染路径再推导。前端本地还存在即时性 UI 变更（启动/停止/排队等先改本地再等服务端事件），故采用「**state 权威 + running 本地镜像**」：渲染路径只读 `state`，本地动作同时写 `state` 与 `running`（镜像保持既有 `task.running` 读取点有效）。

## Goals / Non-Goals

**Goals:**

- 删 deriveTaskStatus 判定分支（渲染路径零推导）
- taskBucket/taskStatusInfo 等展示映射只基于 state + outcome
- report-generator 状态口径全小写（修复 Step 1 后的大小写断层）
- `npm run typecheck` + `npm run build` 通过

**Non-Goals:**

- 不删 `task.running` 字段与读取点（本地镜像，Step 7 可再清理）
- 不动 WS 事件协议、不动 ai-assistant 状态显示（登记）

## Decisions

- **resolveTaskState(task) = task.state || "idle"**：旧缓存/本地行无 state 时回退 idle（字段读取，非推导）
- **taskBucket 语义保持**：running→running；queued→waiting；done→outcome completed ? completed : incomplete；其余（idle）→ incomplete（现状行为）
- **镜像同步点**：所有 `task.running = x` 变更点旁补 `task.state = ...`（值：running/queued/idle/done），使既有 `task.running` 读取（约 30 处）零改动保持正确
- **小写口径**：report 三处 map/tabs 全部 lowercase；后端已小写，旧大写键为死代码删除

## 模块防火墙自检

- 纯前端改动；无新增 API 调用；信封与 snake_case 契约不变
- 展示组件不改契约；无 Pinia 新增
- 通过

## Risks / Trade-offs

- [state 与 running 镜像不同步导致渲染偏差] → 变更点逐一补同步（grep `\.running\s*=` 全量核对后补齐）
- [旧缓存任务无 state 显示为 idle] → 刷新列表即恢复权威值；过渡期回退 idle 优于推导
- [report 筛选键变化影响 URL/收藏] → 键仅内部使用（params），无 URL 持久化
