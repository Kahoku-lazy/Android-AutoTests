# 已取消的变更（cancelled）

本目录存放**已取消但保留原文**的 OpenSpec 变更。放在 `openspec/` 下而不是 `openspec/changes/` 下，
是为了让 `openspec list` 只列活跃变更（放在 `changes/` 里会被 CLI 当成一个 No tasks 的变更列出来）。

## 取消规则

- 取消 = 把 `openspec/changes/<name>/` 整体移到本目录，并在其中留 `CANCELLED.md`（进度、原因、恢复方法、取消后的实际影响）。
- **取消只去掉跟踪载体，不改变代码现状**：被取消的原定缺陷/债务仍在仓库里，只是不再有任务载体。
- 恢复 = 把目录整体移回 `openspec/changes/<name>/`，重新出现在 `openspec list`；恢复前先复核 proposal 的事实是否仍成立。

## 已取消清单（2026-11-23）

| 变更 | 原进度 | 原定处理的问题 |
|---|---|---|
| `fix-bug-error-label-wiring` | 0/5 | 规格 `bug-ticket-management` 要求的错误行首标签加粗未实现 |
| `fix-eval-usage-billing` | 0/5 | 两处计费失真（评测真实调用但 usage 记 0 token） |
| `fix-task-runtime-p0-defects` | 0/8 | 四处 P0 运行时缺陷（含设备锁身份可被请求体伪造） |
| `retire-backend-dead-code` | 0/25 | 后端约 70 处死代码/死配置 |
| `retire-frontend-dead-code` | 0/19 | 前端退役残留（孤儿文件、死类型簇、零使用图标与依赖） |
| `route-cross-app-imports-via-api` | 0/6 | 存活红线违规：dashboard 跨 App import `usage_ledger.rates` 内部常量 |

**未取消**（仍在 `openspec/changes/` 下）：`converge-device-pool-writes-to-api`(0/6) ——「写库走 api.py」红线的最大破口，且是 `device_pool` 模块文档后续任务（`align-backend-docs-with-code` 7.2）的前置。
