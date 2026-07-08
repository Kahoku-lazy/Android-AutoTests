# 子PRD — 元素定位 (Element Locator)

> 关联模块：`apps/element_locator/` · 前端：`frontend/src/modules/element-locator/`
> 关联全局：`../全局PRD.md` · 关联用例：`../子PRD/03-case-manager.md` · 关联设备：`../子PRD/设备管理.md`
> 版本：v3.0 · 状态：已实现 · 日期：2026-07-07

---

## 1. 模块功能目标

元素定位模块是测试平台的**UI元素发现与定位中心**，是连接Android设备与自动化测试的桥梁。核心职责：

1. **实时设备画面预览**：通过WebSocket推送手机截图流（2fps），叠加元素边界框，提供所见即所得的视觉反馈
2. **UI层级抓取（Dump）**：一键抓取设备当前页面的完整UI树，解析XML提取元素属性（class、text、resource-id、bounds等16个字段），自动生成8种XPath定位策略
3. **XPath定位策略引擎**：对每个元素生成最多8种XPath候选，按匹配特异性排序（count越小越精确），为自动化测试提供可靠的元素定位表达式
4. **页面与元素资产库**：保存已抓取的页面快照和元素数据，支持手动添加、重命名、标记测试点、别名管理，形成可复用的元素知识库
5. **页面跳转流管理**：记录页面间的导航关系（从哪个页面点哪个元素跳转到哪个页面），构建App的页面拓扑图
6. **跨模块元素供给**：向用例工程模块提供测试点元素（`is_test_point=True`），向AI助手提供元素搜索能力

### 用户故事

| # | 角色 | 故事 | 验收标准 |
|---|------|------|----------|
| US-01 | 自动化测试开发者 | 作为**测试开发者**，我希望**连接设备后看到实时手机画面**，截图帧叠加元素边界框，这样我在不碰手机的情况下就能确认当前页面状态，找到需要操作的目标元素 | WebSocket连接后2fps推送截图；画布正确叠加元素边界框（选中红色、悬停橙色、其他蓝色）；无设备时显示占位提示 |
| US-02 | 自动化测试开发者 | 作为**测试开发者**，我希望**一键抓取当前页面的完整UI层级**，自动识别每个可交互元素的多种定位方式，这样我不需要手写XPath就能获得可靠的元素定位表达式 | 点击Dump按钮后几秒内返回元素列表；每个元素至少有1种XPath（有resource-id/text/content-desc的元素最多8种）；XPath按匹配特异性排序 |
| US-03 | 自动化测试开发者 | 作为**测试开发者**，我希望**在手机截图上直接点击元素**，系统自动定位该元素并展示其XPath候选，这样我可以像使用UI Inspector一样直观地选取元素 | 点击截图上的元素边界框后右侧面板展示该元素详情和XPath列表；悬停时高亮当前元素边界框 |
| US-04 | 自动化测试开发者 | 作为**测试开发者**，我希望**将定位到的元素保存到页面资产库**，标记别名和测试点，这样在编写用例时可以直接搜索选取，不需要每次都重新抓取 | 元素可保存到指定页面；支持编辑别名；测试点标记后可在用例编辑器中搜索到 |
| US-05 | 测试工程师 | 作为**测试工程师**，我希望**在编写用例步骤时，从已保存的元素库中搜索选取元素**，XPath自动填入步骤，这样我不需要记住任何定位表达式 | 步骤编辑器的元素选取器可按页面/别名搜索元素；选中后XPath自动填入步骤字段 |
| US-06 | 测试工程师 | 作为**测试工程师**，我希望**将元素定位页面中选中的XPath一键发送到正在编辑的用例**，省去复制粘贴的步骤 | 在XPath列表中点击"添加到用例"，当前编辑的用例自动新增一个click步骤并填入XPath |
| US-07 | 测试工程师 | 作为**测试工程师**，我希望**管理已保存的页面和元素**——重命名页面、编辑元素别名、删除无用内容、批量清理，保持元素库的整洁 | 元素管理页支持页面CRUD、元素CRUD、测试点切换、批量删除、全部清空 |
| US-08 | 测试架构师 | 作为**测试架构师**，我希望**了解App的页面跳转关系**——从哪个页面点哪个元素会跳到哪里，这样在设计测试场景时能从全局视角规划用例覆盖 | 支持手动创建页面跳转流记录；跳转流数据在YAML导出时一同输出 |
| US-09 | AI对话用户 | 作为**AI对话用户**，我希望**AI助手能搜索和获取平台中的元素信息**，这样我通过对话就能让AI帮我找到合适的元素并生成测试步骤 | AI Agent的`search_elements`和`get_test_points`工具可以从知识库检索元素 |

### 1.1 模块边界

```
设备层 (uiautomator2 + ADB)
      │
      ▼ 截屏、dump、点击、滑动
element-locator
      │
      ▼ 提供 Element (is_test_point=True) + XPath
case-manager (用例工程)
      │
      ▼ 提供步骤XPath
test-runner (执行引擎)
```

### 1.2 两Tab布局

元素定位页面采用双Tab布局：

```
┌─────────────────────────────────────────────────────────┐
│ [📱 设备发现]  [📋 元素管理]                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Tab 1 - 设备发现:                                       │
│  ┌────────┬──────────────┬────────┐                     │
│  │ 📱     │  手机截图     │ 元素   │                     │
│  │ 设备   │  +覆盖层     │ 详情   │                     │
│  │ [Dump] │  (直播)      │ +XPath │                     │
│  └────────┴──────────────┴────────┘                     │
│                                                         │
│  Tab 2 - 元素管理:                                       │
│  ┌────────┬──────────────────────┐                      │
│  │ 页面   │  元素表格              │                      │
│  │ 列表   │  (别名/定位/编辑)      │                      │
│  └────────┴──────────────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 功能详细说明

### 2.1 F-01：实时截图流预览

**概述**：通过WebSocket连接，将设备屏幕以2fps频率推送到前端，在手机外框内实时渲染。截图之上叠加Canvas层绘制元素边界框。

**技术架构**：
```
ScreenshotConsumer (WS)
    ← ScreenshotStream (单例广播)
        ← uiautomator2 device.screenshot()
            ← Android 设备 (ADB)
```

**连接流程**：
1. 前端`ScreenshotView.vue`挂载时并发执行：①`GET /api/elements/screenshot`获取首帧JPEG（快速展示），②`new WebSocket(wsUrl('/ws/screenshot')?token=JWT)`建立长连接
2. WebSocket发送4种消息类型：
   - `screenshot` — base64 JPEG帧（quality=50, max_width=720）
   - `device_changed` — 设备切换通知（含分辨率和序列号）
   - `no_device` — 无设备选中
   - `screenshot_error` — 截图异常
3. 前端200ms节流渲染：base64解码→Uint8Array→Blob→ObjectURL→`<img>`显示
4. 断连自动重连（3秒间隔）

**叠加层渲染**：
- Canvas大小随容器自适应，元素坐标按`clientWidth/screenW`缩放
- 三种颜色：蓝色（普通元素）、橙色（悬停）、红色（选中）
- 仅绘制可点击或含text或含resource-id的元素（过滤纯容器）
- 点击/右键截图区域触发元素命中测试（最小面积包含算法）

**状态矩阵**：

| 状态 | 触发 | 视觉 |
|------|------|------|
| connecting | WebSocket握手中 | 「正在连接截图流…」+ loading动画 |
| connected | 收到第一帧 | 手机外框 + 实时截图 + 覆盖层 |
| no_device | 后端无活跃设备 | 「请先在设备管理中选择设备」 |
| error | WS断开/截图失败 | 「截图流已断开」+ 自动重连倒计时 |

### 2.2 F-02：UI层级抓取（Dump）

**概述**：一键抓取当前设备屏幕的完整UI层级结构，解析每个元素的16个属性，自动生成XPath定位策略。

**抓取流程**：
1. 用户点击「Dump UI」→ `POST /api/elements/dump`
2. 后端调用`uiautomator2`的`dump_hierarchy()`获取XML节点树
3. 三种参数组合fallback：默认 → `compressed=False` → `compressed=False, pretty=True`
4. XML截断修复：检测结尾非`>`则`rfind(">")`截断
5. 递归解析每个XML节点，提取16个属性：`index, text, resource-id, class, package, content-desc, checkable, checked, clickable, enabled, focusable, focused, scrollable, long-clickable, password, bounds`
6. 对含resource-id/text/content-desc或可点击的元素生成8种XPath候选
7. 按匹配数升序排列（count越小=越唯一=越优）
8. 截图保存到`data/screenshots/`（保留最近3张）
9. 返回全部元素+可交互子集

**8种XPath策略**：

| # | 策略 | XPath模式 | 触发条件 | 示例 |
|:--:|------|----------|------|------|
| 1 | resource-id | `//{cls}[@resource-id='{rid}']` | 有resource-id | `//Button[@resource-id='com.app:id/login']` |
| 2 | text | `//{cls}[@text='{txt}']` | 有text | `//TextView[@text='登录']` |
| 3 | content-desc | `//{cls}[@content-desc='{desc}']` | 有content-desc | `//ImageView[@content-desc='返回']` |
| 4 | 仅类名 | `//{cls}` | 始终生成 | `//Button` |
| 5 | 索引 | `(//{cls})[{pos}]` | 有index（标记fragile） | `(//Button)[3]` |
| 6 | rid+text组合 | `//{cls}[@resource-id='{rid}' and @text='{txt}']` | 同时有rid和text | `//Button[@resource-id='...' and @text='确认']` |
| 7 | 通配+rid | `//*[@resource-id='{rid}']` | 有resource-id | `//*[@resource-id='com.app:id/login']` |
| 8 | 通配+text | `//*[@text='{txt}']` | 有text | `//*[@text='登录']` |

**策略排序规则**：每个候选附带`count`（在全量元素集合中的匹配数）。count=1最优（唯一定位），按count升序排列。

**Dump结果过滤器**：

| 过滤器 | 筛选逻辑 |
|------|------|
| all | 全部可交互元素 |
| clickable | 仅`clickable=True` |
| text | `text_val`非空 |
| rid | `resource_id`非空 |
| clickable_text | 可点击且有文本 |
| clickable_no_text | 可点击但无文本（图标按钮等） |
| input | `class_name`含`edit`（输入框） |
| scrollable | `scrollable=True` |

### 2.3 F-03：三列工作区交互

**左列 — 设备选择 + Dump**：
- `DeviceSelector.vue`：在线设备下拉列表（型号/序列号/分辨率/连接类型图标）
- 「Dump UI」按钮：触发抓取
- 30秒轮询设备列表，检测当前设备离线自动标记

**中列 — XPath候选面板**（`XPathCandidatePanel.vue`）：
- 操作栏：Click / Input / Long-click 三个设备操作按钮
- 「保存到元素管理」→ 弹窗选页面 → `POST /api/elements/pages/{id}/elements`
- XPath表格：策略名 | XPath文��� | 匹配数 | 复制按钮 | +按钮(添加到用例)
- Input操作弹框：文本输入 → 输入完成后恢复原始输入法
- 复制XPath：`navigator.clipboard.writeText`/`execCommand('copy')`降级

**右列 — 元素详情面板**（`ElementDetailPanel.vue`）：
- 展示6个核心属性：class_name, text, resource_id, content_desc, bounds, clickable
- 空状态：「点击截图上的元素查看详情」

### 2.4 F-04：设备手势操作

`POST /api/elements/action`

| 操作 | 参数 | 用途 |
|------|------|------|
| click | x, y | 点击坐标 |
| longclick | x, y | 长按（1秒） |
| swipe | x, y, direction, distance | 上下左右滑动 |
| drag | x, y, x2, y2 | 拖拽 |
| input | x, y, text, clear_first | 点击坐标后输入文字 |

所有坐标基于设备实际分辨率（非截图显示尺寸）。

### 2.5 F-05：页面元素资产库

**数据模型关系**：
```
el_pages (页面) ──< el_elements (元素)
     │
     └──< el_page_flows (跳转流) >── el_pages
```

**页面API**：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/elements/pages` | 列出全部页面，附带`flow_out`/`flow_in`跳转计数 |
| POST | `/elements/pages/create` | 手动创建（label必填且唯一，package/activity选填，device自动取当前） |
| PUT | `/elements/pages/{id}` | 重命名（校验唯一性） |
| DELETE | `/elements/pages/{id}` | 删除页面（CASCADE元素和跳转流） |
| POST | `/elements/pages/clear` | 清空全部 |

**元素API**：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/elements/pages/{id}/items?filter=` | 获取元素列表（filter: all/clickable/text/testpoint） |
| POST | `/elements/pages/{id}/elements` | 添加/更新元素（upsert：同page+rid+bounds则更新元数据） |
| PUT | `/elements/items/{id}` | 更新元素（alias/tags/notes/is_test_point） |

### 2.6 F-06：元素管理页

**路由**：`/element-mgr`，独立视图。

**页面管理（左侧面板 300px）**：
- 新���对话框：label（必填且唯一）、package、activity
- 行内重命名：点击「重命名」→ 输入 + 回车保存
- 多选批量删除
- 全部清空（二次确认）
- 行背景三色交替

**元素表格（右侧）**：
- 7列：名称(可编辑)、XPath(首候选)、Class、Text、Resource ID、可点击(标签)、测试点(Switch)
- 4个筛选Tab：全部 / 可点击 / 已命名 / 测试点
- 行内别名编辑
- 手动添加元素对话框
- 元素总数展示

### 2.7 F-07：页面跳转流

**数据模型**：`from_page → trigger_element → to_page`

**API**：GET/POST `/elements/flows`，DELETE `/elements/flows/{id}`

**用途**：记录App页面导航关系，在YAML导出时包含跳转数据辅助测试场景设计。

### 2.8 F-08：跨模块集成

**→ case-manager**：
- EventBus `add-step-to-case`：XPath列表一键发送到正在编辑的用例
- `is_test_point`元素供YAML导出（`case_manager/views.py`查询`Element.objects.filter(is_test_point=True)`）
- 步骤编辑器元素选取器：加载全部页面+元素，按页面分组搜索

**→ AI助手（AgentScope）**：
- `get_test_points(page_ids?)`：获取测试点元素
- `search_elements(query)`：关键词搜索元素
- `fetch_page_elements(page_id)`：获取页面全部元素

**→ dashboard**：首页展示元素总数/页面数/元素分布

---

## 3. 数据模型

### 3.1 页面表（el_pages）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BigAutoField PK | — | 自增 |
| device | FK→dp_devices | SET_NULL | Dump设备 |
| label | VARCHAR(500) | UNIQUE | 页面名称 |
| package | VARCHAR(500) | — | 包名 |
| activity | VARCHAR(500) | — | Activity |
| screenshot_path | VARCHAR(1000) | — | 截图路径 |
| element_count | INT | 0 | 元素总数 |
| created_at | DateTime | auto | 创建时间 |

### 3.2 元素表（el_elements）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BigAutoField PK | — | 自增 |
| page | FK→el_pages | CASCADE | 所属页面 |
| class_name | VARCHAR(500) | — | 控件类名 |
| text_val | VARCHAR(2000) | — | 文本 |
| content_desc | VARCHAR(2000) | — | 无障碍描述 |
| resource_id | VARCHAR(500) | — | Android资源ID |
| bounds | VARCHAR(200) | — | [x1,y1][x2,y2] |
| xpath_candidates | TEXT | '[]' | 8种XPath JSON |
| clickable | BOOL | — | 可点击 |
| enabled | BOOL | — | 可用 |
| alias | VARCHAR(500) | — | 中文别名 |
| tags | VARCHAR(500) | — | 标签 |
| is_test_point | BOOL | False | 测试点标记 |
| notes | TEXT | — | 备注 |
| created_at | DateTime | auto | 创建时间 |

**唯一约束**: `UNIQUE(page_id, resource_id, bounds)`

### 3.3 页面跳转流表（el_page_flows）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BigAutoField PK | — | 自增 |
| from_page | FK→el_pages | CASCADE | 起始页 |
| to_page | FK→el_pages | CASCADE | 目标页 |
| trigger_element | FK→el_elements | SET_NULL | 触发元素 |
| trigger_action | VARCHAR(50) | 'click' | 触发动作 |
| created_at | DateTime | auto | 创建时间 |

---

## 4. 关键约束速查

| 约束 | 实施位置 | 说明 |
|------|:--:|------|
| 页面label唯一 | `models.py` UNIQUE + `views.py` | 创建/重命名校验 |
| 元素(page, rid, bounds)唯一 | `models.py` UniqueConstraint | upsert逻辑 |
| 截图保留最近3张 | `views.py` | dump时删除旧图 |
| WS JWT鉴权 | `consumers.py` | query string提取token |
| 设备操作当前设备 | `views.py` + pool | `device.current_serial` |
| MySQL索引上限 | 注释说明 | 原(page,rid,text,bounds)超3072字节，移除text |

---

## 5. 异常场景处理

| 场景 | 处理 |
|------|------|
| WS断连 | 3秒自动重连 |
| 截图失败 | WS发送screenshot_error，前端显示错误态 |
| 设备离线 | WS发送no_device，前端占位提示 |
| Dump XML截断 | rfind(">")修复，失败抛RuntimeError |
| 重复创建页面 | 返回label已存在错误 |
| 重复添加元素 | upsert更新元数据 |
| 清空操作 | 二次确认，CASCADE删除 |
| 首帧慢 | REST截图兜底（并行请求） |

---

## 6. 组件树

```
index.vue (/elements + /element-mgr)
├── Tab 1: 设备发现
│   ├── DeviceSelector.vue
│   ├── Dump UI按钮
│   ├── 过滤器 + 搜索
│   └── 三列: ScreenshotView | XPathCandidatePanel | ElementDetailPanel
└── Tab 2: 元素管理
    └── ElementManager.vue
        ├── 页面列表(左)
        └── 元素表格(右)
```

---

## 7. 后端文件

```
apps/element_locator/
├── models.py        Page/Element/PageFlow
├── views.py         13 HTTP端点
├── api.py           跨模块__all__白名单
├── service.py       8种XPath + YAML dump
├── urls.py          路由
├── admin.py         Admin注册
├── consumers.py     WS JWT鉴权
├── stream.py        ScreenshotStream 2fps广播
├── apps.py          verbose_name='元素定位'
├── permissions.py   占位(v2)
└── serializers.py   占位(v2)
```

---

## 8. 关联模块

| 模块 | 交互方式 |
|------|------|
| device-pool | u2截屏/dump/手势 |
| case-manager | EventBus + is_test_point导出 + 元素选取器 |
| AI助手 | element_tools(3个Tool) |
| dashboard | 元素/页面统计 |

---

## 9. 规划

**已实现** ✅：截图流 / Dump / 8种XPath / 元素保存 / 页面CRUD / 测试点 / EventBus / 设备手势

**规划中** 📋：Activity自动dump / OCR文字识别 / 相似元素批量 / XPath自动校验 / 元素变更历史 / 可拖拽三列

---

## 变更记录

| 版本 | 日期 | 类型 | 说明 |
|------|------|------|------|
| v3.0 | 2026-07-07 | 重写 | 基于代码实现完整逆向，覆盖13端点/8 XPath策略/WS截图流/6组件/3数据表/跨模块集成 |
