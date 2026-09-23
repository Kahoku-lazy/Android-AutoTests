# 分组规则与字段字典

本文件是 `device-page-analysis` skill 的规则真相源：类名集合、细类定义、元素字段含义、出图与报告约定、局限。

## 一、L1 分组（类名集合，按顺序匹配，命中即定）

| 分组 | key | 类名集合（取类名末段） |
|------|-----|------------------------|
| 布局容器 | `layout_container` | ViewGroup, FrameLayout, LinearLayout, RelativeLayout, ConstraintLayout, CoordinatorLayout, GridLayout, TableLayout, TableRow, RadioGroup, CardView, AppBarLayout, NavigationView, DrawerLayout, SwipeRefreshLayout, Toolbar, MotionLayout, TabLayout, ViewAnimator, ViewSwitcher |
| 滚动·集合容器 | `scroll_collection` | RecyclerView, ListView, GridView, ScrollView, HorizontalScrollView, NestedScrollView, ViewPager, ViewPager2, ExpandableListView, AdapterView, AbsListView, AbsSpinner, Spinner |
| 内容控件 | `content_widget` | 文本类（见下表）+ ImageView, ImageButton + 裸 View + Chip, SearchView |
| 其它 | `unclassified` | 不在以上任何集合内（**不猜**，单列一类） |

判据来源：Android 框架类层级（`View` vs `ViewGroup`）+ 职责。`RecyclerView`/`ScrollView`/`GridView`/`ViewPager` 本身也是 ViewGroup，但带滚动与复用职责，故单独成组。

## 二、L2 分组（只作用于内容控件）

| L2 | 细类 | 判据 |
|----|------|------|
| 文本 | `text` | 文本类控件且 `text` 非空且非私用区字符 |
| 文本 | `text_empty` | 文本类控件但 `text` 为空（占位/间距） |
| 图标 | `icon_font` | 文本类控件但 `text` 是私用区码点 U+E000–F8FF / U+F0000–FFFFD（图标字体伪装的图标） |
| 图标 | `icon_semantic` | ImageView / ImageButton 且有 `content-desc` |
| 图标 | `icon_bare` | ImageView / ImageButton 且无 `content-desc`（纯图形，无语义） |
| 其它 | `hotzone` | 裸 View 且 `clickable=true`（不可见点击热区） |
| 其它 | `shape` | 裸 View 且不可点击（分隔线 / 色块 / 占位） |

文本类控件集合：TextView, Button, EditText, AutoCompleteTextView, CheckBox, RadioButton, Switch, ToggleButton, CheckedTextView, Chip, SearchView。

**为什么必须看三个字段而不是一个**：

| 只用… | 会错在哪 |
|-------|----------|
| 只用 `class_name` | 文本类里可能有 `text` 为空的占位件；文本类也可能放图标字体 |
| 只用 `text` | 把「图标」与「裸 View」混为一类，丢失区分 |
| 只用 `content_desc` | 绝大多数图标没有描述，会漏掉 |

## 三、元素字段字典

| 字段 | 含义 | 来源 |
|------|------|------|
| `seq` | 全页 (y, x, depth) 升序序号（分组内沿用同一序号） | 分析生成 |
| `coords.{x,y,w,h}` | 左上角坐标与宽高（像素，与截图同坐标空间） | dump `bounds` 拆解 |
| `coords.{cx,cy}` | 中心点 = x+w/2, y+h/2 | 派生 |
| `coords.bounds` | 原始字符串 `[左,上][右,下]` | dump |
| `class_name` / `class_simple` | 控件类名（全名 / 末段） | dump `class` |
| `resource_id` | `包名:id/名字`。**有值 ≠ 唯一**，唯一性看候选的 `count` | dump `resource-id` |
| `text` | 控件当前显示文字 | dump `text` |
| `content_desc` | 无障碍描述（图标类常用） | dump `content-desc` |
| `package` | 归属 App 包名（可识别系统状态栏/桌面叠加元素） | dump `package` |
| `depth` | 层级深度（合成根为 0，故 1 = 应用窗口最外层） | 遍历计算 |
| `index_attr` | 在父节点里的第几个孩子（字符串） | dump `index` |
| `flags.clickable` | 该节点自身是否响应点击。**false 不代表点不到**（外层容器可能承接） | dump |
| `flags.long_clickable` | 是否支持长按 | dump `long-clickable` |
| `flags.scrollable` | 是否可滚动 | dump |
| `flags.checkable` / `flags.checked` | 是否可勾选 / 当前是否已勾选 | dump |
| `flags.enabled` | 是否启用（false = 置灰，仍可定位但不该点） | dump |
| `flags.focusable` | 是否可获得焦点 | dump |
| `kept_in_snapshot` | 平台是否把它写进快照（false = 被展示裁剪丢弃） | 平台 `trim_hierarchy` |
| `content_kind` | 七个细类之一 | 分析生成 |
| `primary.{xpath,type,count,stable}` | 主定位与唯一性判定 | 分析生成 |
| `xpath_candidates[]` | 平台生成的候选定位器（`{type,xpath,count,note?}`，按 count 升序） | 平台 `gen_xpath_candidates` |

候选类型：`resource-id` / `content-desc` / `combined` / `text` / `class` / `resource-id (any)` / `text (any)` / `index`（位置型，标 `note: fragile`）。

## 四、主定位与唯一性口径（本 skill 的分析口径）

1. 先筛 **`count == 1` 且类型非 `index`** 的候选（即「基于属性/文本且本屏唯一」）；
2. 再按类型质量排序取第一：`resource-id` > `content-desc` > `combined` > `resource-id (any)` > `text` > `text (any)` > `class`;
3. 没有这样的候选时 `stable=false`，给出匹配数最小者作为最接近的定位。

**为什么不能按 count 最小者胜**：位置型候选 `(//cls)[n]` 的 count 被硬编码为 1，会排到属性型定位前面，形成「假唯一」（页面多一个同类控件就指错）。

**这是分析口径，平台当前没有这两个字段。**

## 五、圈选图约定

- 一个非空叶子一张图，**不合成**（合成后难以逐个分析）。
- 颜色：布局=青 `#19c8b9`、滚动=橙 `#e59266`、文本=紫 `#b77dee`、图标=蓝 `#889df0`、其它=粉 `#f8a6b2`。
- **实线** = `kept_in_snapshot=true`；**虚线** = 被裁（`pure_container` / `bounds_dedup`）。
- 角标 = `index_attr`。
- 图脚两行：层级路径 + 数量 + 保留数；细类计数 + 图例。图例画在截图下方（不遮挡元素，坐标 1:1）。
- 截图与 dump 必须**同一次连接内**取得（先截图后 dump）。

## 六、报告结构

总览统计卡 → 旭日图（L1→L2）→ 分组柱状图 + 环形饼图 → 五组数据表 → 逐组卡片（压缩预览图 + 定位说明 + 关键数字 + 保留/被裁占比 + 类名与细类分布 + 图上看什么/注意）→ L2 判定依据表 + 细类条形图 → 口径与局限。

视觉遵循 `html-report` skill 的 animal-island-ui 规范（Nunito + Noto Sans SC、暖木色系、圆角 ≥12px、禁止纯黑与冷蓝聚焦环）。图片以压缩预览内联（宽 380 JPEG，约为原图 4%~6%），报告自包含。

## 七、局限（写进报告，别省）

1. **单页单次采样**：计数随页面状态变化（滚动位置、弹窗、动画），换页必须重跑。
2. **可见性无法完全判定**：`text` 非空不等于肉眼可见 —— 可能被压成极窄高度，或被上层容器遮挡；dump 的 `visible-to-user` 属性对这两种情况都不敏感（实测均为 true）。
3. **平台裁剪只影响展示集合**：`kept_in_snapshot=false` 不代表元素不存在，只是没被写进快照的展示列表。
4. **主定位是分析口径**，不是平台现状。
5. **ECharts 走 CDN**：无网络时图表区域显示提示，数据表常驻（信息不丢）。

## 八、常见问题

| 现象 | 处理 |
|------|------|
| 报告标题乱码 | 中文标题改用 `--title-file`（UTF-8 文件），别用 `--title` |
| 采集到别的页面 | 页面状态可能被切走；重新采，并核对 `package`/`activity` 与用户描述是否一致 |
| 目录名撞了别的页面 | 同包名 + 同 Activity + 同元素数时脚本会自动加 `_v2`；也可用 `--label` 加页面前缀 |
| 框与画面错位 | 说明截图与 dump 不同源；重新跑 `capture_page.py` |
| 找不到项目根 | 脚本按 `manage.py` + `config/settings.py` 向上查找，需在项目树内运行 |
