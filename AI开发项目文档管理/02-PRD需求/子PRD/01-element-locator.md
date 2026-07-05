# 子PRD — 元素定位 (Element Locator)

> 关联模块：`apps/element_locator/` · 前端：`frontend/src/modules/element-locator/`
> 关联全局：`../全局PRD.md` · 关联用例：`../子PRD/03-case-manager.md` · 关联执行：`../子PRD/04-test-runner.md`
> 版本：v2.0 · 状态：草稿 · 日期：2026-06-30

---

## 1. 模块功能目标

元素定位模块是测试平台的 UI 可视化交互中枢，承担以下核心职责：

1. **设备 UI 实时查看**：通过 WebSocket 持续拉取手机截图并在浏览器中实时渲染，延迟 ≤500ms，帧率 ≥2fps
2. **UI 层级抓取**：一键抓取设备当前页面的完整 UI 层级树（dump hierarchy），结构化存储所有元素节点
3. **XPath 自动生成**：为页面中每个元素自动生成 8 种 XPath 定位策略，按匹配数排序，确保唯一而稳定的定位表达式
4. **测试点标记**：支持在元素上标记"测试点"作为可测试锚点，为用例工程（case-manager）和执行引擎（test-runner）提供标准化的元素定位数据

### 1.1 模块边界

```
device-pool (设备连接)
      │
      ▼ 提供 u2 设备实例
element-locator
      │
      ├─ 元素 / XPath / 页面流  ──→  case-manager (用例工程, 读 Element)
      │
      └─ WebSocket 截图流  ──→  test-runner (执行引擎, 可选辅助)
```

---

## 2. 功能清单与概述

| 编号 | 功能名称 | 优先级 | 一句话描述 |
|:--:|------|:--:|------|
| F-01 | UI 层级抓取与截图 | P0 | 一键抓取设备当前页面完整 UI 树节点 + 截图，创建 Page/Element 记录 |
| F-02 | 元素定位与 XPath 生成 | P0 | 为每个元素自动生成 8 种 XPath 候选，按匹配数升序排列，支持别名标注和测试点标记 |
| F-03 | 页面流程管理 | P0 | 记录页面间跳转关系（from → to + 触发元素），支持增删查 |
| F-04 | 实时截图流 | P0 | WebSocket 实时推送设备截图，前端 Canvas 渲染 + 元素高亮交互覆盖层 |

---

## 3. 功能详细规格

---

### 3.1 F-01：UI 层级抓取与截图

#### 3.1.1 需求定义

用户点击"抓取 UI"按钮后，后端通过 uiautomator2 获取设备当前页面的完整 UI 层级树（XML/JSON），同时截取设备屏幕图片保存到服务端。解析层级树后创建 Page 记录和所有 Element 记录。

#### 3.1.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 抓取成功率 | dump hierarchy 成功 / 尝试 | ≥98% |
| 抓取耗时 | 按钮点击 → 前端渲染完成 | ≤3s |
| 元素解析完整性 | 解析到 Element 数 / UI 树节点数 | 100%（跳过非关键系统节点） |

#### 3.1.3 触发条件

- 用户在 element-locator 页面点击「抓取 UI」按钮
- 前置条件：已通过 device-pool 连接到设备

#### 3.1.4 业务规则

```
用户点击「抓取 UI」
    ├─ 无设备连接 → ❌ 提示「请先在设备管理中连接设备」
    ├─ 设备离线 → ❌ 提示「设备已离线」
    └─ 设备可用 →
        1. POST /api/elements/dump
        2. 后端执行：
           a. device.dump_hierarchy() → 获取 UI 层级 XML
           b. device.screenshot() → 保存截图到 data/screenshots/
           c. 解析 XML → 遍历所有可交互节点 → 创建 Element 记录
           d. 创建 Page 记录 (package/activity/element_count/screenshot_path)
        3. 返回：{ok, page_id, element_count, screenshot_path}
        4. 前端发起 WebSocket 连接获取实时截图 + 拉取元素列表
```

**节点过滤规则**：
- 仅保存 `clickable=true` 或 `long-clickable=true` 或 `focusable=true` 的节点
- 跳过 `class='android.widget.FrameLayout'` 且 `bounds=[0,0,0,0]` 的空节点
- 系统状态栏/导航栏节点：保留但标记 `is_system=true`（前端默认折叠）

#### 3.1.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| 抓取按钮 | 页面顶部工具栏"抓取 UI"按钮，loading 状态显示 spinner |
| 截图区 | 左侧大面积 Canvas，通过 WebSocket 接收实时截图流渲染 |
| 元素列表 | 右侧 el-table，列：元素类型图标 / class / text / resource-id / 可点击 / 已标记测试点 |
| 无连接状态 | 未连接设备时抓取按钮 disabled + 提示"请先连接设备" |

#### 3.1.6 后端接口要求

| 接口 | 核心行为 |
|------|---------|
| `POST /api/elements/dump` | dump_hierarchy → screenshot → 解析节点 → 创建 Page + Element 记录。详见附录 §4.3.1 |
| `GET /api/elements/pages/{page_id}/items` | 获取某页面的元素列表，支持 ?filter=clickable|text|testpoint。详见附录 §4.3.4 |

---

### 3.2 F-02：元素定位与 XPath 生成

#### 3.2.1 需求定义

对 UI 层级抓取到的每个元素节点，自动生成 8 种 XPath 候选定位策略。每种策略在页面全局范围内计算匹配数（count），按 count 升序排列。用户在截图 Canvas 上点击元素时，右侧面板展示该元素的所有 XPath 候选，并支持复制和"加入步骤"。

#### 3.2.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| XPath 生成策略数 | 每元素至少 3 种有效策略 | ≥3 |
| 唯一定位率 | count=1 的策略占比 | ≥60% |
| 交互延迟 | Canvas 点击 → XPath 展示 | ≤200ms |

#### 3.2.3 触发条件

- 用户在截图 Canvas 上点击一个高亮元素区域
- 前端根据点击坐标反向映射 → 查找命中元素 → 请求该元素的 XPath 候选列表

#### 3.2.4 业务规则

**8 种 XPath 策略生成算法**（`gen_xpath_candidates`）：

```
对每个元素 el：
1. resource-id 策略    //*[@resource-id="{el.resource_id}"]
2. text 策略            //*[@text="{el.text}"]
3. content-desc 策略    //*[@content-desc="{el.content_desc}"]
4. class + index 策略   //{el.class}[{el.index}]（兄弟节点中的位置）
5. resource-id + text 组合策略  //*[@resource-id="{rid}" and @text="{text}"]
6. resource-id any 策略  //*[contains(@resource-id, "{last_segment}")]
7. text any 策略        //*[contains(@text, "{text}")]
8. class 策略           //{el.class}
```

**排序规则**：
- 每种策略在当前页面全局执行 `xpath` 匹配计数
- 按 `count` 升序排列（count=1 最精确，优先推荐）
- 去重：相同 XPath 字符串只保留一条
- 策略有值才生成（如无 text 则跳过策略 2）

#### 3.2.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| Canvas 渲染 | ScreenshotView.vue：设备尺寸 1440×3040 按 0.3 倍缩放绘制，可点击元素绘制蓝色半透明矩形覆盖层 |
| 元素命中 | 点击 Canvas → 反向映射坐标到设备像素 → 查找 bounds 包含该坐标的 Element → 红色高亮该元素 |
| XPath 面板 | XPathTable.vue：展示选中元素属性（class/text/ID/bounds），el-table 展示 XPath 列表（策略名 / XPath / 匹配数）|
| 加入步骤 | 每条 XPath 右侧"+"按钮 → 触发 `add-step` 事件，将 XPath + 元素信息传入 case-manager 的步骤列表 |
| 测试点标记 | 元素行开关 "标记为测试点"（`is_test_point`），标记后在元素列表中显示星标图标 |
| 别名标注 | 元素支持自定义别名（`alias` 字段），可编辑 |

#### 3.2.6 后端接口要求

| 接口 | 核心行为 |
|------|---------|
| `PUT /api/elements/items/{el_id}` | 更新元素 alias/tags/notes/is_test_point。详见附录 §4.3.5 |
| 截图 WebSocket | `ScreenshotStream` 引擎以 0.5s 间隔推送 base64 截图。详见附录 §4.3 |

---

### 3.3 F-03：页面流程管理

#### 3.3.1 需求定义

在多次 UI 抓取后，记录设备上各页面之间的跳转关系（从哪个页面 → 点击哪个元素 → 跳转到哪个页面），形成页面导航流程图。

#### 3.3.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 流程自动发现 | 每次 dump 后自动匹配上一页 | ≥80% 成功率 |
| 流程可视化 | 页面之间跳转关系一目了然 | — |

#### 3.3.3 触发条件

- 每次抓取 UI 时，后端自动对比上一页的 Package/Activity
- 用户手动在流程管理页创建/删除流程

#### 3.3.4 业务规则

```
每次 dump_page 后：
1. 获取当前 page_id 和上一页 last_page_id
2. if last_page_id != page_id:
     a. 在上一页的元素中查找最近一次点击的元素（从 action 历史）
     b. 创建 PageFlow(from_page=last_page, to_page=page, trigger_element=clicked_el)
3. 手动管理：
   - GET /api/elements/flows → 列出所有流程
   - POST /api/elements/flows → 手动创建流程 (from/to/trigger/action)
   - DELETE /api/elements/flows/{flow_id} → 删除流程
```

#### 3.3.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| 流程列表 | 页面底部 Tab "页面流程"：el-table 展示 来源页 → 触发元素 → 目标页 |
| 新建流程 | 对话框：选择来源页 / 目标页 / 触发元素 / 动作类型（click/long-click/input）|

#### 3.3.6 后端接口要求

| 接口 | 核心行为 |
|------|---------|
| `GET /api/elements/flows` | 列出所有流程，含 from_page/to_page/trigger_element 关联数据。详见附录 §4.3.7 |
| `POST /api/elements/flows` | 创建新流程。详见附录 §4.3.7 |
| `DELETE /api/elements/flows/{flow_id}` | 删除指定流程。详见附录 §4.3.8 |

---

### 3.4 F-04：WebSocket 实时截图流

#### 3.4.1 需求定义

设备连接成功后，通过 WebSocket 持续推送设备实时截图（base64 编码）到前端，前端 Canvas 渲染并叠加元素高亮交互覆盖层。推送频率 2fps（500ms 间隔），自动启停：有客户端连接时推送，无客户端时停止。

#### 3.4.2 需求目标

| 目标 | 衡量方式 | 目标值 |
|------|----------|:--:|
| 截图延迟 | 设备截图 → 前端 Canvas 渲染 | ≤500ms |
| 截图帧率 | 每秒推送帧数 | ≥2fps |
| 自动启停 | 无客户端时 CPU 零消耗 | — |

#### 3.4.3 触发条件

- 前端 element-locator 页面挂载时自动建立 WebSocket 连接
- component unmount 时自动断开
- 设备连接成功（POST /api/devices/{serial}）后

#### 3.4.4 业务规则

```
ScreenshotStream 引擎：
1. 维护 clients 集合（WebSocket consumer 列表）
2. 广播循环：
   - 每 SCREENSHOT_INTERVAL（默认 0.5s）执行一次
   - 调用 device.screenshot_b64() → 获取 base64 JPEG
   - 构造 JSON: {type: "screenshot", data: "base64...", timestamp: ...}
   - 发送给所有 clients
3. 生命周期：
   - 第一个 client 连接 → 启动广播循环（asyncio.create_task）
   - 最后一个 client 断开 → 取消广播任务
4. 异常处理：
   - 截图失败 → 发送 {type: "error", message: "..."}
   - 设备断连 → 发送通知 → 停止广播
```

#### 3.5.5 前端交互要求

| 变动项 | 描述 |
|--------|------|
| WebSocket 连接 | ws://localhost:8765/ws/screenshot，onmessage 更新 Canvas |
| Canvas 渲染 | 1440×3040 设备尺寸 scale=0.3 缩放，imageSmoothingEnabled=true |
| 元素覆盖层 | 遍历页面元素 bounds，绘制蓝色半透明矩形（非选中）/ 红色半透明矩形（选中） |
| 重连机制 | WS 断开后 3s 自动重连，最多 5 次 |

#### 3.5.6 后端接口要求

| 接口 | 核心行为 |
|------|---------|
| WebSocket `/ws/screenshot` | ScreenshotConsumer 注册到 ScreenshotStream。详见附录 §4.3 |

---

## 4. 附录

### 4.1 数据模型

#### 4.1.1 el_pages（UI 页面快照）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BigAutoField | PK | 自增主键 |
| `device` | FK(Device) | SET_NULL | 关联设备（设备删除时不删除 Page） |
| `label` | CharField(500) | — | 页面标签（用户可编辑） |
| `package` | CharField(500) | — | App 包名 |
| `activity` | CharField(500) | — | 当前 Activity |
| `screenshot_path` | CharField(1000) | — | 截图文件路径 |
| `element_count` | IntegerField | default=0 | 元素数量 |
| `created_at` | DateTimeField | auto_now_add | 创建时间 |

#### 4.1.2 el_elements（UI 元素）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BigAutoField | PK | 自增主键 |
| `page` | FK(Page) | CASCADE | 所属页面 |
| `class_name` | CharField(200) | — | 元素的 class 属性 |
| `text_val` | CharField(500) | — | 元素的 text 属性 |
| `content_desc` | CharField(500) | — | 元素的 content-desc 属性 |
| `resource_id` | CharField(500) | — | 元素的 resource-id 属性 |
| `bounds` | CharField(200) | — | 元素边界 [x1,y1][x2,y2] |
| `xpath_candidates` | TextField | default='[]' | JSON 格式 XPath 候选列表 |
| `clickable` | BooleanField | default=False | 是否可点击 |
| `enabled` | BooleanField | default=True | 是否可用 |
| `alias` | CharField(200) | — | 用户自定义别名 |
| `tags` | CharField(500) | — | 标签 |
| `is_test_point` | BooleanField | default=False | 是否标记为测试点 |
| `notes` | TextField | — | 备注 |

**唯一约束**：`(page, resource_id, text_val, bounds)`

#### 4.1.3 el_page_flows（页面流程）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | BigAutoField | PK | 自增主键 |
| `from_page` | FK(Page) | CASCADE | 来源页面 |
| `to_page` | FK(Page) | CASCADE | 目标页面 |
| `trigger_element` | FK(Element) | SET_NULL | 触发跳转的元素 |
| `trigger_action` | CharField(50) | default='click' | 触发动作 |
| `created_at` | DateTimeField | auto_now_add | 创建时间 |

---

### 4.2 状态说明

| 对象 | 状态 | 含义 |
|------|------|------|
| Page | — | 无状态，纯数据快照 |
| Element | `is_test_point` | 标记后可用于用例工程提取为测试锚点 |
| PageFlow | — | 无状态，记录页面间跳转关系 |
| ScreenshotStream | broadcasting / idle | 有客户端时 broadcasting，无客户端时 idle |

---

### 4.3 API 接口规格

#### 4.3.1 接口总览

| # | 方法 | 路径 | 功能 |
|---|------|------|------|
| 1 | POST | `/api/elements/dump` | UI 层级抓取 |
| 2 | POST | `/api/elements/action` | 执行设备操作 (click/input) |
| 3 | GET | `/api/elements/pages` | 页面列表 |
| 4 | PUT/DELETE | `/api/elements/pages/{page_id}` | 更新/删除页面 |
| 5 | POST | `/api/elements/pages/clear` | 清空所有数据 |
| 6 | GET | `/api/elements/pages/{page_id}/items` | 页面元素列表 |
| 7 | PUT | `/api/elements/items/{el_id}` | 更新元素 |
| 8 | GET/POST | `/api/elements/flows` | 流程列表/创建 |
| 9 | DELETE | `/api/elements/flows/{flow_id}` | 删除流程 |
| — | WS | `/ws/screenshot` | 实时截图流 |

#### 4.3.2 核心接口示例

**POST /api/elements/dump** (UI 抓取)

Request: 无参数
Response 200:
```json
{
  "ok": true,
  "page_id": 42,
  "element_count": 87,
  "package": "com.example.app",
  "activity": ".MainActivity",
  "screenshot_path": "data/screenshots/page_42.png"
}
```

**GET /api/elements/pages/{page_id}/items?filter=clickable**

Response 200:
```json
{
  "ok": true,
  "page_id": 42,
  "elements": [
    {
      "id": 150,
      "class_name": "android.widget.Button",
      "text_val": "登录",
      "resource_id": "com.example:id/btn_login",
      "bounds": "[540,1200][720,1350]",
      "clickable": true,
      "is_test_point": false,
      "alias": "",
      "xpath_candidates": [
        {"type": "resource-id", "xpath": "//*[@resource-id='com.example:id/btn_login']", "count": 1},
        {"type": "text", "xpath": "//*[@text='登录']", "count": 2}
      ]
    }
  ]
}
```

---

### 4.4 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|:--:|
| **性能** | UI 抓取耗时 | ≤3s |
| **性能** | XPath 生成（100 元素） | ≤500ms |
| **性能** | 截图帧率 | ≥2fps |
| **性能** | 截图延迟 | ≤500ms |
| **可靠性** | WebSocket 断线重连 | 3s 内自动重连，最多 5 次 |
| **可靠性** | 截图失败降级 | 不崩溃，显示上次成功截图 + 错误提示 |

---

### 4.5 非目标（Non-goals）

| 功能 | 原因 | 归属 |
|------|------|------|
| AI 智能元素识别（图像识别定位） | v4 功能 | ai-assistant |
| XPath 编辑/手动编写 | 当前以自动生成为核心 | 后续迭代 |
| 多设备同时截图对比 | 单设备场景优先 | v3 |
| UI 变更检测/视觉回归 | 独立产品能力 | v4 |

---

### 4.6 里程碑

| 阶段 | 交付物 | 对应功能 |
|------|------|----------|
| v1 ✅ | 基础 UI 抓取 + XPath 生成 + Canvas 渲染 + WS 截图流 | F-01, F-02, F-04 |
| v2 当前 | 页面流程可视化 + 元素标注增强 + 截图交互优化 | F-03 + 优化 |
| v3 | 多设备截图对比 + UI 变更检测 | — |

---

## 变更记录

| 版本 | 日期 | 变更类型 | 变更摘要 |
|------|------|----------|----------|
| v1.0 | 2026-06-30 | — | v1 实现完成：dump / XPath / WebSocket / Canvas |
| v2.0 | 2026-06-30 | 重写 | 统一 6 维度结构，补充业务规则和前后端交互细节 |
