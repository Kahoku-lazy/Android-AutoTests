## Context

装配台左侧来源行的副标题由 `useToolboxAssembly.sourceMeta(src)` 生成，判据是「有没有 `gateKey`」：prompt / port / debug 三个来源 `gateKey` 为空，理论上都该走「不交给助手」的说明文案，但只有 prompt 与 port 被逐一写了分支。debug 来源（后加的第四个来源）掉进通用分支，执行 `${sourceLiveCount}/${sourceCatalogTotal} 生效`：分子取自生效芯片（`buildLiveChips` 只产出 biz / skill 两类，debug 恒为 0），分母退回复用 Skill 目录数量，于是得到「0/5 生效」这一假数据。动机见 `proposal.md - Why`，行为契约见 `specs/ai-model-debug/spec.md`。

## Goals / Non-Goals

**Goals:**

- 「模型调试」来源行展示说明性文案，不再出现任何「n/m 生效」计数。
- 消除根因：让「无总闸来源」不再有机会掉进计数分支，后续新增同类来源时不会重演。

**Non-Goals:**

- 不改动装配台的整体信息架构、不新增来源、不调整其它来源行的文案与计数口径。
- 不改动模型调试子页、后端接口与数据。

## Decisions

**决策 1：把「无总闸来源」的副标题文案下沉到来源定义里，而不是再加一个 `if (src.key === 'debug')` 分支。**

- 做法：`AssemblySourceDef` 增加可选字段 `meta`（无总闸来源必填）；`ASSEMBLY_SOURCES` 里 prompt / port / debug 各自声明自己的文案；`sourceMeta` 优先返回 `src.meta`，只有在没有 `meta` 时才走「分子/分母 生效」的计数逻辑。计数逻辑因此只服务于真正参与装配的两个来源（biz / skill）。
- 理由：现有实现按 key 逐个特判，是「加了新来源忘了补分支」这类缺陷的温床（本次即为其后果）。把文案放在来源定义同一处，新增来源时字段缺失一眼可见，且文案与来源名称 / 说明同源。
- 备选：① 只给 debug 加一个 `if` 分支——改动最小，但根因留存在，下一个无总闸来源仍会复现；② 在计数函数里对无总闸来源统一返回空串——会让「文案」变成隐式默认值，prompt 那类有专属语义的文案无处安放。故取下沉方案。
- 文案取值：debug 用 `规划 / 执行 / 验收 · 仅调试不交给助手`，与 port 现有句式（`监听开关 · 原始日志 · 不交给助手`）一致；prompt 保持现有 `规划 / 执行 / 验收 · 始终交给助手` 不变。

**决策 2：文案常量落在来源定义所在的 `helpers/toolbox-assembly.ts`。**

- 理由：该文件已是来源名称 / 说明的唯一真相源（`sourceDef()` 供子区块取用），副标题与它们同属一层元信息；`constants.ts` 面向页面级文案（角色标签、区块标题、范围说明），不适合承载来源定义字段。
- 备选：放进 `constants.ts`——会造成「来源定义在这里、来源文案在那里」的双处维护。

**决策 3：测试对齐既有 port 用例形态，补一条 debug 用例。**

- 做法：在 `frontend/tests/ai-assistant/p0/toolbox-assembly-port-source.spec.ts` 同目录新增等价用例：debug 来源存在、`gateKey` 为空、不进生效芯片、不进「未装配」清单、`sourceMeta` 返回说明文案且不含 `/` 形态计数。
- 理由：port 的用例就是上一次同类修正留下的验收模板，复用可避免口径漂移。

## 模块防火墙自检

- 跨 App import：本次仅改前端 `ai-assistant` 模块内部（composable + helper + 测试），无任何后端 / 跨 App import。
- 写库收敛：无 INSERT/UPDATE/DELETE，不触碰 `api.py`。
- 前端不直连数据库、不做写操作：本变更只改展示文案，符合。
- 通信通道：无 HTTP 调用新增或改动，前端唯一出口（`api/toolbox.ts`）不受影响。

## Risks / Trade-offs

- [prompt / port 的现有文案被挪动位置后可能被无意改写，导致既有用例或用户可见文案变化] → 文案字面值原样迁移，port 既有用例的断言字符串一字不改；实施后用该用例回归验证。
- [`AssemblySourceDef` 增加可选字段，若某来源漏填 `meta` 又无 `gateKey`，会静默回落计数分支] → 由决策 3 的用例断言「无总闸来源的副标题不含计数」；同时在字段注释里写明「无总闸来源必填」。
- [类型放宽导致 `meta` 语义被误用到有总闸来源上] → `sourceMeta` 只在 `gateKey` 为空时读取 `meta`，有总闸来源即使填了也不生效（或约定不填）。
