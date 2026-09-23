## Why

检查器的「元素名称」内联重命名在保存时**会串名**：`store.saveToElements` 把自定义名按 `resource_id` 组装成 `aliases`（`{rid: name}`），后端 `save_snapshot_to_elements` 也按 `resource_id` 回填（`apps/device_inspector/api.py:293-297`）。当同一个页面里有多个元素共享同一 `resource_id`（列表项、同构行很常见）时，这些元素会**一起**拿到最后写入的那个名称，用户为每个元素分别起的名字丢失。

## What Changes

- 检查器改为按**元素下标**回填名称：请求新增 `element_aliases: [{index, name}]`（index = `dump_json.elements` 下标，与 `element_ids` 同源），后端按原始下标精确写入对应元素
- 保留既有的 `aliases: {resource_id: name}` 通道不变（AI 助手工具 `save_page_to_elements` 仍按 rid 传参，向后兼容）
- 优先级：逐元素名称**覆盖** rid 别名（更具体的口径优先）
- **BREAKING**：无（新增可选字段；旧请求形状仍可用）

## 明确移出本变更范围

- 不改 `aliases`（rid 口径）的既有语义与调用方
- 不改元素定位侧的 `alias` 回退规则（`alias or text or resource_id`）
- 不做「按 rid 批量改名」的批量工具（用户要的是逐元素命名）
- 不在本变更内改元素定位 UI 的别名编辑（那是它自己的写入口）

## 关联文档

- 需求编号：`PRD-03-设备检查器`
- 相关既有要求：`device-inspector-page`「元素表格勾选驱动筛减保存」（本次为它补一条同名 rid 的口径）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `device-inspector-page`: 修改「元素表格勾选驱动筛减保存」，补「同名 `resource-id` 的多个元素逐元素回填名称、互不覆盖」

## Impact

- 后端 2 文件：`apps/device_inspector/api.py`（新入参 + 按原始下标回填）、`apps/device_inspector/views.py`（透传 `element_aliases`）
- 前端 1 文件：`frontend/src/modules/device-inspector/store.ts`（用下标口径组装 `element_aliases`，不再发 rid 口径的 `aliases`）
- 测试：新增 `tests/graybox/integration/test_inspector_save_element_aliases.py`
- 规格：`device-inspector-page` 1 份 delta（1 改）
- 迁移：无