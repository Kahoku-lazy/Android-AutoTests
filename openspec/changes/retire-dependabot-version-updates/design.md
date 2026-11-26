## Context

- 现状：`.github/dependabot.yml` 配了 pip（`/`）、npm（`/frontend`）、github-actions（`/`）三个 ecosystem，均为 `interval: weekly` + `open-pull-requests-limit: 5`，无 `groups`，`ignore` 只覆盖 django、opencv、vite、pinia、@vitest/ui 的部分升级类型。
- 后果：一依赖一 PR，理论上限 15 个并发；实际 2026-11-19 至 11-26 开出 56 个，当前 10 个打开，另有 11 个历史挂单。
- 安全侧现状（仓库设置实测）：`automated-security-fixes` = `{"enabled": true, "paused": false}`，漏洞告警开启（`vulnerability-alerts` 返回 204），当前 1 个 open 告警（`minimatch`，medium，`frontend/package-lock.json`）。
- CI 现状：`ci-phase1.yml` 只有 `python` 与 `frontend` 两个 job，**不含任何依赖审计或漏洞门禁**，即 Dependabot 是唯一的漏洞信号来源。动机见 `proposal.md` - Why。

## Goals / Non-Goals

**Goals:**

- 让「每周 10+ 个版本升级 PR」归零，同时**不丢失** CVE 自动修复与漏洞告警这两条通道。
- 留下可被后来者读懂的反悔路径：为什么停、怎么恢复、恢复后会发生什么。

**Non-Goals:**

- 不改任何依赖的版本约束、不升不降任何包（`minimatch` 告警单列，不在本次范围）。
- 不改 CI 工作流、不新增依赖审计门禁。
- 不做 `groups` / 扩 `ignore` 的「降噪但不关」方案（这是被否掉的备选，见 D1）。

## Decisions

### D1 关到 A 档：停定期升级，保留安全更新与告警

- 依据：噪音源是 version updates（定时扫最新版），而 security updates 只在有 CVE 时开 PR，量小且真该升。
- 备选与不选理由：
  - **B 档（连安全更新与告警一起关）**：会让 `minimatch` 这类 medium 告警彻底无人提醒，而 CI 不看漏洞 → 不选。
  - **C 档（`groups` 分组 + 扩 `ignore`）**：PR 能降到每周 1–2 个，但 `ignore` 清单要长期维护、跨大版本仍会以「分组 PR」形式灌入，且需求方要的是「停」，不是「少」→ 不选。

### D2 删除整个 `.github/dependabot.yml`，而不是留空壳

- `dependabot.yml` 的 `updates:` 是必填且要求非空；把条目注释掉等于无效配置，GitHub 会在 Security 页报「Dependabot 配置无效」，属于把静默换成另一种噪音。
- 删除文件 = GitHub 视为「未启用 version updates」，无告警、无报错。
- 停用理由落在 `SECURITY.md`（该文件已有「第三方依赖漏洞」条目），恢复方式 = 从 git 历史取回该文件。

### D3 只 close 当前打开的 10 个 PR，不 merge

- 关闭范围：当前打开的 10 个 PR（#78–#87）。
- 历史挂单（#8 / #14 / #18 / #25 / #29 / #34 / #35 / #45 / #52 / #53 / #55）实测**均已关闭**（2026-11-19 至 11-24 期间被新版本取代），本次无动作。
- 只 `gh pr close`，附同一句说明「版本升级策略已停用，见 SECURITY.md」；分支与 commit 保留，需要时可 `reopen`。
- 不 merge 任何一条：合并即等于「在停用前夕偷偷升级」，与本次意图相反，也会把未验证的跨大版本带进 `Kahoku`。
- 关闭后远端 open 列表应为 0 条，作为 3.1 的验收信号。

### D4 文档口径：一处承诺、一处记录

- `SECURITY.md`：「第三方依赖自身的漏洞（…Dependabot 会跟踪本仓库依赖更新）」改为区分两件事 —— 安全更新仍由 Dependabot security updates 自动开 PR；定期版本升级已停用，依赖巡检改为人工按需发起。
- `CHANGELOG.md`：`Unreleased` 下加一条 `chore(deps)` 记录本次策略变更，指向本变更目录。

### D5 不引入替代工具（Renovate / npm-check-updates 定时任务）

- 换工具解决的是「谁来扫」，本变更要解决的是「不要自动扫」。人工按需升级（`npm outdated` / `pip list --outdated` 后手工提 PR）已足够，且天然带人工评审。

## 模块防火墙自检

- 本变更**不涉及** Python / Vue 源码、不新增 import、不触碰 `apps/`（`backend`）与 `engines/` 的依赖方向。
- 改动面为 1 个 GitHub 配置文件 + 2 个 Markdown，均不属于「跨 App import / service 直连 / 前端直连数据库」约束的适用对象。
- 不涉及 `AGENTS.md` 红线、禁止事项、准入清单与依赖边界条款（`AGENTS.md` 第 4 条的四类改动均不命中）。

## Risks / Trade-offs

- [依赖长期冻结，已知 CVE 之外的「有更新但无 CVE」的好处丢失] → 保留告警通道 + `SECURITY.md` 写明人工巡检口径；需要追新时按需单个升级，不再批量。
- [安全更新 PR 仍会出现，可能被误读为「关闭没生效」] → `SECURITY.md` 明确区分两类 PR；关闭时给存量 PR 统一留言。
- [一次性 close 21 个 PR 产生通知噪音] → 同一批操作、同一句说明，一次做完，不分批打扰。
- [后人不知原因，重新加回配置] → 停用理由与恢复步骤写进 `SECURITY.md`，并在 `CHANGELOG.md` 留记录。
- [GitHub 侧 Settings 与文件状态不一致（文件删了但 security updates 关着）] → apply 阶段用 `gh api .../automated-security-fixes` 复核一次，确认仍为 `enabled: true`。

## 迁移与回退

- 迁移：删配置 → 批量 close 存量 PR → 改进两份文档 → 复核 `automated-security-fixes` 仍 enabled → 本地 `python -m run check` 无新增失败（本变更不触碰门禁项，预期全绿）→ 走 `feature 分支 → PR → CI 双 job 全绿 → 合并 Kahoku`。
- 回退：`git revert` 该提交即可恢复每周扫描（`dependabot.yml` 从历史取回）；被关闭的 PR 在 GitHub 上可逐个 `reopen`（分支未删）。
