## Why

目标架构重构六步序列（L1b 枚举收敛 → L1a 算法下沉 → L1c 引擎收敛 → L2 协议接入 → L3 权威状态 → L4 前端收敛）开始前，需要先把"将要被移动的代码"的现状行为用测试锚定。当前这些代码无专项单测：`tests/device_inspector/` 仅 `test_capture_service.py`（无 xpath/ocr 专项），device_pool 连接池、test_runner 状态机与连接预检路径均无测试保护——不补基线，后续任何搬动都无法回归（见 Checklist §一"补测试先行"铁律）。

## What Changes

- 新增**现状行为基线测试**（纯测试变更，不改任何产品代码）：
  - 枚举与状态机现状：TaskCard 合法流转表、`repair_queued_terminal_drift` 漂移修复、TaskCard 序列化字段、TestRunStatus 双定义使用点
  - 算法现状：`gen_xpath_candidates` 策略分支、`trim_hierarchy`、XML 截断修复、OCR 契约
  - 引擎与连接现状：DevicePool 单例（switch_to/_addr/remove_device/info 缓存）、connect 预检关键词判定与超时常量、recovery 崩溃分类、`screenshot_b64` 格式
- 全量 pytest 跑通并**留存基线结果**（附到本变更完成说明，勾选 Checklist §一）

## 关联文档

- `dev_docs/03-设计与架构/迁移实施注意事项-Checklist.md`（§一 前置准备第 1、3 条：补测试先行、基线全绿留档）
- `dev_docs/03-设计与架构/设计-L1b-领域模型与枚举真相源.md`（§四 现状审计清单 → 测试锚定点）
- `dev_docs/03-设计与架构/设计-L1a-算法层.md`（§六 迁移映射 → 测试锚定点）
- `dev_docs/03-设计与架构/设计-L1c-引擎层.md`（§八 迁移映射 → 测试锚定点）
- 纯测试变更，不修订任何 PRD/ARCH 正文

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯测试基线变更：`.openspec.yaml` 已设 `skip_specs: true`，无需规范增量。

## Impact

- 新增测试文件：`tests/test_runner/`（新建目录）、`tests/device_pool/`、`tests/device_inspector/` 下的基线测试
- 对产品代码、API、数据库、前端零改动
- 后续变更（converge-state-enums 等）的行为改动将同步更新本变更锚定的"现状行为"断言
