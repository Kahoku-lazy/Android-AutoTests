---
name: platform-tools-manual
description: |
  平台 AI 可调用工具（12 个）的完整操作手册：设备管理/设备检查器/工作流三类的用途、只读/写标记、关键入参与返回，以及设备控制场景的工具序列与写操作落库校验铁律。
  Keywords: 平台工具, 工具手册, 工具用途, 工具组合, 工具序列, 落库校验, tool manual
  Trigger: 规划/执行/验收需要了解平台有哪些工具、某个工具怎么用、如何组合工具达成目标、写操作后如何校验时查阅。
---

# 平台工具操作手册

本手册汇总平台 AI 可调用的全部工具（来源 `apps/ai_assistant/tools.py`），供规划/执行/验收模型查阅，据此选择正确工具与组合。

> 约定：read_only=True 为查询工具（无副作用，可反复核实）；False 为写/控制工具（改变设备状态）。

## 一、工具总览（3 类 12 个）

### 1. 设备管理（9）
| 工具 | 只读 | 用途 |
|------|:--:|------|
| get_online_devices | ✅ | 查在线设备列表（不含使用中） |
| list_devices | ✅ | 查全部设备及状态/占用/是否当前 |
| list_apps | ✅ | 列设备已装应用包名 |
| acquire_device | ❌ | 锁定一台在线设备独占测试 |
| release_device | ❌ | 释放已锁定设备回设备池 |
| device_action | ❌ | 设备 UI 动作：启停 App/点击/滑动/输入/返回/读前台 |
| click_ratio | ❌ | 归一化坐标点击（nx/ny 0~1） |
| drag_ratio | ❌ | 归一化坐标拖动（起终点 0~1） |
| xpath_action | ❌ | 按 xpath 检查存在 / 读文本 / 点击 / 长按 |

### 2. 设备检查器（1）
| 工具 | 只读 | 用途 |
|------|:--:|------|
| screenshot_page | ✅ | 截图返回图片（给视觉模型看图）；`keep_local=true` 时 summary 带回 screenshot_path / screenshot_name |

### 3. 工作流（2）
| 工具 | 只读 | 用途 |
|------|:--:|------|
| list_page_flows | ✅ | 列页面流文档 |
| get_page_flow | ✅ | 取页面流文档语义摘要 |

## 二、链路归属

- **设备控制链路**：planner 用 DEVICE_PLANNER_TOOLS（list_page_flows / get_page_flow）读页面流；executor 用 VISION_TOOLS（设备管理 9 个 + screenshot_page）控制设备；verifier 用 VERIFIER_TOOLS（screenshot_page）截图验收。
- 平台任务链路已弃用（业务工具删减后无可用工具）。

## 三、按目标的推荐工具序列

- ① 选设备：list_devices 查设备，取 status=ONLINE 设备的 serial；必要时 acquire_device 锁定、release_device 释放。
- ② 读页面流：list_page_flows 检索页面流文档 → get_page_flow 读语义摘要（节点/页面/跳转关系/元素 xpath），识别测试点（目标页面/节点）。
- ③ 设备控制：device_action(start_app/stop_app/back/swipe/input_text/current) 做启停/输入/返回；点击优先 xpath_action(action=click, xpath=...)（页面流给了 xpath 时），否则 click_ratio 视觉坐标点击。
- ④ 检查/验收：xpath_action(action=exists/get_text) 断言元素存在 / 读文本；screenshot_page 截图看当前画面二次确认。

## 四、关键工具入参与返回约定

- **device_action(serial, action, package, x, y, direction, distance, text, clear_first)**：action ∈ start_app/stop_app/click/long_click/swipe/back/input_text/current；每次返回 package/activity 用于判断页面是否跳转。
- **xpath_action(serial, action, xpath, index, timeout)**：action ∈ exists/get_text/click/long_click；exists 返回 {"exists": bool}，get_text 返回 {"text": str}，click/long_click 返回 {"clicked": bool, "current": {...}}。
- **click_ratio(serial, nx, ny)** / **drag_ratio(serial, nx1, ny1, nx2, ny2)**：归一化坐标（0~1），工具换算像素。
- **get_page_flow(doc_id)**：返回页面流语义摘要（nodes / elements(含 xpath) / links / paths）。

## 五、写/控制操作铁律

1. 控制操作（device_action / click_ratio / drag_ratio / xpath_action）执行后，用 screenshot_page 截图或 xpath_action(exists/get_text) 二次确认结果。
2. 上一步返回的 id（serial / doc_id / page_id / element_id）作为下一步入参，不要臆造 id。
3. 查询工具（read_only=True：list_devices / get_online_devices / list_apps / screenshot_page / list_page_flows / get_page_flow）无副作用，可反复调用核实。
