## Why

主规格 `bug-ticket-management` 的「错误内容行首标签加粗」要求（MUST 走 `helpers/errorDetail.ts::splitErrorDetail`）已随 `2026-11-17-bug-error-label-bold` 归档，但 git 历史证明渲染接线从未入库：`BugDetailDrawer.vue` 至今用 `<pre>` 直出错误原文，纯函数与 P0 测试空转、`.bug-detail__line-key` 成死样式类。规格与实现互相矛盾，须恢复实现合规。

## What Changes

- `BugDetailDrawer.vue`「错误内容」分支（无失败步骤时的 `v-else`）：`<pre>` 改为逐行渲染——`splitErrorDetail` 拆行，行首标签用 `<span class="bug-detail__line-key">` 加粗，其余整行按正文；空文本保留「—」占位。
- 复用已入库的 `BugDetailDrawer.style.css` 行级样式（`.bug-detail__line` / `.bug-detail__line-key`），不改卡片底色、描边、硬影与行高。
- 新增抽屉渲染单测：标签加粗、堆栈行整行正文、URL 行不拆标签三条规格场景落到组件级断言（现有 `errorDetail.spec.ts` 只覆盖纯函数）。
- 不改 `splitErrorDetail` 判定规则，不改失败步骤（四问）分支，不改任何接口。

## 关联文档

无关联需求编号。本变更是恢复既有规格合规的缺陷修复（规格漂移修复），问题来源于前端废弃代码与技术债审计（审计结论：归档变更任务 2.1 声称完成但模板接线从未提交）。规格文本本身不变，故无规格 delta。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——`bug-ticket-management` 的「错误内容行首标签加粗」要求原文不变，本变更只让实现重新满足它；按 schema 规则在 `.openspec.yaml` 设 `skip_specs: true`。）

## Impact

- 前端：`frontend/src/modules/bug-manager/components/BugDetailDrawer.vue`（仅错误内容分支模板与脚本引入）；样式文件已有对应类，预计零改动或微调。
- 测试：`frontend/tests/bug-manager/p0/` 新增抽屉渲染 spec；既有 `errorDetail.spec.ts` 不动。
- 无后端 / 引擎 / 依赖 / 路由影响；与进行中变更 `platform-config-for-knowledge` 无文件交集。
