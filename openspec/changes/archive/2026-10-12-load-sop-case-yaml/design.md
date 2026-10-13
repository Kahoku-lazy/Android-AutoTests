## Context

见 proposal.md 的 Why。现状：`engines/agents/agents.py` 把两步 `SopStepInput` 写死；`SopSteps.build()` 把 `subject` / `description` 原样交给 AgentScope `SOPStep`。框架默认的执行提问和验收提问都会带上这两段文字。重试与「失败则不再进入下一步」已由 `SOPEngine` 按 `max_attempts` 处理，手工入口当前就是 `max_attempts=2`。

## Goals / Non-Goals

**Goals:**

- 手工入口用必填路径加载 YAML；文件里有几条用例就跑几遍。
- 执行提问只含 `action`，验收提问只含 `assert`。
- 保持 `max_attempts=2`，不重写引擎的通过 / 重试 / 停止循环。

**Non-Goals:**

- 不从 YAML 读设备 ID、模型或重试次数。同一文件里的多条用例共用这一份开场输入，但各跑一遍。
- 不改角色系统提示词、工具、技能，也不改 `SopRunner` 的计费与对话稿。

## Decisions

1. **加载函数放在手工入口模块，装配仍走 `SopSteps`。**  
   `load_sop_cases(path)` 返回每条用例的 `(title, list[SopStepInput])`，`action` → `subject`，`assert` → `description`。工作流目录继续只做装配，不读文件。  
   备选：把 YAML 解析放进 `workflow/steps.py`。否决原因是文件格式属于入口，不属于可反复运行的流程定义。

2. **根节点同时接受「单个映射」和「非空映射列表」。**  
   列表里每一条单独装配、单独 `start()` 后再跑，避免上一条的对话留在角色里。  
   备选：把多条步骤拼成一次 SOP。否决原因是两条用例要各有自己的标题和一次完整运行。

3. **在 `_CheckedStep` 上覆盖提问，不改 AgentScope。**  
   执行侧沿用框架的重试说明拼接，但正文只留 `subject`。验收侧正文只留 `description`，交接内容（handover）仍按框架附上，否则验收看不到执行者交出来的证据。恢复挂起时的事件仍原样交回，不重新包一层提示。  
   备选：把 `assert` 写进 `subject`、把 `action` 留空。无法同时满足「两边都要非空」和「两边各看各的」。

4. **路径用必填位置参数，相对路径按进程当前目录解析。**  
   与入口注释「在仓库根目录执行」一致。不设默认文件。

5. **PyYAML `safe_load`，不新增依赖。**  
   仓库测试加载器已经使用同一库。

6. **汇总按用例标题分行，不合成一个总的 PASS/FAIL。**  
   阶段为完成的用例写 `标题：PASS`。否则写 `标题：FAIL`，其下列出阶段为失败或结论为不通过的步骤（步序、动作、驳回说明）。尚未开始的后续步骤不列入。全部用例的耗时、token 与费用在末尾合计一次。  
   备选：只给一个总结果。否决原因是一条失败、另一条成功时无法看出是哪一条。

## 模块防火墙自检

- 不涉及 `apps/`，无跨 App import，无写库。
- 不改前端，不新增 HTTP / WebSocket。
- 只改 `engines/agents` 的手工入口与步骤提问，依赖停留在已有的 AgentScope 与 PyYAML。

## Risks / Trade-offs

- [执行者不再看到断言原文] → 这是本次要的拆分；驳回说明仍会在第二次尝试时交回执行者。
- [覆盖提问后和框架升级分叉] → 只改正文来源，挂起恢复与交接结构保持框架原样，并在单测里锁住两边提示词的包含关系。
- [现有单测把 `subject` 称作短名] → 字段名不变，那些断言仍然成立；补提示词拆分与 YAML 解析用例，不改它们的通过条件。
