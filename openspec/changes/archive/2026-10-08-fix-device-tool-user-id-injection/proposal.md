## Why

执行模型跑测工具第一次真机运行就暴露：引擎自带的 9 个设备动作工具**全部调用失败**，错误统一为 `got an unexpected keyword argument 'user_id'`。根因是工具包装层无条件给每次调用补 `user_id`（平台侧工具函数都带这个参数），而引擎自带的设备工具没有用户概念、签名里没有它——于是模型每次调工具都拿到错误，白烧 8 轮（费用已产生）。

## What Changes

- 工具包装层仅在**被包装函数确实声明了 `user_id`** 时才注入该参数；未声明的工具（引擎自带设备动作工具）不再被注入。
- 参数表剥离 `user_id` 的既有行为保持不变（模型仍看不到该参数）。
- 影响面：`engines/ai/tools/tool_wrapper.py` 一处；平台侧工具（都声明了 `user_id`）行为不变。

## 关联文档

无关联需求编号：缺陷修复（不改可观察的产品行为，只让原本就该成功的工具调用成功），故在变更元数据声明 `skip_specs: true`。

## Capabilities

### New Capabilities

（无。）

### Modified Capabilities

（无：修复的是实现缺陷，未改变任何需求的行为契约。）

## Impact

- **引擎**：`engines/ai/tools/tool_wrapper.py`。
- **平台**：零改动（平台工具函数仍带 `user_id`，注入行为不变）。
- **测试**：跑测工具的真机运行由「全部工具报错」变为「正常执行」；既有相关用例保持全绿。
