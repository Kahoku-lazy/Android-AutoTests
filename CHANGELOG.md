# Changelog

本文件记录 Android-AutoTests 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Changed

- AgentScope 下限由 2.0.9 提到 2.0.12。本地向量库 `delete` 接受可选 `metadata_filter`，与该版 `VectorStoreBase` 对齐
- 依赖升级策略调整：移除 Dependabot 定期版本升级（`.github/dependabot.yml`），保留安全更新与漏洞告警，依赖巡检改为人工按需发起（见 `openspec/changes/retire-dependabot-version-updates/`）

### Added

- 开源社区基础设施：贡献指南（CONTRIBUTING）、行为准则（CODE_OF_CONDUCT）、安全策略（SECURITY）、Issue 模板、Dependabot 依赖更新、英文 README
- 仓库启用 Discussions、私密漏洞报告、secret scanning 与 push protection

## [0.1.0] - 2026-11-19

首个标记版本（早期版本，接口与功能可能变动）。

### Added

- **平台三层架构**：前端展示（Vue 3.5）· 后端通道与记账（Django 6.0.6 + DRF + Daphne）· `engines/` 能力核心（AgentScope ≥ 2.0.9）
- **登录鉴权**：JWT 双令牌 + 落库吊销
- **仪表盘**：KPI、执行趋势、任务结果、模型用量与费用、活动时间线
- **设备管理**：USB / WiFi ADB 接入、占用锁、心跳巡检、同设备串行 / 异设备并行
- **用例管理**：项目锁定库类型（自动化 / 功能两库），项目 → 用例行 → 步骤
- **平台助手**：模型配置、Agent 配置（执行者 / 验收者 / 规划者）、SOP 工作流、测试对话与评测
- **任务清单**：从已发布工作流提交 / 重跑 / 关闭
- **测试报告**：SOP 报告与助手报告只读台账
- **BUG 单**：任务失败分类台账
- **串口日志**：端口监听、只读日志、关键词对照表
- **知识库**：模块登记、只读检索、自动评测
- **运营后台**：用户管理、Agent 与模型配置
- **用量账本**：每次模型调用一条明细（`ai_usage_records`）
- **质量闸门**：`ci-phase1.yml`（python / frontend 双 job）+ 本地门禁 `python run.py check`；OpenSpec 规范驱动流程

### Security

- 模型密钥只从仓库根 `.env` 读取，页面不落明文；CI 凭据门禁（硬编码密码 / API Key / Token 检查）

[Unreleased]: https://github.com/Kahoku-lazy/Android-AutoTests/compare/v0.1.0...Kahoku
[0.1.0]: https://github.com/Kahoku-lazy/Android-AutoTests/releases/tag/v0.1.0