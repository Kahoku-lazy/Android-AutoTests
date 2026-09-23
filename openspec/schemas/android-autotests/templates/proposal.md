## Why

<!-- 动机：解决什么问题？为什么现在做？（中文填写，1-2 句） -->

## What Changes

<!-- 变更内容：新增/修改/移除的具体能力，破坏性变更标 **BREAKING** -->

## 关联文档

<!-- 必填：关联的需求编号。
     需求入口一律从 PRD 开始，只写编号，不写文档文件路径。
     无关联文档时写明原因（如纯重构 / 工具链 / 文档类变更）。 -->

## Capabilities

### New Capabilities
<!-- 新增能力。路径段用 kebab-case（如 user-auth 或 identity/user-auth），
     遵循项目现有 spec 组织。每个都会生成 specs/<capability-path>/spec.md。 -->
- `<capability-path>`: <该能力覆盖范围的简要说明>

### Modified Capabilities
<!-- 需求级行为发生变化的现有能力（非实现细节）。每个都需要 delta spec 文件。
     使用 openspec/specs/ 下的现有精确路径。无需求变化则留空。
     完全没有能力的变更（纯重构/工具/文档）必须在其 .openspec.yaml 里设
     `skip_specs: true`——openspec validate 会拒绝无 delta 且无该标记的变更。
     不要为了通过校验而编造需求。 -->
- `<existing-capability-path>`: <哪些需求在变化>

## Impact

<!-- 受影响的代码、API、依赖、系统（列出 apps/ 模块、前端页面、测试范围） -->
