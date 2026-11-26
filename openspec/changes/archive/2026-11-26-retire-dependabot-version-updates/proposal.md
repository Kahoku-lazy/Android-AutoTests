## Why

Dependabot 定期版本升级按 pip / npm / github-actions 三个生态每周自动开 PR，2026-11-19 配置上线后 7 天内累计开出 **56 个**；其中 `vitest 4→5`、`mermaid 11→12`、`jsdom 29→31`、`vue-router 4→5`、`vue-tsc 2→3` 这类跨大版本升级与仓库刻意锁定的技术栈口径冲突，必须人工逐个判废，而每个 PR 都要把 `python` 与 `frontend` 两个 CI job 跑一遍。升级带来的不兼容风险由人工兜底、却缺少配套验证（CI 不执行设备与图像代码），噪音与风险两头都不划算。

## What Changes

- **移除定期版本升级**：**删除整个** `.github/dependabot.yml`（GitHub 的该文件要求 `updates:` 非空，留空壳会被判为配置无效并报错）。停用理由与反悔路径写进 `SECURITY.md`，避免后来者误判为漏配而重新打开。
- **保留安全网**：不改仓库 Settings 中的 `Dependabot security updates`（当前 `enabled: true`）与漏洞告警；出现 CVE 时仍会自动开修复 PR。
- **收尾当前打开的 10 个 PR**（#78–#87）：只关闭、不合并。更早的 11 个同类 PR（#8 / #14 / #18 / #25 / #29 / #34 / #35 / #45 / #52 / #53 / #55）已在 2026-11-19 至 11-24 期间被关闭（被新版本取代），本次无需再动。安全更新类 PR 不在关闭范围（当前无）。
- **文档措辞同步**：`CHANGELOG.md` 与 `SECURITY.md` 中「Dependabot 跟踪依赖更新」的表述改为「安全更新与漏洞告警」，避免文档承诺与实际策略不一致。
- **不动**：CI 工作流、`python -m run check`、`requirements.txt` 与 `frontend/package.json` 的版本约束、平台运行行为。**非 BREAKING**。

## 关联文档

无 PRD 编号：属**仓库工具链策略**变更（与 `repo-wide-python-docstring`、`fix-module-doc-drift` 同类），不改平台运行行为，`.openspec.yaml` 已设 `skip_specs: true`。需求方口径见 `design.md` D1–D5（2026-11-26 会话确认：A 档「停定期升级、保留安全更新与告警」+ 走 OpenSpec 变更单）。

## Capabilities

### New Capabilities

（无 —— 纯工具链策略变更，无行为级需求变化。）

### Modified Capabilities

（无）

## Impact

- **配置**：`.github/dependabot.yml`（唯一代码级改动，一个文件）
- **文档**：`CHANGELOG.md`、`SECURITY.md`
- **远端操作**：关闭当前打开的 10 个 PR（#78–#87；只 `close`，不 `merge`；分支保留，可 `reopen`）。关闭后远端 open 列表归零，11 个历史挂单本就已关闭
- **不受影响**：`ci-phase1.yml` 两个 job、依赖安装与锁定版本、`backend/**` / `engines/**` / `frontend/**` 源码
- **回退**：`git revert` 该提交即恢复每周扫描；被关闭的 PR 在 GitHub 上可逐个 reopen（分支与 commit 未删除）
- **遗留事项（不在本次范围）**：`minimatch` 的 medium 告警仍挂着（`frontend/package-lock.json`，传递依赖，devDependencies 链路），本次不顺手升，避免把行为改动混进策略变更；如需处理另开单。

### 变更申请（改什么 / 为什么必须改 / 影响面 / 怎么回退）

| 项 | 内容 |
| --- | --- |
| 改什么 | ① 删除 `dependabot.yml` 的 `updates:` 三生态条目并改写为策略说明；② 同步 `CHANGELOG.md` / `SECURITY.md` 措辞；③ 关闭存量定期升级 PR |
| 为什么必须改 | 需求方 2026-11-26 明确「升级会带来问题」，要求关闭定期升级检查；跨大版本 PR 持续灌入且无配套验证，人工判废成本高于收益 |
| 影响面 | 不触碰 `AGENTS.md` 红线 / 禁止事项 / 准入清单 / 依赖边界，不改任何运行时行为、不改依赖版本；影响仅限仓库依赖维护流程与文档表述 |
| 怎么回退 | 单文件回退：`git revert` 该提交；若只恢复扫描、不恢复文档，可单独 `git checkout` 还原 `.github/dependabot.yml` |
