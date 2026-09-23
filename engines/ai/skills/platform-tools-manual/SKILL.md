---
name: platform-tools-manual
description: |
  平台 AI 可调用工具（17 个）的完整操作手册：设备管理/设备控制/设备信息/设备检查器/视觉识别/页面流工具六类的用途、只读/写标记、关键入参与返回，以及设备控制场景的工具序列与写操作落库校验铁律。
  Keywords: 平台工具, 工具手册, 工具用途, 工具组合, 工具序列, 落库校验, tool manual
  Trigger: 规划/执行/验收需要了解平台有哪些工具、某个工具怎么用、如何组合工具达成目标、写操作后如何校验时查阅。
---

# 平台工具操作手册

本手册汇总平台 AI 可调用的全部工具（来源 `apps/ai_assistant/tools.py`），供规划/执行/验收模型查阅，据此选择正确工具与组合。

> 约定：read_only=True 为查询工具（无副作用，可反复核实）；False 为写/控制工具（改变设备状态）。

## 一、工具总览（6 类 17 个）

> 分类即工具箱「整类启停」的单位，故按工具性质分组：台账 / 控制（有手机副作用）/ 信息（只读连设备）。

### 1. 设备管理（3）— 设备池台账，不操作手机
| 工具 | 只读 | 用途 |
|------|:--:|------|
| list_devices | ✅ | 查全部设备及状态/占用/是否当前 |
| acquire_device | ❌ | 锁定一台在线设备独占测试 |
| release_device | ❌ | 释放已锁定设备回设备池 |

### 2. 设备控制（8）— 会在手机上产生副作用，可整类停用
| 工具 | 只读 | 用途 |
|------|:--:|------|
| app_control | ❌ | 启停指定 App（action=start_app/stop_app，需 package） |
| tap_screen | ❌ | 像素坐标点击或长按（mode=click/long_click，需 x/y） |
| swipe_screen | ❌ | 按方向滑动（direction=up/down/left/right，distance 默认 500） |
| press_key | ❌ | 按返回键（BACK） |
| input_text | ❌ | 向输入框输入文本（clear_first 默认 true） |
| click_ratio | ❌ | 归一化坐标点击（nx/ny 0~1） |
| drag_ratio | ❌ | 归一化坐标拖动（起终点 0~1） |
| xpath_action | ❌ | 按 xpath 检查存在 / 读文本 / 点击 / 长按 |

### 3. 设备信息（2）— 只读，但要连设备取数
| 工具 | 只读 | 用途 |
|------|:--:|------|
| list_apps | ✅ | 列设备已装应用包名 |
| current_app | ✅ | 只读当前前台 App（package/activity/pid），不动设备 |

### 4. 设备检查器（1）
| 工具 | 只读 | 用途 |
|------|:--:|------|
| screenshot_page | ✅ | 截图返回图片（给视觉模型看图）；`keep_local=true` 时 summary 带回 screenshot_path / screenshot_name |

### 5. 视觉识别工具（1）
| 工具 | 只读 | 用途 |
|------|:--:|------|
| ocr_page | ✅ | OCR 识别设备当前页面文本，返回文本/置信度/角点与归一化中心点；`texts` 可收窄查找范围 |

### 6. 页面流工具（2）
| 工具 | 只读 | 用途 |
|------|:--:|------|
| list_page_flows | ✅ | 一次列出**全部**页面流文档（不截断），每条含目录完整路径与层级深度 |
| get_page_flow | ✅ | 取页面流文档语义摘要 |

## 二、链路归属

- **设备控制链路**：planner 用 DEVICE_PLANNER_TOOLS（list_page_flows / get_page_flow）读页面流；executor 用 VISION_TOOLS（14 个：设备管理 3 + 设备控制 8 + 设备信息 2 + screenshot_page）控制设备；verifier 用 VERIFIER_TOOLS（screenshot_page）截图验收。
- 平台任务链路已弃用（业务工具删减后无可用工具）。

## 三、按目标的推荐工具序列

- ① 选设备：list_devices 查设备，取 status=ONLINE 设备的 serial；必要时 acquire_device 锁定、release_device 释放。
- ② 读页面流：list_page_flows 一次列出全部文档（`query` 可按标题/ID 收窄；每条含 `directory_path` 与 `directory_depth`，未归类文档路径为空串）→ get_page_flow 读语义摘要（节点/页面/跳转关系/元素 xpath），识别测试点（目标页面/节点）。
- ③ 设备控制：app_control 启停 App、press_key 返回上一页、swipe_screen 滑动、input_text 输入文本、current_app 只读当前前台（不动设备）；点击优先 xpath_action(action=click, xpath=...)（页面流给了 xpath 时），否则用 click_ratio 视觉归一化坐标点击。
- ④ 检查/验收：xpath_action(action=exists/get_text) 断言元素存在 / 读文本；screenshot_page 截图看当前画面二次确认。

## 四、关键工具入参与返回约定

- **app_control(serial, action, package)**：action ∈ start_app/stop_app，二者都需 package；每次返回 package/activity 用于判断页面是否跳转。
- **tap_screen(serial, mode, x, y)**：mode ∈ click/long_click，x/y 为**像素**坐标（0 视为未提供）；每次返回 package/activity。
- **swipe_screen(serial, direction, distance)**：direction ∈ up/down/left/right（默认 up），distance 默认 500；每次返回 package/activity。
- **press_key(serial)**：按返回键 BACK；每次返回 package/activity。
- **input_text(serial, text, clear_first)**：clear_first 默认 true（先清空输入框）；每次返回 package/activity。
- **current_app(serial)**：只读当前前台，返回 package/activity/pid，不改变设备状态。
- **xpath_action(serial, action, xpath, index, timeout)**：action ∈ exists/get_text/click/long_click；exists 返回 {"exists": bool}，get_text 返回 {"text": str}，click/long_click 返回 {"clicked": bool, "current": {...}}。
- **click_ratio(serial, nx, ny)** / **drag_ratio(serial, nx1, ny1, nx2, ny2)**：归一化坐标（0~1），工具换算像素。
- **get_page_flow(doc_id)**：返回页面流语义摘要（nodes / elements(含 xpath) / links / paths）。

## 五、写/控制操作铁律

1. 控制操作（app_control / tap_screen / swipe_screen / press_key / input_text / click_ratio / drag_ratio / xpath_action）执行后，用 screenshot_page 截图或 xpath_action(exists/get_text) 二次确认结果。
2. 上一步返回的 id（serial / doc_id / page_id / element_id）作为下一步入参，不要臆造 id。
3. 查询工具（read_only=True：list_devices / list_apps / ocr_page / screenshot_page / list_page_flows / get_page_flow）无副作用，可反复调用核实。
