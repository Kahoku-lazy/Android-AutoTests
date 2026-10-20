## Context

校验链路 = 卡片按钮 → `POST /agents/{id}/test`（或进页 `GET /agents/health`）→ 两段网络探测（供应商模型列表 + 极短推理）→ 写 `route_configs.*.health` 与 `AIAgent.is_connected/last_checked_at/available_models` → 卡片徽标。配置页已不再管理模型（`slim-agent-config-basic-info`），模型改由后台维护，这套探测只剩展示作用，且每次进页都会同步打供应商接口。

## Goals / Non-Goals

**Goals:**

- 前端不再有校验入口、状态徽标与自动探测；卡片身份区为名称 / 职责两行。
- 后端四个校验相关端点与三个健康字段彻底删除，不留「无 UI 的 API」。
- 消除进页时的同步外呼（原实现单请求 15s 超时 × 多角色）。

**Non-Goals:**

- 不改变任务执行链与模型装配（仍读 `route_configs`）。
- 不清理 `route_configs` 里已有的 `health` JSON 键（无读取方，留旧数据无害）。
- 不删除 `reveal-key`（查看密钥与连通校验无关）。

## Decisions

**D1 端点与字段全删，不只摘 UI。**
用户已确认「全套删除」。保留端点会继续进入 OpenAPI 并可能被外部调用，且三个字段没有其他写入方。备选：保留 `/agents/{id}/models`——它只缓存探测结果，随之删除。

**D2 模型探测端点 `/models/detect` 一并删除。**
它只服务已删除的模型配置 UI，当前零调用方。

**D3 卡片胶带色固定为青绿。**
原色由连通状态驱动；状态删除后固定 `var(--c-case)`，保持卡片视觉与其它 note 卡一致。

**D4 序列化器同步收缩输出。**
详情去掉 `is_connected / last_checked_at / available_models`；列表线路摘要去掉 `health`。`route_configs` 的 name/avatar/roles 仍保留（卡片与任务列表使用）。

## 模块防火墙自检

- 跨 App import：无新增；只删本 App 代码。
- 写库收敛：删除的是探测写库函数，其余不变。
- 前端不直连数据库：仍走 `djangoClient`。
- 数据：三个字段由本 App 迁移删除。

## Risks / Trade-offs

- [失去「模型是否可用」的页面可见性] → 由任务执行结果直接暴露；需要排查时看后台配置与任务日志。
- [仓外调用方仍请求四个端点] → 删除后 404，属预期；文档同步。
- [历史 `health` 键残留] → 无读取方；如需清理可另做数据清洗。
- [删字段不可逆] → 迁移只生成不执行；部署前可备份 `ai_agents`。

## Migration Plan

1. 合并代码与迁移；
2. 备份或确认无需保留三个健康列；
3. 执行 `python manage.py migrate ai_assistant`；
4. 回滚：恢复代码并用备份重建列（迁移不可逆）。

## Open Questions

无。
