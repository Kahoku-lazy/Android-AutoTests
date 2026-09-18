## MODIFIED Requirements

### Requirement: 操作原语契约
引擎实现 MUST 提供 click、long_click、swipe、input_text、press_key、shell、start_app、stop_app 操作原语；语义 SHALL 与契约一致（坐标为设备像素）。MUST 额外提供 click_xpath、long_click_xpath（按 XPath 定位第 index 个匹配元素中心后执行点击/长按，返回是否命中）。

#### Scenario: 操作转发
- **WHEN** 上层调用任一操作原语
- **THEN** 引擎按契约语义将该操作执行到设备连接层

#### Scenario: XPath 定位操作
- **WHEN** 上层调用 click_xpath 或 long_click_xpath
- **THEN** 引擎按 XPath 匹配第 index 个元素并点击/长按，越界返回 False

## ADDED Requirements

### Requirement: Toast 完整能力
引擎 MUST 提供 get_toast_message（读取当前 toast 文本，无则空字符串）与 reset_toast（清空 toast 缓冲）；两者受 capabilities.toast_wait 门控，不支持时上层 SHALL 降级。

#### Scenario: 读取 toast
- **WHEN** 上层调用 get_toast_message
- **THEN** 返回当前 toast 文本（无则空字符串）

### Requirement: 分辨率查询
引擎 MUST 提供 get_resolution 返回设备物理分辨率 (width, height)，供上层做坐标换算；实现不得向调用方泄漏引擎特有数据结构。

#### Scenario: 获取分辨率
- **WHEN** 上层调用 get_resolution
- **THEN** 返回设备 (width, height) 整数元组
