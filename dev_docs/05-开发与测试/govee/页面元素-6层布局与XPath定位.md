# Govee Home「设备」页 · 6 层布局 + XPath 定位

> 设备：`RF8N21MSW7A` · 应用：`com.govee.home` / `.main.MainTabActivity` · 屏幕：1440×3040 · 采集时间：2026-08-25 15:20:41

> 列说明：**名称**=功能名；**元素**=resource-id；**指标**=可点击/可滚动/可勾选（具备几项就占几个标签）；**xpath_id**=按 id 定位；**xpath_text**=按 text 定位；**bounds**=坐标

## 1. 系统状态栏

| 名称 | 元素 | 指标 | xpath_id | xpath_text | bounds |
| --- | --- | --- | --- | --- | --- |
| 时钟 | clock | - | `//android.widget.TextView[@resource-id='com.android.systemui:id/clock']` | `//android.widget.TextView[@text='15:20']` | [95,33][228,150] |
| 电池百分比 | battery_percentage_view | - | `//android.widget.TextView[@resource-id='com.android.systemui:id/battery_percentage_view']` | `//android.widget.TextView[@text='100%']` | [1030,33][1159,150] |

## 2. App 头部信息

| 名称 | 元素 | 指标 | xpath_id | xpath_text | bounds |
| --- | --- | --- | --- | --- | --- |
| 设备 | tvTabLayout | - | `//android.widget.TextView[@resource-id='com.govee.home:id/tvTabLayout']` | `//android.widget.TextView[@text='设备']` | [77,110][221,321] |
| 网关入口 | ivGateway | 可点击 | `//android.widget.ImageView[@resource-id='com.govee.home:id/ivGateway']` | `-` | [1070,162][1178,270] |
| 添加设备入口 | ivDevAdd | 可点击 | `//android.widget.ImageView[@resource-id='com.govee.home:id/ivDevAdd']` | `-` | [1255,162][1363,270] |

## 3. 层级一：房间标签栏

- 列表容器 `rvRoom`：`scrollable=true` → 指标 `可滚动`，bounds [0,352][1079,509]

> **左右滑动规则**：房间标签栏支持左右滑动。
>
> 判定依据：① XML 中 `rvRoom` 节点 `scrollable="true"`，但 XML **不含方向**（无 scrollX/scrollY 字段）；② 方向靠「滑动 + 重新 dump 对比」实测得出——手指左→右滑，左侧露出新标签（测试设备、图表…）；手指右→左滑，右侧露出新标签（庭院、休闲区、办公室…），两侧都有 → 左右均可滑。
>
> 完整标签序列：全部 → 自动化 → 测试设备 → 图表 → 自动化SKU → 卧室 → 餐厅 → 书房 → 游戏房 → 庭院 → 休闲区 → 办公室

| 名称 | 元素 | 指标 | xpath_id | xpath_text | bounds |
| --- | --- | --- | --- | --- | --- |
| 标签列表容器 | rvRoom | 可滚动 | `//androidx.recyclerview.widget.RecyclerView[@resource-id='com.govee.home:id/rvRoom']` | `-` | [0,352][1079,509] |
| 标签「全部」 | tvName | 可点击 | `//android.widget.TextView[@resource-id='com.govee.home:id/tvName']` | `//android.widget.TextView[@text='全部']` | [38,377][234,485] |
| 标签「自动化」 | tvName | 可点击 | `//android.widget.TextView[@resource-id='com.govee.home:id/tvName']` | `//android.widget.TextView[@text='自动化']` | [265,377][513,485] |
| 标签「测试设备」 | tvName | 可点击 | `//android.widget.TextView[@resource-id='com.govee.home:id/tvName']` | `//android.widget.TextView[@text='测试设备']` | [544,377][844,485] |
| 标签「图表」 | tvName | 可点击 | `//android.widget.TextView[@resource-id='com.govee.home:id/tvName']` | `//android.widget.TextView[@text='图表']` | [875,377][1071,485] |
| 搜索 | ivDeviceSearch | 可点击 | `//android.widget.ImageView[@resource-id='com.govee.home:id/ivDeviceSearch']` | `-` | [1094,369][1217,492] |
| 房间编辑 | ivRoomEdit | 可点击 | `//android.widget.ImageView[@resource-id='com.govee.home:id/ivRoomEdit']` | `-` | [1267,377][1421,485] |

## 4. 层级二：设备列表

卡片总数：**7**

### 卡片 1：H705F

| 名称 | 元素 | 指标 | xpath_id | xpath_text | bounds |
| --- | --- | --- | --- | --- | --- |
| 设备名 | tvName | - | `//android.widget.TextView[@resource-id='com.govee.home:id/tvName']` | `//android.widget.TextView[@text='H705F']` | [92,587][399,666] |
| WiFi连接 | ivWifi | - | `//*[@text='H705F']/..//*[@resource-id='com.govee.home:id/ivWifi']` | `-` | [602,560][671,629] |
| 设备图标 | ivIcon | - | `//*[@text='H705F']/..//*[@resource-id='com.govee.home:id/ivIcon']` | `-` | [92,890][257,1055] |
| 开关 | ivSwitch | 可点击 | `//*[@text='H705F']/..//*[@resource-id='com.govee.home:id/ivSwitch']` | `-` | [498,901][648,1051] |

### 卡片 2：H6020

| 名称 | 元素 | 指标 | xpath_id | xpath_text | bounds |
| --- | --- | --- | --- | --- | --- |
| 设备名 | tvName | - | `//android.widget.TextView[@resource-id='com.govee.home:id/tvName']` | `//android.widget.TextView[@text='H6020']` | [789,587][1096,666] |
| 状态标注 | tvShow | - | `//*[@text='H6020']/..//*[@resource-id='com.govee.home:id/tvShow']` | `//android.widget.TextView[@text='设备离线']` | [789,678][1345,736] |
| 设备图标 | ivIcon | - | `//*[@text='H6020']/..//*[@resource-id='com.govee.home:id/ivIcon']` | `-` | [789,890][954,1055] |
| 开关 | ivSwitch | 可点击 | `//*[@text='H6020']/..//*[@resource-id='com.govee.home:id/ivSwitch']` | `-` | [1195,901][1345,1051] |

### 卡片 3：H61C3

| 名称 | 元素 | 指标 | xpath_id | xpath_text | bounds |
| --- | --- | --- | --- | --- | --- |
| 设备名 | tvName | - | `//android.widget.TextView[@resource-id='com.govee.home:id/tvName']` | `//android.widget.TextView[@text='H61C3']` | [92,1190][399,1269] |
| 蓝牙连接 | ivBT | - | `//*[@text='H61C3']/..//*[@resource-id='com.govee.home:id/ivBT']` | `-` | [523,1163][592,1232] |
| WiFi连接 | ivWifi | - | `//*[@text='H61C3']/..//*[@resource-id='com.govee.home:id/ivWifi']` | `-` | [602,1163][671,1232] |
| 设备图标 | ivIcon | - | `//*[@text='H61C3']/..//*[@resource-id='com.govee.home:id/ivIcon']` | `-` | [92,1493][257,1658] |
| 开关 | ivSwitch | 可点击 | `//*[@text='H61C3']/..//*[@resource-id='com.govee.home:id/ivSwitch']` | `-` | [498,1504][648,1654] |

### 卡片 4：H703B

| 名称 | 元素 | 指标 | xpath_id | xpath_text | bounds |
| --- | --- | --- | --- | --- | --- |
| 设备名 | tvName | - | `//android.widget.TextView[@resource-id='com.govee.home:id/tvName']` | `//android.widget.TextView[@text='H703B']` | [789,1190][1096,1269] |
| 蓝牙连接 | ivBT | - | `//*[@text='H703B']/..//*[@resource-id='com.govee.home:id/ivBT']` | `-` | [1220,1163][1289,1232] |
| WiFi连接 | ivWifi | - | `//*[@text='H703B']/..//*[@resource-id='com.govee.home:id/ivWifi']` | `-` | [1299,1163][1368,1232] |
| 设备图标 | ivIcon | - | `//*[@text='H703B']/..//*[@resource-id='com.govee.home:id/ivIcon']` | `-` | [789,1493][954,1658] |
| 开关 | ivSwitch | 可点击 | `//*[@text='H703B']/..//*[@resource-id='com.govee.home:id/ivSwitch']` | `-` | [1195,1504][1345,1654] |

### 卡片 5：H609D

| 名称 | 元素 | 指标 | xpath_id | xpath_text | bounds |
| --- | --- | --- | --- | --- | --- |
| 设备名 | tvName | - | `//android.widget.TextView[@resource-id='com.govee.home:id/tvName']` | `//android.widget.TextView[@text='H609D']` | [92,1793][399,1872] |
| 蓝牙连接 | ivBT | - | `//*[@text='H609D']/..//*[@resource-id='com.govee.home:id/ivBT']` | `-` | [523,1766][592,1835] |
| WiFi连接 | ivWifi | - | `//*[@text='H609D']/..//*[@resource-id='com.govee.home:id/ivWifi']` | `-` | [602,1766][671,1835] |
| 设备图标 | ivIcon | - | `//*[@text='H609D']/..//*[@resource-id='com.govee.home:id/ivIcon']` | `-` | [92,2096][257,2261] |
| 开关 | ivSwitch | 可点击 | `//*[@text='H609D']/..//*[@resource-id='com.govee.home:id/ivSwitch']` | `-` | [498,2107][648,2257] |

### 卡片 6：H6056_291D

| 名称 | 元素 | 指标 | xpath_id | xpath_text | bounds |
| --- | --- | --- | --- | --- | --- |
| 设备名 | tvName | - | `//android.widget.TextView[@resource-id='com.govee.home:id/tvName']` | `//android.widget.TextView[@text='H6056_291D']` | [789,1793][1096,1941] |
| 状态标注 | tvShow | - | `//*[@text='H6056_291D']/..//*[@resource-id='com.govee.home:id/tvShow']` | `//android.widget.TextView[@text='设备离线']` | [789,1953][1345,2011] |
| 设备图标 | ivIcon | - | `//*[@text='H6056_291D']/..//*[@resource-id='com.govee.home:id/ivIcon']` | `-` | [789,2096][954,2261] |
| 开关 | ivSwitch | 可点击 | `//*[@text='H6056_291D']/..//*[@resource-id='com.govee.home:id/ivSwitch']` | `-` | [1195,2107][1345,2257] |

### 卡片 7：H6099-50001

| 名称 | 元素 | 指标 | xpath_id | xpath_text | bounds |
| --- | --- | --- | --- | --- | --- |
| 设备名 | tvName | - | `//android.widget.TextView[@resource-id='com.govee.home:id/tvName']` | `//android.widget.TextView[@text='H6099-50001']` | [92,2396][399,2544] |
| 状态标注 | tvShow | - | `//*[@text='H6099-50001']/..//*[@resource-id='com.govee.home:id/tvShow']` | `//android.widget.TextView[@text='设备离线']` | [92,2556][648,2614] |
| 设备图标 | ivIcon | - | `//*[@text='H6099-50001']/..//*[@resource-id='com.govee.home:id/ivIcon']` | `-` | [92,2699][257,2864] |
| 开关 | ivSwitch | 可点击 | `//*[@text='H6099-50001']/..//*[@resource-id='com.govee.home:id/ivSwitch']` | `-` | [498,2710][648,2860] |

## 5. 层级三：底部导航栏

| 名称 | 元素 | 指标 | xpath_id | xpath_text | bounds |
| --- | --- | --- | --- | --- | --- |
| 设备Tab | ivTabDevice | 可点击 | `//android.widget.ImageView[@resource-id='com.govee.home:id/ivTabDevice']` | `-` | [128,2657][282,2811] |
| 广场Tab | ivTabSquare | 可点击 | `//android.widget.ImageView[@resource-id='com.govee.home:id/ivTabSquare']` | `-` | [386,2657][540,2811] |
| 社区Tab | ivTabCommunity | 可点击 | `//android.widget.ImageView[@resource-id='com.govee.home:id/ivTabCommunity']` | `-` | [643,2657][797,2811] |
| 商城Tab | ivTabShopping | 可点击 | `//android.widget.ImageView[@resource-id='com.govee.home:id/ivTabShopping']` | `-` | [901,2657][1055,2811] |
| 我的Tab | ivTabProfile | 可点击 | `//android.widget.ImageView[@resource-id='com.govee.home:id/ivTabProfile']` | `-` | [1158,2657][1312,2811] |

## 6. 层级四：系统导航栏区域

| 名称 | 元素 | 指标 | xpath_id | xpath_text | bounds |
| --- | --- | --- | --- | --- | --- |
| 最近使用 | recent_apps | 可点击 | `//android.widget.ImageView[@resource-id='com.android.systemui:id/recent_apps']` | `//*[@content-desc='最近使用']` | [158,2872][477,3040] |
| 返回 | back | 可点击 | `//android.widget.ImageView[@resource-id='com.android.systemui:id/back']` | `//*[@content-desc='返回']` | [963,2872][1282,3040] |
| 主屏幕 | home | 可点击 | `//android.widget.ImageView[@resource-id='com.android.systemui:id/home']` | `//*[@content-desc='主屏幕']` | [560,2872][879,3040] |