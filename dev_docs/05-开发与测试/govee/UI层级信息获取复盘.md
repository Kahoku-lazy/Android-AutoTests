# UI 层级信息获取复盘

> 对象：Govee Home「设备」页（`com.govee.home` / `MainTabActivity`）· 设备 `RF8N21MSW7A` · 屏幕 1440×3040

---

## 一、用什么工具 / 脚本实现

### 1. 数据采集（3 种方式）

| 方式 | 命令/库 | 产出 | 说明 |
| --- | --- | --- | --- |
| uiautomator2（主力） | `u2.connect(serial).dump_hierarchy()` | 145 节点、22 属性、含系统 UI | 最完整，走设备 ATX agent |
| adb（备用） | `adb shell uiautomator dump` + `adb pull` | 96 节点、17 属性、仅 App 窗口 | uiautomator2 被沙箱拦截时兜底 |
| 项目自带解析 | `tools/dump_ui.py` 的 `parse_node()` | 嵌套 dict（含 children） | 最初指定要测的函数 |

**两种 dump 的关键差异**：`adb uiautomator dump` 缺 `hint` / `visible-to-user` / `display-id` / `drawing-order` 四个属性，且不含系统状态栏/导航栏。因此要拿「全量 22 属性 + 系统 UI」必须用 uiautomator2。

### 2. 交互操作（点击 / 滑动）

- `d.click(x, y)` — 把房间筛选从「自动化」切回「全部」，拿到完整 7 张设备卡
- `d.swipe(...)` — 左右滑动做滚动方向实测

### 3. 解析与生成

- `xml.etree.ElementTree`（标准库）解析 XML、递归遍历建树、提取属性
- 一批 `_tmp_*.py` 临时脚本，按任务迭代：
  - 分类统计 → 文本枚举 → 三点核对（网关/卡片/搜索） → 全树 → 滚动实测 → 卡片枚举 → 全属性 → 生成 md
- 最终落盘两份 md（见文末「产出」）

### 4. 环境 / 权限处理

- `adb devices` 先确认设备在线
- uiautomator2 依赖的 `requests` 库在 Roaming site-packages，被沙箱 `workspace-write` 拦读 → 用 `danger-full-access` 一次性提权重试

---

## 二、信息怎么分类

### 分类是「多级分层」，四层递进

**第一层：按页面区域分（6 层）**

靠 `resource-id` 后缀 + `package` 归属判定：

| 层 | 判定依据 |
| --- | --- |
| 系统状态栏/导航栏 | `package` 含 `systemui` |
| App 头部 | rid ∈ {tvTabLayout, ivGateway, ivDevAdd, topBg} |
| 房间标签栏 | rid ∈ {rvRoom, ivDeviceSearch, ivRoomEdit} + 标签 tvName |
| 设备列表 | rid ∈ {rvList, container, tvName, tvShow, ivSwitch, ivIcon, ivWifi, ivBT} |
| 底部导航 | rid 以 `ivTab` 开头 |
| 系统导航 | rid ∈ {recent_apps, back, home} |

**第二层：按元素角色分（功能名）**

把 resource-id 映射成人类可读的功能名：

- `ivGateway → 网关入口`、`ivDevAdd → 添加设备入口`、`ivSwitch → 开关`、`ivWifi → WiFi连接`
- 设备卡片固定拆 5 角色：**名称(tvName) / 状态(tvShow) / 图标(ivIcon) / 开关(ivSwitch) / 连接图标(ivWifi+ivBT)**

**第三层：按属性维度分（22 项）**

每个节点的 dump 属性归 6 组：

- 定位类：class / resource-id / package / index / bounds
- 文本类：text / content-desc / hint
- 交互类：clickable / long-clickable / scrollable / focusable / checkable
- 状态类：checked / focused / selected / enabled / password
- 可见性类：visible-to-user / display-id / drawing-order
- 结构类：depth（深度）/ children（子节点数）

**第四层：按业务状态分（规则推导）**

设备状态不靠单一字段，而是组合判断：

```
有 tvShow(文本="设备离线")        → 离线
无 tvShow 且 有 ivWifi            → 在线
有 ivBT                          → 蓝牙连接
```

### 一个特殊处理：滚动方向

XML 只给 `scrollable="true"`，**没有方向字段**（无 scrollX/scrollY）。滚动方向没法静态读，改用**动态实测法**：

1. dump 记录当前可见标签（基线）
2. 手指左→右滑 → 重新 dump → 左侧冒出「测试设备 / 图表」→ 左侧有内容
3. 手指右→左滑 → 重新 dump → 右侧冒出「庭院 / 休闲区 / 办公室」→ 右侧有内容
4. 再滑一次无新标签 → 已到该方向尽头

据此拼出完整 12 标签序列：

```
全部 → 自动化 → 测试设备 → 图表 → 自动化SKU → 卧室 → 餐厅 → 书房 → 游戏房 → 庭院 → 休闲区 → 办公室
```

---

## 三、关键结论

- **XML 能拿到**：结构 + 定位（类名 / 资源ID / 坐标 / 层级 / 交互标志）的完整信息。
- **XML 拿不到**：视觉样式、图片内容、开关实时状态、滚动位置、视口外内容（RecyclerView 只物化可见项）。
- **补全方向**：dump XML + 截图 + OCR/图像识别 三合一。

---

## 四、产出文件

| 文件 | 内容 |
| --- | --- |
| `页面元素-可获取信息清单.md` | 全量逐层明细（107 节点 × 25 项维度） |
| `页面元素-6层布局与XPath定位.md` | 6 层结构 + 指标 + XPath 定位符 |
