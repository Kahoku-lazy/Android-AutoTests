## Why

项目已安装 OpenSpec，但默认模板是通用英文工作流；需要把模板定制为贴合 Android-AutoTests 的 PRD/ARCH 文档编号体系与验收门禁，让后续每次变更生成时自动带上项目纪律。

## What Changes

- fork 默认 spec-driven schema 为项目本地 schema：`android-autotests`
- 定制 proposal 模板：新增"关联文档"章节（PRD/ARCH/UI 规范编号）
- 定制 tasks 模板：写入项目验收门禁惯例（manage.py check / ruff / pytest / 前端 build / 防火墙检查）
- 定制 design 模板：新增"模块防火墙自检"章节
- 定制 spec 模板：中文注释 + 校验器格式硬约定提示
- `openspec/config.yaml` 默认 schema 切换到 `android-autotests`

## 关联文档

- AGENTS.md（行为准则、模块防火墙、先文档后代码）
- dev_docs/文档编号对照表.md（PRD/ARCH 编号引用规范）
- 纯工具链/文档类变更，不修订任何 PRD/ARCH 内容

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯工具链变更：`.openspec.yaml` 已设 `skip_specs: true`，无需规范增量。

## Impact

- `openspec/schemas/android-autotests/**`（新增项目本地 schema 与 4 份定制模板）
- `openspec/config.yaml`（schema 切换）
- 对产品代码、API、数据库、前端页面无影响
