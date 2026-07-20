# 元素定位 - 设备未连接呼吸动画

**日期**: 2026-07-20 | **范围**: `ScreenshotView.vue` 单文件

## 需求

当没有选择/连接设备时，设备截图栏显示 anime.js "设备未连接~" 呼吸浮动动画，替代当前静态占位符。

## 动画规格

| 元素 | 动画 | 参数 |
|------|------|------|
| 📱 图标 | translateY 浮动 | ±8px, 2.5s loop, easeInOutSine |
| "设备未连接~" 标题 | opacity 呼吸 | 0.6 ↔ 1, 与浮动同频 |
| 装饰圆环 x2 | scale 缩放呼吸 | 不同速率，增加层次 |
| 提示文字 | 静态 | 不变 |

## 实现

- 文件：`frontend/src/modules/element-locator/components/ScreenshotView.vue`
- 新增 `startNoDeviceAnimation()` / `stopNoDeviceAnimation()` 函数
- 用 `watch(wsState)` 在 `no_device` 状态时触发动画，其他状态停止
- 仅当 `wsState === 'no_device'` 且 `screenshotUrl` 为空时渲染动画 DOM
- 改动约 40 行
