## Context

- 现状：6 个已保存页面中，2 个的截图路径指向已删除的 `inspector/**` 文件（源缺失）、其余指向 `inspector/**`（源存在或为空）；`locator/pages/<id>/` 下已有新导入产生的副本（页面 46/47 等）。
- 复用点：`apps/element_locator/api_snapshot.py` 已有 `_copy_into_locator()`（含源缺失/IO 失败/幂等分支）与 `_media_filename(resource_id, bounds)`（与 upsert 键同源），命令直接复用同 app 内的这两个私有 helper，避免第二套命名规则。
- 目录约定：元素定位自有媒体根为 `locator/pages/<page_id>/`（C 方案已定），命令的 prune 只在这个前缀内活动。
- 现有管理命令风格：`apps/ai_assistant/management/commands/{cleanup_uploads,model_test,ui_pipeline}.py`（Django `BaseCommand` + `self.stdout.write`），本命令沿用。

## Goals / Non-Goals

**Goals:**

- 一次命令即可把存量页面「自愈」到元素定位自有目录，并在同一工具里回收孤儿副本
- 默认零副作用（dry-run），落盘必须显式 `--apply`

**Non-Goals:**

- 不删 `inspector/**`
- 不恢复已丢失媒体
- 不做定时调度（不做 cron/beat 注册）
- 不改模型与迁移

## Decisions

**D1 默认 dry-run，`--apply` 才写**
理由：回填会改 DB 路径、prune 会删文件，两者都不可逆；运维工具默认只读最安全，且 dry-run 输出计数足够决定是否执行。
备选：默认执行 + `--dry-run` 开关 → 否决（误触代价不可逆）。

**D2 backfill 只复制、不移动源文件**
理由：源文件可能仍被检查器快照引用（快照未删时删掉会让检查器侧回看 404）；C 方案的语义就是「复制到自有目录」，不是「搬家」。

**D3 prune 只删 `locator/pages/**` 下且**不在 DB 引用集**里的文件**
实现：先把 `Page.screenshot_path` 与 `Element.thumbnail_path` 全量读进内存集合，再遍历目录比对（一次查询、零 N+1）；删除后清理空目录。前缀白名单 + 引用集双重约束，确保不可能删到 `inspector/**`。
备选：按 mtime 清理旧副本 → 否决（会删掉仍被引用的）。

**D4 幂等**：backfill 对已在 `locator/pages/` 下的路径直接跳过（`_copy_into_locator` 的幂等分支）；prune 对已无孤儿的目录是空操作。因此命令可重复执行。

## 模块防火墙自检

- 文件落位：命令属 `apps/element_locator`（它拥有 `locator/pages/**` 与 `el_pages` / `el_elements`），无跨 App 写
- 跨 App import：零新增
- 写库路径：命令直接经 `Page.save(update_fields=...)` 写**本 App** 模型；按 `apps/AGENTS.md`「写库收敛到 api.py」，本命令复用的是 `api_snapshot.py` 的 helper，且只改本 App 两表——不改对方表，属本 App 内部维护
  说明：命令本身是 ORM 写（不经 api 函数）；为遵守「views 不直接 ORM 写」的口径，命令里只调用 `_copy_into_locator()` 并在 `Page`/`Element` 上做最小 `update_fields` 更新，不新增业务写路径。
- 端点 / 信封 / 迁移：零改动

## Risks / Trade-offs

- [prune 误删] → 白名单前缀 + DB 引用集双重约束；测试用「被引用 / 未被引用」两文件验证只删后者；命令输出删除清单前 N 条便于复核
- [大库内存占用] → 引用集为路径字符串集合（页面/元素级，量级千级），可忽略
- [回填把已失效路径「修好」] → 源缺失时明确跳过并计数，不伪造
- [与在跑的导入并发] → 命令以 `--apply` 手动运行；并发窗口内最多产生一次无意义的重复复制，幂等分支可收敛

## Migration Plan

1. 新增命令 + 4 例集成测试
2. 真机（dev 库）dry-run：核对计数（存量待回填 / 孤儿数）
3. 真机 `--apply`：回填后抽查页面记录指向 `locator/pages/**`，且副本可访问
4. 回滚：命令是新增文件，`git revert`；已回填的路径不会自动还原（功能不受影响）

## Open Questions

（无）
