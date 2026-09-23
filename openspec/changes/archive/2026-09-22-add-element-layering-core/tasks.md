## 1. 引擎：只输出原始 XML，不做解析

- [x] 1.1 修改 `engines/device/base.py` 的协议：层级取数方法签名改为返回原始 XML 文本，并删除原「返回 Node 列表」的方法声明，验证：`python manage.py check` 通过，且协议内不再声明 Node 版层级方法
- [x] 1.2 修改 `engines/device/android/u2.py`：实现新的原始 XML 取数（三层 fallback 收敛在新方法内），删除对算法层解析器的 import 与节点转换逻辑，验证：`grep -R "from algorithms" engines/` 无命中，且 `pytest tests/graybox/unit -q` 通过
- [x] 1.3 改造调用方 `apps/device_inspector/service.py:86-95`：改为「取原始 XML → 经算法层解析 → 按原流程消费」，并同步更新 `models/ui_nodes.py:3-4` 的职责注释（构造职责归算法层），验证：设备检查器采集端点回归通过（快照的元素数与保留数与此前一致）
- [x] 1.4 更新引擎契约测试：断言「原始 XML 经算法层解析」得到的节点集合与改造前口径一致（节点数、类名、资源标识、文本、bounds），并覆盖「层级取数失败时抛错而不是返回假数据」，验证：`pytest tests/graybox/unit tests/arch -q` 通过
- [x] 1.5 边界自检：`python tools/gen_arch_stats.py --check-boundaries` 通过，确认 `engines/` 内不再出现 `algorithms.*` import（既有那处契约出入随本单消除）

## 2. 算法层：两级分组与主定位

- [x] 2.1 新增 `algorithms/element_layers.py`：登记布局容器/滚动·集合容器/文本类/图形类四个类名集合，实现一级分组分类（含未覆盖类名进「其它」的兜底），验证：单测覆盖四个分组，且「其它」分组只承接集合外类名
- [x] 2.2 同模块实现二级分组与七细类判定（文本非空/空文本/图标字体码点区间/图形有无内容描述/裸视图可点与否），验证：单测对七个细类各至少一条断言，含私用区码点（U+E000–F8FF）与空文本两条边界
- [x] 2.3 同模块实现主定位选择与唯一性判定（先筛匹配数为 1 且非位置型候选，再按资源标识 > 内容描述 > 组合 > 文本 > 类名 取首条；无唯一候选时标记不稳定），验证：单测覆盖「位置型候选匹配数恒为 1 但不得胜出」「唯一性优先于类型质量」「无可定位身份时主定位为空」三条
- [x] 2.4 同模块实现分组内坐标排序与元素条目组装（坐标含左上角、宽高、中心点与原始 bounds 文本，另含类名、资源标识、文本、内容描述、七项交互标志、保留标记、主定位与候选），验证：单测断言排序键为 (顶边 y, 左边 x, 层级深度) 升序，且被展示裁剪元素仍出现在分组中并带保留标记为假
- [x] 2.5 算法层边界自检：模块 MUST NOT import apps/django/engines，验证：`python tools/gen_arch_stats.py --check-boundaries` 通过，且模块导入清单仅含同层算法模块与标准库

## 3. 文档与工具同步

- [x] 3.1 契约文档同步：核实归档后无「引擎协议」接口文档需要改（`API-执行引擎` 是已下线的 test_runner 文档，不列引擎协议；架构总览只提协议名不列签名），契约真相源为本变更的 engine-protocol delta，验证：`openspec show add-element-layering-core --json --deltas-only` 含该 MODIFIED 需求
- [x] 3.2 设备页面分析工具的内联算法副本（`scripts/vendor/`）加摘要比对检查（`scripts/check_vendor.py`，与算法层来源文件的 sha 对照），验证：`python .agents/skills/device-page-analysis/scripts/check_vendor.py` 退出码 0 且两个副本均报「一致」；改动任一来源文件后退出码变 1

## 4. 门禁

- [x] 4.1 落单门禁全量执行：`python manage.py check`、`ruff check`、`pytest tests/graybox/unit tests/arch -q`、`python tools/gen_arch_stats.py --check-boundaries`，验证：全部通过且无新增告警