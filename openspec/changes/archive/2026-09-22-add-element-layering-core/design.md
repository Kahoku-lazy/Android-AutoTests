## Context

- `engines/device/base.py` 的 `UiEngine` 协议现有感知方法：`screenshot() -> bytes`、`dump_hierarchy() -> list[Node]`、`app_current() -> dict`；`engines/device/android/u2.py` 另有 `screenshot_b64()` 与 `screenshot_file(path)`。
- `algorithms/hierarchy.py` 已是纯解析器（raw 文本/字节 → 节点 dict 列表，含补 XML 声明与截断修复）；`models/ui_nodes.py` 定义 Node 契约。
- **既有分层错配**：`u2.py:21` 在引擎内 import 算法层解析器，引擎同时承担取数与解析；该文件 `:9-10` 自注为「⚠️ 契约出入…待评审裁决」。
- 平台内层级取数的消费者只有一处：`apps/device_inspector/service.py:88`（`[asdict(n) for n in engine.dump_hierarchy()]`）。`tools/dump_ui.py` 不经引擎，直接用 uiautomator2，不受影响。
- 「两级分组 + 细类 + 主定位选择」目前只存在于一次性工具脚本，平台层没有对应模块，Django 端点与前端因此没有共同真相源。
- 动机见 proposal.md - Why；要求见 specs/element-layering 与 specs/engine-protocol。

## Goals / Non-Goals

**Goals:**

- 让引擎只做取数：层级取数只返回原始 XML，解析与分类都归算法层；由此消除 `engines → algorithms` 反向依赖。
- 算法层新增纯函数模块，成为两级分组、七细类与主定位选择的**唯一真相源**，供后续的后端端点、前端页面与 HTML 报告共用。

**Non-Goals:**

- 不改展示裁剪规则（纯布局容器 / 同 bounds 去重）。
- 不改 6 层页面分区算法（`layout.classify_structure`）与其端点。
- 不加 Django 端点、不落库、不动前端页面（后续两个变更处理）。
- 不改造 `tools/dump_ui.py`（它不经引擎，与本变更无关）。
- 不在本单做候选生成的性能优化（另议）。

## Decisions

**D1 引擎只输出层级原始 XML，解析一律在调用方。** 依据「引擎取数、算法解析」的分层口径，取数与解析必须分家；这也是消除反向依赖的唯一彻底做法。备选：让算法层直接 import engines 取设备 → 否决（同时越过 engines 与 algorithms 两层边界）。

**D2 层级取数方法的返回值由 Node 列表改为原始 XML 文本（BREAKING）。** 若保留 Node 版方法并另加原始 XML 方法，引擎仍必须解析，反向依赖原样保留——问题改不动，故一并移除。平台内唯一消费者是设备检查器采集编排，同一变更内改造完毕；引擎契约测试同步更新。备选：保留 Node 版方法只加原始 XML 方法 → 否决（解析仍在引擎内）。

**D3 解析归算法层既有函数：调用方拿 XML 调 `algorithms.hierarchy.parse_hierarchy_xml` 得到节点，再照原流程消费。** 不在 apps 层另写解析。备选：把解析器上移到 `models/` 让引擎继续解析 → 否决（与「引擎不做解析」的口径冲突）。

**D4 算法层新增 `algorithms/element_layers.py`（纯函数模块）。** 与 `algorithms/xpath.py`（候选生成）职责正交：前者回答「这是什么控件、信不信得过」，后者回答「怎么定位」。备选：塞进 `xpath.py` → 否决（两个职责混在一处，后续前端/报告复用会牵连候选生成）。

**D5 位置型候选保留生成，但永不作主定位，且始终标注脆弱。** 它是无身份元素的最后回退，删掉会让部分元素彻底无候选。备选：删除位置型候选 → 否决（丢失回退与「同类第 n 个」的显式表达）。

**D6 未被任何类名集合覆盖的控件进「其它」，不做猜测归组。** 对齐根 AGENTS「面对模糊不清拒绝猜测」；「其它」的计数本身是可观测信号，便于后续按真实语料扩集合。

**D7 图标字体用码点区间判定（U+E000–F8FF / U+F0000–FFFFD），不用字形。** 字形判断依赖字体文件、不可测；码点区间可写成断言。

**D8 不做 Schema-Driven（XSD/xsdata）解析。** uiautomator dump 没有权威 schema，走 XSD 只能自造并长期维护，收益是「把隐式映射显式化」而非「用权威 schema 校验」，成本却是 XSD + 生成代码 + 构建步骤三份工件；且生成的类型会与 `models/ui_nodes.py` 的手写契约冲突。

## 模块防火墙自检

- **跨 App import**：本单不新增任何跨 App import。
- **engines ↔ algorithms**：本单**消除**既有的 `u2.py → algorithms.hierarchy` 反向依赖；改造后 `engines/` 内 MUST NOT 出现对 `algorithms.*` 的 import，`algorithms/element_layers.py` 也 MUST NOT 反向 import engines。
- **调用方向**：`apps/` 调 `algorithms/`（上层调下层纯函数）是合法方向；`models/ui_nodes.py` 作为数据契约被两侧共享，属既有安排。
- **写库**：本单不涉及 ORM，无 INSERT/UPDATE/DELETE。
- **前端**：无改动；无 HTTP 出口变化。
- **新增依赖**：无。

## Risks / Trade-offs

- [层级取数契约 BREAKING（返回值由 Node 列表改为原始 XML）] → 平台内唯一消费者是 `apps/device_inspector/service.py:88`，同一变更内改造；引擎契约测试与 `tests/arch` 一并更新，避免遗漏调用方。
- [调用方各自解析可能口径漂移] → 解析统一走 `algorithms.hierarchy.parse_hierarchy_xml`，并由契约测试断言「原始 XML 经该函数解析」与改造前的节点集合一致（节点数、类名、资源标识、文本、bounds）。
- [`models/ui_nodes.py` 的职责注释与实现分家] → 同一变更内更新注释：Node 的构造职责归算法层，引擎只产出原始 XML。
- [类名集合覆盖不到 OEM 自定义控件，会落进「其它」] → 「其它」是显式兜底且计数可观测；后续按真实语料扩集合，不改判据结构。
- [工具脚本带有一份内联算法副本，长期可能与算法层漂移] → 工具侧已有来源路径与来源摘要记录；本变更补一条摘要比对检查，平台算法改动后即可发现不一致。

## Migration Plan

- 发布顺序：先改协议与引擎实现，再同批改调用方（同一提交内完成，避免中间态）。
- 回滚：恢复 Node 版方法（引擎重新 import 解析器）与调用方原写法即可；无数据迁移。
- 无数据库、无前端、无端点影响，回滚成本低。

## Open Questions

- 引擎是否需要向上层暴露「压缩 / 美化」开关（当前由实现内部三层 fallback 决定，暂不暴露）。
- 类名集合是否需要按 OEM/版本语料扩展（等真实语料，不影响本单判据结构）。