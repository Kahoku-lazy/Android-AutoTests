## Why

设备检查器当前只按「位置启发式的 6 层页面分区」展示元素，回答不了两个真问题：每个元素属于什么类型的控件、它能不能被稳定定位。本轮实测（同一台真机 4 个页面）显示：元素库里 33.9% 的元素拿不到唯一的非位置型定位，而现有候选排序规则会把位置型 xpath 伪装成「唯一」（假唯一）。

要让这套「两级分组 + 主定位选择」成为平台能力，必须先解决一处既有的分层错配：引擎实现 import 算法层解析器（`engines/device/android/u2.py:21` 的 `from algorithms.hierarchy import parse_hierarchy_xml`，该文件自己注为「⚠️ 契约出入…待评审裁决」），并在引擎内完成层级解析。按「引擎只取数、解析归算法层」的口径，这一处必须纠正。

## What Changes

- **引擎只输出层级原始 XML，不做任何解析**：`UiEngine` 的层级取数方法改为返回**原始 XML 文本**，原「返回 Node 列表」的方法签名移除（**BREAKING**）。引擎实现随之删除解析器 import 与节点转换逻辑，`engines → algorithms` 反向依赖消失。
- **解析职责完全归算法层**：调用方拿原始 XML，用算法层的解析函数得到 Node 列表；平台内层级取数的唯一消费者是设备检查器采集编排，同一变更内改造完毕。
- **算法层新增元素分层规则模块**（纯函数，零 apps/django/engines 依赖）：
  - L1 四类：布局容器 / 滚动·集合容器 / 内容控件 / 其它（不属于以上三类的）；
  - L2 三类（仅作用于内容控件）：文本 / 图标 / 其它；
  - 七个细类：`text`、`text_empty`、`icon_font`、`icon_semantic`、`icon_bare`、`hotzone`、`shape`；
  - 主定位选择：先筛 `count==1` 且非位置型候选，再按 `resource-id > content-desc > combined > text > class` 取首条；无唯一候选时如实返回 `stable=false`（MUST NOT 用位置型 xpath 冒充唯一）。
- **不改变**：展示裁剪规则（纯容器 / 同 bounds 去重）、6 层页面分区算法、检查器现有端点与前端——它们保持不变，由后续两个变更分别处理。

## 关联文档

- PRD-03（设备检查器）
- PRD-00（需求总纲）

## Capabilities

### New Capabilities

- `element-layering`: 元素两级分组的分类规则、七个细类判据、主定位与唯一性口径（纯规则，供后端与前端共用同一真相源）。

### Modified Capabilities

- `engine-protocol`: 「感知标准化」需求改写——层级取数返回原始 XML 文本，引擎 MUST NOT 解析、MUST NOT 构造 Node 列表；解析由调用方经算法层完成。

## Impact

- 引擎：`engines/device/base.py`（协议层级取数签名改为原始 XML）、`engines/device/android/u2.py`（移除解析器 import 与节点转换，三层 fallback 收敛到新方法）、契约测试
- 调用方：`apps/device_inspector/service.py:86-95`（改为经算法层解析后再消费节点）
- 契约注释：`models/ui_nodes.py:3-4`（「构造职责在 engines」的表述需改为归算法层）
- 算法：新增 `algorithms/element_layers.py`；`algorithms/hierarchy.py`（解析器）、`algorithms/xpath.py` 不改
- 不涉及：`tools/dump_ui.py`（直接用 uiautomator2，不经引擎，无需改）、Django 端点、数据库、前端页面
- 文档：接口文档「API-执行引擎」需同步层级取数签名
- 测试：引擎契约测试、算法层单元测试（分类与主定位边界）、采集编排回归