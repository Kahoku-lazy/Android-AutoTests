## Why

手工入口把步骤写死在源码里，换用例就要改代码。执行角色和验收角色现在还会看到同一段步骤文字，无法按 YAML 里的 `action` / `assert` 分别提问。

## What Changes

- 手工入口改为必填命令行参数，从 YAML 读出用例标题和步骤，再装配 SOP。一个文件里有几条用例就按顺序各跑一遍。
- `action` 只作为执行角色这一步的提示词；`assert` 只作为验收角色这一步的提示词。
- 验收通过进入下一步；不通过时同一步最多再试一次（`max_attempts=2`），第二次仍不通过则整次运行停在当前步，后续步骤不执行。
- 全部跑完后按用例标题分别输出 PASS 或 FAIL；FAIL 下列出失败步。末尾给出总耗时和合计 token、费用。
- 设备 ID 等开场输入、角色系统提示词、工具和技能保持不动。

## 关联文档

无关联 PRD。这是 `python -m engines.agents.agents` 手工运行入口的步骤来源调整，不改平台产品能力。

## Capabilities

### New Capabilities

### Modified Capabilities

- `agent-sop-workflow`: 步骤输入的两段文字分别只交给执行角色与验收角色；手工入口从 YAML 按条装入并各跑一遍；跑完后按标题输出 PASS 或 FAIL 与失败点。

## Impact

- `engines/agents/agents.py`：去掉写死的 `SopStepInput`，改为解析命令行路径并加载 YAML。
- `engines/agents/workflow/steps.py`：执行侧提问不含 `assert`，验收侧提问不含 `action`。
- 依赖：沿用仓库已有的 PyYAML，不新增依赖。
- 测试：补一条不调用模型的单测，覆盖 YAML 解析和两边提示词拆分。不跑全量回归。
