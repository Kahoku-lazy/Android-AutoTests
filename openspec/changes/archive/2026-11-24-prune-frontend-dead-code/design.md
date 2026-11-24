## Context

`frontend/src` 35,120 行 / 261 文件，其中组件（`.vue`）100 个、样式 6,750 行。本轮已完成的取证：

- **引用统计口径**：对 `src` 全部 `.vue/.ts/.js` 做「路径字符串包含文件名（含 `.vue` 后缀）」匹配；`components.d.ts` 证实 `unplugin-vue-components` 只自动导入 Element Plus 与 `RouterLink/RouterView`，**本地组件无自动导入**，故显式 import 数即真实引用数。结论：14 个文件零引用，合计 1,635 行。
- **二次点名核验**：对 14 个文件名做全 `src` 纯文本搜索（含注释与模板），命中全部为 0；对照组 `AppTabs` / `TaskBoard` 命中非 0，排除「扫漏」。
- **图标**：`shared/icons/index.ts` 定义 45 个，全站引用 15 个；侧栏图标走 `sidebarNavConfig.ts` 的 lucide 字符串键，与自绘图标是两套体系，互不影响。
- **时间格式化现状**（8 个函数 / 6 处）：

  | 位置 | 函数 | 相对时间档位 | 绝对时间精度 | 空/非法兜底 |
  |---|---|---|---|---|
  | `shared/helpers/datetime.ts` | `formatRelativeTime` / `formatDateTime` | 到日期 | 秒 | 「—」 |
  | `modules/device-pool/helpers.ts` | 同上两函数 | 到日期 | 秒 | 空「—」，**非法漏 `Invalid Date`** |
  | `modules/ops-console/helpers/datetime.ts` | 同上两函数 | 到天/月/年 | 分 | 「—」 |
  | `modules/bug-manager/constants.ts` | `formatBugTime` | — | 分 | 非法返回原串 |
  | `modules/report-generator/helpers/report-row.ts` | `formatReportTime` | — | 分 | 非法返回原串 |
  | `modules/task-list/helpers/task-detail.ts` | `formatTaskTime` | — | 分 | 空串，**字符串切片不解析** |

## Goals / Non-Goals

**Goals:**

1. 删掉 14 个零引用文件、1 个死 API 文件、30 个死图标、3 个死动画导出、15 个死常量、`getTask`，并清掉随之无对象的用例。
2. 把 6 处时间格式化收敛为 `shared/helpers/datetime.ts` 单一实现，**各调用方输出逐字不变**（唯一的显式例外见 D5）。
3. 用「先写死期望、再换实现」的顺序保证等价，而不是靠肉眼 diff。

**Non-Goals:**

- 不重新设计时间文案（不改「刚刚 / N 分钟前 / 日期」的措辞、不引入 i18n、不改时区口径）。
- 不动 `modules/ai-assistant/helpers/time-label.ts`（刻意不做时区换算，是另一套语义）。
- 不碰 `task-detail.ts` 中详情页装配函数与 `STEP_LOG_CHECK_*` 常量（见 D7）。
- 不做分页条 / ECharts 主题 / `.vue` 业务逻辑下沉（体检报告的第 3–5 项，另案）。

## Decisions

**D1：删除判据取「`src` 内零引用」，不取「全仓零引用」。**
`openspec/`、`dev_docs/`、`.agents/` 里的文件名提及是文档陈述，不是消费者。反例：`dev_docs` 若提到某组件，按全仓口径会被判为「有人用」，从而永远删不掉。备选：全仓口径 → 否决，它会把已退役功能的文档残留当成依赖。

**D2：只测死代码的用例随代码一起删，不留孤儿测试。**
5 个用例（`DoodleNote` / `TaskMediaThumb` / `ocrMatch` / `yaml-case-titles` / `errorDetail`）的被测对象删除后没有任何价值，保留只会让覆盖率虚高。备选：保留并标 `skip` → 否决，那是只增不减的债。

**D3：时间格式化用「一个模块 + 选项」，不按业务域分文件。**
对外只暴露 5 个入口：`formatRelativeTime`（含 `granularity: "long"`）、`formatDateTime`（含 `precision`）、`formatMonthDayTime`、`formatIsoNaive`，加一个内部 `pad2`。选项是**现有口径的枚举**，不是新设计——`"long"` 只为运营台的天/月/年档位、`minute`/`second` 只为现有两档精度。备选：每个业务域一个 formatter → 否决，那正是现状的成因。

**D4：等价性靠「先断后改」的 golden 用例。**
顺序固定为：① 对每个调用方现有函数写 4 类输入（正常 / 空串 / 非法串 / 未来时刻）的逐字期望；② 跑绿；③ 换成共享实现；④ 期望一字不改再跑绿。这样「等价」是可执行事实，不是审阅意见。

**D5：`device-pool` 的非法时间从 `Invalid Date` 改为「—」，作为本次唯一可见变化。**
依据：该函数缺 `NaN` 判定，`new Date("bad").toLocaleDateString()` 会渲染 `Invalid Date`；同模块 `formatDateTime` 与全站其它 formatter 都返回「—」，属兜底不一致的缺陷。`openspec/specs/` 下无任何能力描述「前端相对时间格式」，故不产生 delta。**显式声明**，不夹带：除这一条外不允许任何文案变化。

**D6：`time-label.ts` 不在收口范围。**
它用正则抽取服务端墙钟时间（`T17:55`），明确「不做时区换算」；共享实现走 `new Date()` 会按浏览器时区换算，语义相反。备选：并入共享并加 `noConvert` 选项 → 否决，那会把两套语义硬塞进一个函数。

**D7：3 个「零引用但被规格 / 设计系统点名」的文件与 `task-detail.ts` 的详情页装配函数，本次不删。**

| 文件 | 零引用事实 | 为什么不能删 |
|---|---|---|
| `bug-manager/helpers/errorDetail.ts`（39） | 生产 0 引用，仅测试 | `openspec/specs/bug-ticket-management/spec.md` 的 MUST 点名 `splitErrorDetail` 做行首标签识别 |
| `shared/components/DoodleNote.vue`（178） | 生产 0 引用，仅测试 | `openspec/specs/frontend-l4-data-surface/spec.md` 的 MUST 把 `DoodleNote` 列为共享卡片零件 |
| `shared/components/SplitHandle.vue`（145） | 生产 0 引用 | `doodle-craft` 版式规则要求「两栏之间 MUST 有 `SplitHandle`」，且要求「手柄行为照抄 `shared/components/SplitHandle.vue`」 |
| `task-detail.ts` 装配函数（约 300） | 生产只用到 `formatTaskCost` / `formatTaskDuration` | `openspec/specs/ai-task-list` 仍要求「任务卡『详情』MUST 进入 `/tasks/:taskId`」，而 `routes.ts` 只有 `/tasks` |

四者的共同点：**零引用不等于死代码**——它们是「规格要求、实现未接线」的既有漂移。删掉会让漂移从「规格要求但没接」升级成「规格指向不存在的文件」，也就是本变更用一个 `skip_specs` 的重构单，悄悄改了需求级事实。处理方式：本次不碰，在关单汇报里逐条登记，交需求方裁决「补接线」或「走 OpenSpec 退役条款」。同理 `STEP_LOG_CHECK_*` 文案常量暂留。

**D10：删除判据必须叠加「未被活规格与设计系统点名」。**
D1 只解决「谁算消费者」，不足以判死。反例就是 D7 的三个文件：代码零引用，但规格/技能把它们当作必须存在的零件。故判死三步：① `src` 内零引用；② `openspec/specs/**` 与 `.agents/skills/**` 不复述其文件名或 API；③ 删除后不会让某条 MUST 失去所指。备选：只看引用数 → 否决，本次已实证会误删 3 个文件并加深漂移。

**D8：图标注释同步为实际数量。**
`shared/icons/index.ts` 头注释写「45 个图标」，删除 30 个后必须同步，否则又是一条假信号（该文件历史上已因计数失真被单独修过一次：`2026-09-15-fix-icon-count-comment`）。

**D9：`ops-console/helpers/datetime.ts` 保留为薄包装，不直接改调用点。**
该文件被 `ops-console/index.vue` 以相对路径导入；转成 3 行 re-export 可让本次 diff 限制在 helper 内部，避免在 229 行的 `.vue` 里制造无关改动。备选：全部改调用点 → 否决，收益为零、回归面更大。

## 模块防火墙自检

- **跨 App import**：不涉及。本变更只动 `frontend/src`，无后端 import。
- **禁跨层依赖**：`shared/helpers/datetime.ts` 只依赖语言内建（`Date`），不引入任何模块、组件或 `api-client`，不前向依赖 `modules/`。
- **写库收敛**：不涉及任何 INSERT/UPDATE/DELETE；不新增接口调用。
- **前端不直连数据库**：维持。
- **仪表盘只读**：维持（删的是绘图组件与展示函数，无写操作）。

## Risks / Trade-offs

- **[删组件但存在 `<component :is>` 动态引用]** → 已用全 `src` 纯文本点名搜索（含模板与注释）排除；对照组证明扫描有效。
- **[等价表覆盖不足，某调用方文案悄悄变了]** → D4 的四类输入 + 逐字期望；改后再跑一次，期望文件零改动即为通过。
- **[`Invalid Date` 修复被当成「未经申报的行为变更」]** → D5 在 proposal 与 design 双处显式登记，且限定为单一函数、单一输入类。
- **[删用例导致某模块覆盖率下降被误读为回归]** → 在关单汇报里写明「删除的 5 个用例，其被测对象亦已删除」，并给出删除前后用例总数。
- **[文档/索引仍引用被删文件]** → 删除后对 14 个文件名做全仓复扫（`openspec/` 归档除外），把仍被 `frontend/AGENTS.md` 或模块文档引用的条目一并同步。
