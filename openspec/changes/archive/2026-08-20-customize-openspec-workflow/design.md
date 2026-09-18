## Context

默认 schema 模板位于 node_modules（`schema which spec-driven` → Source: package），npm 升级会被覆盖。定制必须 fork 到项目内 `openspec/schemas/android-autotests/`，通过 `openspec/config.yaml` 的 `schema:` 字段绑定。

## Goals / Non-Goals

**Goals:**
- 模板层定制：proposal 关联文档编号、tasks 验收门禁、design 防火墙自检、spec 中文注释
- 校验器骨架（`### Requirement:` / `#### Scenario:` / skip_specs 约定）保持不变

**Non-Goals:**
- 不改 schema 的 artifact 组合（proposal→specs→design→tasks 原样保留）
- 不把 AGENTS.md 铁律编进 schema.yaml 的生成指令（属深度定制，暂缓）
- 不替换现有 PRD/ARCH 文档体系

## Decisions

- **fork 而非 init**：项目工作流与默认 spec-driven 相同，fork 复用完整模板与指令，改动面最小
- **模板内用 HTML 注释承载约定**：校验器只解析标题与 checkbox，注释不会污染生成物
- **schema 描述行同步更新**：避免 fork 副本仍自称 "Default OpenSpec workflow" 造成误导

## 模块防火墙自检

- 不涉及任何 apps/ 模块代码，无跨 App import、无 ORM 写，防火墙无影响
- 新增文件全部位于 openspec/ 与 package.json（工具链宿主），无前端直连数据库等红线问题

## Risks / Trade-offs

- [schema fork 为 experimental 特性，升级可能变化] → fork 副本独立于 node_modules，升级只影响 `npx openspec` 本体；schema.yaml 结构如变更需手动跟进（升级后跑 `openspec schema validate android-autotests`）
- [模板注释与官方模板漂移] → 仅当新版本引入新必需章节时才需要合并，`openspec update` 不覆盖项目内 schema
