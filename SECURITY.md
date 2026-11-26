# 安全策略（Security Policy）

## 受支持的版本

| 版本 | 支持状态 |
| --- | --- |
| 0.1.x | ✅ 接收安全修复 |
| 更早 / 未发布分支 | ❌ 请先升级到受支持版本 |

## 报告漏洞

**请勿在公开 Issue、PR 或 Discussions 中披露安全漏洞。**

请使用 GitHub 私密漏洞报告（Private Vulnerability Reporting）：

👉 **[提交私密安全公告](https://github.com/Kahoku-lazy/Android-AutoTests/security/advisories/new)**

仅仓库维护者可见，修复发布前不会公开。

### 报告时请尽量包含

- 漏洞类型与影响（如：越权、注入、密钥泄露、路径穿越）
- 复现步骤或最小 PoC
- 受影响版本 / 提交号
- 可能的修复建议（可选）

### 响应预期

维护者会尽快确认收到（通常 7 天内），评估严重性并安排修复；修复发布后会在安全公告中致谢报告者（如你希望匿名，请注明）。本项目为社区维护，不设正式 SLA。

## 范围说明

- **在范围内**：本仓库平台代码（backend / frontend / engines）的安全缺陷。
- **不在范围内**：第三方依赖自身的漏洞（请报告给对应上游，本仓库的处理方式见下节「依赖更新策略」）、用户自行部署配置不当（如把 `.env` 提交进仓库、生产环境开启 DEBUG）。

## 依赖更新策略

- **安全更新自动开 PR**：仓库启用了 Dependabot security updates 与漏洞告警，出现已知 CVE 时会自动开修复 PR，仅针对有漏洞的依赖，不做常规版本追新。
- **定期版本升级已停用**：`.github/dependabot.yml` 已于 2026-11-26 移除。它按 pip / npm / github-actions 三个生态每周批量开 PR，跨大版本（如 vitest 4→5、mermaid 11→12）需人工逐个判废，成本高于收益；依赖巡检改为**人工按需发起**：`pip list --outdated` / `npm outdated` 评估后再单独提交升级 PR。
- **恢复自动追新**：从 git 历史取回配置即可 —— `git log -- .github/dependabot.yml` 找到删除前的提交，再 `git checkout <commit>^ -- .github/dependabot.yml`，下一个扫描周期生效。

## 密钥卫生（贡献者必读）

- 模型密钥只从仓库根 `.env` 读取，**严禁**把真实密钥写进代码、配置、文档或提交历史；仓库只跟踪 `.env.example` 占位模板。
- CI 含凭据门禁（硬编码密码 / API Key / Token 检查），推送保护（push protection）已开启，会拦截已知格式的密钥。