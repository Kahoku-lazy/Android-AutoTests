# 模块测试方案 — 元素定位

> 关联子PRD：`02-PRD需求/子PRD-01-element-locator.md` · 版本：v1.0 · 日期：2026-06-30

---

## 1. 测试范围

| 类型 | 内容 |
|------|------|
| 接口测试 | 11 个 REST + 1 个 WebSocket |
| 前端测试 | 截图渲染、XPath 候选展示、重叠元素菜单 |
| 边界测试 | 无设备、超大截图、深层嵌套 XML |

---

## 2. 接口测试

### 2.1 dump 操作

| 编号 | 用例 | 方法 | 路径 | 输入 | 预期 |
|:--:|------|------|------|------|------|
| EL-API-01 | 正常 dump | POST | /api/elements/dump | 设备在线 | 200，返回 page_id + elements 数量 |
| EL-API-02 | 无设备 dump | POST | /api/elements/dump | 无 ADB 设备 | 503，error "无可用设备" |
| EL-API-03 | dump 截图不完整 | POST | /api/elements/dump | 设备在线 | screenshot.png 存在且 >10KB |

### 2.2 页面管理

| 编号 | 用例 | 方法 | 路径 | 预期 |
|:--:|------|------|------|------|
| EL-API-04 | 获取页面列表 | GET | /api/elements/pages | 200，返回数组（含空数组场景） |
| EL-API-05 | 更新页面标签 | PUT | /api/elements/pages/{id} | 200，label 已更新 |
| EL-API-06 | 删除页面 | DELETE | /api/elements/pages/{id} | 200，关联 elements + flows 级联删除 |
| EL-API-07 | 清空全部页面 | POST | /api/elements/pages | 200，所有 page/element/flow 清空 |

### 2.3 元素管理

| 编号 | 用例 | 方法 | 路径 | 预期 |
|:--:|------|------|------|------|
| EL-API-08 | 获取元素列表 (全部) | GET | /api/elements/pages/{id}/items?filter=all | 返回全量 |
| EL-API-09 | 获取可点击元素 | GET | /api/elements/pages/{id}/items?filter=clickable | 仅返回 clickable=true |
| EL-API-10 | 获取文本元素 | GET | /api/elements/pages/{id}/items?filter=text | 仅返回含 text 属性 |
| EL-API-11 | 更新元素元数据 | PUT | /api/elements/items/{id} | 200，alias/tp_label 已更新 |

### 2.4 页面跳转

| 编号 | 用例 | 方法 | 路径 | 预期 |
|:--:|------|------|------|------|
| EL-API-12 | 创建跳转记录 | POST | /api/elements/flows | 200，flow 记录创建 |
| EL-API-13 | 删除跳转 | DELETE | /api/elements/flows/{id} | 200 |

### 2.5 WebSocket 截图流

| 编号 | 用例 | 方向 | 预期 |
|:--:|------|------|------|
| EL-WS-01 | 连接成功 | ws://host/ws/screenshot | WebSocket 握手成功 |
| EL-WS-02 | 接收帧 | S→C | 收到 JSON: type=screenshot, image=base64, ts=ISO8601 |
| EL-WS-03 | 帧率达标 | 统计 60s | ≥2fps (≥120 帧) |
| EL-WS-04 | 心跳保活 | C→S 任意文本 | 连接不超时断开 |
| EL-WS-05 | 断连后重连 | 断网→恢复 | 自动重连，恢复帧流 |

---

## 3. XPath 选择器测试

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| EL-XP-01 | 8 种策略生成 | 点击唯一元素 | 返回 8 种 XPath，匹配数升序 |
| EL-XP-02 | count=1 排第一 | 点击唯一登录按钮 | 最优策略 count=1 排第一位 |
| EL-XP-03 | 重叠元素右键菜单 | 点击重叠区域 | 弹出列表显示所有层叠元素 |
| EL-XP-04 | text 属性定位 | 点击含 text 元素 | `//*[@text='xxx']` 在候选列表中 |
| EL-XP-05 | resource-id 定位 | 点击含 resource-id 元素 | `//*[@resource-id='xxx']` 在候选中 |
| EL-XP-06 | 无属性元素 | 点击纯容器 View | 生成 class+index 策略 |
| EL-XP-07 | 深层嵌套 | 点击 10 层嵌套内元素 | 正确生成，不超时 |

---

## 4. 前端测试

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| EL-UI-01 | 截图渲染 | 连接设备 | 手机截图正确显示在页面中 |
| EL-UI-02 | 截图刷新 | 等待 2s | 截图自动更新 |
| EL-UI-03 | XPath 候选展示 | 点击元素 | 右侧面板显示 8 条候选 |
| EL-UI-04 | 候选点击高亮 | 点击候选 | 截图叠加层高亮对应元素 |
| EL-UI-05 | 添加为步骤 | 点击"添加为测试步骤" | 跳转用例编辑页，步骤已填入 |
| EL-UI-06 | 右键菜单交互 | 右键点击重叠元素 | 弹出列表 + 点击选项切换选中 |

---

## 5. 边界与异常测试

| 编号 | 用例 | 场景 | 预期 |
|:--:|------|------|------|
| EL-EDGE-01 | 超大 XML hierarchy | dump 一个复杂页面 (>5000 节点) | 不超时，不 OOM |
| EL-EDGE-02 | 空页面 | dump 白屏 | 返回 0 elements |
| EL-EDGE-03 | 快速连续 dump | 1 秒内 dump 3 次 | 不崩溃，每次返回独立结果 |
| EL-EDGE-04 | 页面 ID 不存在 | GET /api/elements/pages/{不存在的ID}/items | 404 |
| EL-EDGE-05 | 元素 ID 不存在 | PUT /api/elements/items/{不存在} | 404 |
| EL-EDGE-06 | 截图太大 | 4K 分辨率设备 | 传输不超时，前端正常渲染 |

---

## 变更记录

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-06-30 | 基于子PRD v1.0 输出，覆盖 11 API + 1 WS + 6 UI + 6 边界 |
