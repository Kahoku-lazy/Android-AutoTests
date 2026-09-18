## 1. Schema 定制

- [x] 1.1 fork spec-driven 为 android-autotests，验证 `npx openspec schema which android-autotests` 显示 Source: project
- [x] 1.2 定制 proposal/tasks/design/spec 四份模板，验证 `npx openspec schema validate android-autotests` 通过
- [x] 1.3 openspec/config.yaml 切换默认 schema，验证 `npx openspec new change <name>` 生成的 .openspec.yaml 绑定 android-autotests

## 2. 全链路验证

- [x] 2.1 创建本变更并按定制模板填写 proposal/tasks，验证 `npx openspec validate customize-openspec-workflow` 通过
- [ ] 2.2 归档本变更：`npx openspec archive customize-openspec-workflow --skip-specs -y`，验证进入 changes/archive/
