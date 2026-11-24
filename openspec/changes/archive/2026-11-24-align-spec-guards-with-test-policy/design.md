# Design: align-spec-guards-with-test-policy

## Context

- 触发点见 `proposal.md`；本设计只解决"规格指向哪里"。
- 现状：`tests/graybox/` 不存在；4 个活跃规格 6 处引用它。
- 现在实际守护这些一致性的用例都在 `tests/arch/unit/`：

| 规格 | 实际守护 |
|---|---|
| api-path-convention · 前端与测试调用面 | `tests/arch/unit/test_api_path_callers.py` |
| api-path-convention · 前端调用面与路由表 | 同上（三个扫描面之一为 frontend） |
| auth-form-validation · 文案与阈值 | `tests/arch/unit/test_auth_validation_parity.py` |
| auth-form-validation · 密码空白归一化 | 同上 |
| auth-response-shape · 前端 DTO 字段 | `tests/arch/unit/test_auth_frontend_contract.py` |
| auth-session · 公开端点清单 | `tests/arch/unit/test_auth_frontend_contract.py` + `test_auth_endpoint_declaration.py` |

## Goals / Non-Goals

**Goals**
- 规格里"由谁守护"指向真实存在、且在当前门禁里默认执行的目录。
- 保持原要求的语义强度（SHALL、零依赖、不得 skip）不变。

**Non-Goals**
- 不改断言语义、不新增/删除断言、不重构守护实现。
- 不把守护迁成灰盒用例（这些是源码一致性断言，不需要启动服务，也不该落库）。

## Decisions

**D1 落点选 `tests/arch/unit`，不选灰盒或 b2b。**
这些一致性断言的对象是"源码与路由表/网关清单一致"，不是用户可见功能；跑它们不需要起服务、不需要 DB。放进灰盒或 b2b 会把零依赖的守护变成环境依赖，反而降低默认门禁的守护力。

**D2 保留 requirement 标题原文，只改正文与场景。**
OpenSpec 的 MODIFIED 要求 header 与存量逐字匹配（whitespace-insensitive）；`api-path-convention` 那条标题里有「默认测试」字样，但改名会被校验器当成"新需求"或报不匹配。标题里的「默认测试」仍可读作"默认跑的那套"，故不动。

**D3 场景一并改，不留"默认单元测试"字样。**
场景是给执行者看的指令。只改需求正文、场景仍写"运行默认单元测试"，执行者还是会去找不存在的套件。两处都改成 `tests/arch/unit` 契约守护。

**D4 用 MODIFIED 全量复制需求块。**
按 schema 要求复制整块（需求正文 + 全部场景）再改，避免归档时丢场景。

## Risks / Trade-offs

- [归档时 delta 覆盖 main spec，若场景漏复制会丢内容] → 每条需求整块复制，归档后 `git diff openspec/specs` 应只有 6 处词句替换。
- [其他文档仍提 graybox] → `tests/AGENTS.md` 与 `.agents/docs/tests/**` 已在本轮口径变更里改完；`openspec/changes/archive/**` 的历史记录按惯例不改。
- [有人按旧印象找 `tests/graybox`] → 规格文本已改；`tests/arch/unit` 的模块 docstring 本就写明"契约守护"性质。

## Migration Plan

1. 落 4 个 delta（本变更 `specs/` 下）。
2. `openspec validate align-spec-guards-with-test-policy --strict` 通过后归档，由 tooling 覆盖 4 个 main spec。
3. 回退：还原这 4 个 main spec 的提交即可；不涉及代码，回退无副作用。
