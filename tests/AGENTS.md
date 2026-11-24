# tests 索引 — 测试文档导航

> **层级**：根 `AGENTS.md` → **本文件（索引）** → `.agents/docs/tests/**`（分层测试文档）
>
> 本文件只保留**简介**与**两条代码规范**，其余目录约定、分层范式与迁移状态都在下列文档里。
> **改某一层测试前，先读下表对应文档**；文档里的 MUST / 禁止 / 例外范式 / 保留理由，效力等同本目录约束。

## 简介

负责平台的测试工作，测试范围有接口、单元测试、集成测试、端到端测试，对应的测试信息详细阅读对应的模块。


## 代码规范

1. 所有的测试用例文件名称**必须**以 `test_` 开头。
2. 测试报告统一输出到 `reports/`目录


## 怎么用

1. 先读上面的「简介」与「代码规范」两条。
2. 新增 / 迁移测试目录、查某模块当前的落位与状态 → [tests_directory_conventions.md](../.agents/docs/tests/tests_directory_conventions.md)。
3. 按层改：单元与契约对拍 → [tests_unit_and_contract_parity.md](../.agents/docs/tests/tests_unit_and_contract_parity.md)；
   集成、接口与脚本映射 → [tests_integration_and_api.md](../.agents/docs/tests/tests_integration_and_api.md)；
   端到端 → [tests_e2e.md](../.agents/docs/tests/tests_e2e.md)。
4. 跨层改动（例如新增接口用例同时动了 YAML、脚本与夹具）→ 相关的两篇都要读，契约对拍那篇尤其要读。

## 主题 → 文档

| 主题 | 文档 | 讲什么 |
|------|------|--------|
| 目录约定 + 迁移状态 | [tests_directory_conventions.md](../.agents/docs/tests/tests_directory_conventions.md) | 一级按模块、二级按类型的四层目录；marker 与目录正交；`__init__.py` 必要性；已迁移 / 保留 / 已删除清单 |
| 单元测试 + 契约对拍 | [tests_unit_and_contract_parity.md](../.agents/docs/tests/tests_unit_and_contract_parity.md) | 单元层落位与 marker；「读源码做契约对拍」的例外范式：只读、只做一致性断言、零外部依赖、按调用形态扫描、例外显式、规模下限 |
| 集成测试 + 接口测试 | [tests_integration_and_api.md](../.agents/docs/tests/tests_integration_and_api.md) | 集成层落位；接口脚本与 `api_kit` 共享设施、Jsonschema 断言、YAML 用例要求；接口脚本与模块映射表 |
| 端到端测试 | [tests_e2e.md](../.agents/docs/tests/tests_e2e.md) | 用例落位与选择器集中、编号映射、零密钥、环境前置与 skip、每步留痕、步骤报告与 pytest-html |
