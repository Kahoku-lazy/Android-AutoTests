# 设备检查器 业务功能需求

> 版本：v1.1 · 日期：2026-09-22 · 状态：刷新（对照 HEAD 与 `openspec/specs` 实测；变更 `align-inspector-prd-with-layers`）
> 范围：`apps/device_inspector`（后端 8 端点 + 快照表）· `frontend/src/modules/device-inspector/`（`/inspector` 页面）· `algorithms/element_layers.py`（两级分组与主定位）· `algorithms/xpath.py`（XPath 纯规则）
> 关联：[平台总体架构](ARCH-平台总体架构.md) · [需求总纲](PRD-需求总纲.md) · [API-设备检查器](../DEV_TEST/接口文档/API-设备检查器.md)
> 规格真相源：`openspec/specs/` 下的 device-inspector-page · device-inspector-layers · device-inspector-snapshots · element-layering · api-path-convention · frontend-l4-data-surface · frontend-l5-overlay

---

## 产品功能

> 模块在数据链路上的位置：**设备管理 →（同步设备信息）→ 设备检查器 →（采集 UI 元素）→ 元素定位**。检查器负责「把设备上的一屏抓成可回看、可筛减、可落盘的元素资产」，本身不写元素定位的表，落盘一律经 `apps/element_locator/api_snapshot.py`。

### 页面骨架与设备选择

#### UI交互

1. **模版** —— 一张检查器工作台（路由 `/inspector`，标题「设备检查器」），从上到下：
   1. 页头 —— 标题「设备检查器」，副标题「选择设备一键获取页面元素快照，回看、筛减并保存到元素管理」。
   2. 工具条 —— 设备选择框 ·「获取」·「历史快照」·「已保存页面」（禁用）·「保存到元素定位」（禁用）；右侧「N 元素」（当前分组元素数）；历史快照缺全量索引时另有一条如实提示；失败时再出现一条错误条。
   3. 工作区 —— 两栏：左＝「元素分组 + 元素档案表」面板（分组列表与表格在面板内并排）→ 右＝手机屏幕。
   4. 页脚 —— 「就绪」· 元素数 · `serial · package`。
   5. 三个覆盖层 ——「历史快照」抽屉、「保存到元素定位」弹窗、「已保存页面」弹窗（后两者当前处在冻结入口之后）。
   `index.vue` · `components/CaptureForm.vue`
2. **业务逻辑**
   1. **骨架常驻** —— 尚无快照时，工具条、元素分组列表、元素表格列与手机屏幕列都照常渲染；每个数据区以空态表达「无数据」，**不整块隐藏区域**。
   2. **设备列表** —— 进页面即拉一次设备；只把「在线」与「使用中」两类放进下拉，其中**被执行引擎占用**（`occupied_by` 以 `runner-` / `ai_agent` / `task-` / `run-` 开头）的设备排除。
   3. **下拉项文案** —— `型号或品牌 (serial) · 在线|使用中`。
   4. **未选设备** —— 「获取」与「保存到元素定位」呈灰底；点灰键**不发请求**，只提示「按键不可用，请先选择设备」（原生 disabled 不派发 click，故由 click 守卫承担）。
   5. **两个入口冻结** —— 「已保存页面」与「保存到元素定位」保留可见但处于禁用态（原因分别是「存量已保存页面数据已作废，功能冻结」与「元素下标口径已随全量元素展示变更，保存链路待后续变更对齐，暂不可用」）；点按只提示原因、不发请求、不改动当前分组、表格与画面。
   6. **响应式** —— 窗口宽度 ≤1200px 时工作区折成上下两行（分组 + 表格在上、手机屏幕在下）。
   `store.ts`（`availableDevices` · `captureSerial` · `notifyKeyUnavailable`）· `index.vue`（`canSaveToElements`）
3. **样式** —— 以实际代码为准。工具条与分组筹码的硬边按键皮肤、设备选择框白底无阴影，由页面根类 `.inspector-workbench` 作用域承担；模块私有的间距与固定尺寸登记在模块 `tokens.css` 的 `--insp-*` 令牌。
   `index.vue` · `tokens.css` · `shared/styles/tokens.css`
4. **校验** —— 无字段级校验；两道门槛提示：「未选设备 → 灰键 + 提示」与两个冻结入口的点按提示。
5. **出口** —— 设备下拉的数据来自设备管理 `GET /api/devices/`；本页不自建端点。
   `api.ts`（`apiGetDevices`）

#### API契约

本页不自建端点，设备下拉消费设备管理接口：

1. **入口** —— `GET /api/devices/`，需登录，返回 `{status, data: {devices, current}}`。
2. **业务规则** —— 检查器只读该列表做过滤，**不写设备状态、不切换「当前设备」**。
3. **返回** —— 字段口径归设备管理，检查器只消费 `serial` / `model` / `brand` / `status` / `occupied_by`。
4. **校验** —— 无。
   `apps/device_pool/views.py`

#### 数据表单

无表单。设备选择框只是本地状态（`store.captureSerial`），不落库、不进 URL。

### 获取快照

#### UI交互

1. **模版** —— 工具条最左端：设备选择框（宽 280px，白底无阴影）+「获取」按键（⚡ 图标，文案在请求中变「获取中...」）。
   `components/CaptureForm.vue`
2. **业务逻辑**
   1. 点「获取」：有设备 → 发起抓取；成功即把快照载入元素表**并自动取一次分层数据**，无需再点任何按键；没设备 → 只提示、不发请求。
   2. 成功提示「获取成功（元素 N）」，并刷新历史快照列表。
   3. 请求期间按钮转圈（原生 disabled），不能重复点。
   4. 失败提示后端给的可读原因，并出现错误条；错误条上的「重试」重新发起这一次抓取。
   5. 抓取全程是一次**短连接**：不做占用、不加锁、不切「当前设备」。
   6. 载入新快照会把展示态复位 —— 选中元素、勾选集合、内联重命名全部清空，当前分组复位到第一个非空分组。
   `store.ts`（`capture` · `applyLayers`）
3. **样式** —— 以实际代码为准（按键几何与底色在页面作用域，`CaptureForm.vue` 不再重复声明）。
4. **校验** —— 只有「未选设备」这一道：灰键 +「按键不可用，请先选择设备」；设备不可用（被占用 / 不可达）的判定在后端。
5. **出口** —— `POST /api/inspector/capture/`，请求体只有 `{serial, method}`；**前端恒发 `method: 'dump'`**（OCR 链路前端已下线）。
   `api.ts`（`apiCapture`）

#### API契约

获取快照接口：POST api/inspector/capture/

1. **入口**
   1. 方法与路径：`POST api/inspector/capture/`。
   2. 尾斜杠必须带，不带是 404（`APPEND_SLASH=False`）。
   3. **需要登录**：走 DRF 默认 `IsAuthenticated`，未带令牌由网关中间件拦成 401「请先登录」。
   4. 请求字段：`serial`（先 trim）/ `method`（缺省 `dump`）。
   `apps/device_inspector/urls.py` · `views.py`
2. **业务规则**
   1. `method` 只认 `dump` 与 `ocr`，其它值一律 `400`「无效的获取方法」。
   2. 设备三连校验（全部在 `open_inspector_engine` 内，失败即拒绝、不产生任何快照行）：
      - `serial` 为空 → `409`「未选择设备，请先连接设备」；
      - `serial` 不在设备池 → `409`「设备未注册」；
      - 设备为 `BUSY` 且 `occupied_by` 命中执行引擎前缀 → `409`「设备正被执行引擎占用（{occupied_by}），请等待执行完毕」。
   3. 校验通过 → 按 `serial` 打开引擎短连接（连接地址取设备的 `connection_addr`，为空时退回 `serial`），**用完立即断开**。
   4. **先截图后解析** —— 截图先落盘（OCR 识别与元素缩略图裁剪都依赖它）。
   5. **dump 链路** —— 抓完整 UI 层级 → 对有身份的节点（有 resource_id / text / content_desc 或可点击）生成 XPath 候选（count 用**完整层级**算，保证定位语义准确）→ 裁剪层级（去纯布局容器 + 按 bounds 去重，保留最具体节点）→ 取可交互子集 → 按 bounds 从页面截图裁元素缩略图落盘。
   6. **ocr 链路**（前端已不再调用）—— 对截图做 OCR 识别 → 丢弃 base64 缩略图，改写为落盘路径。
   7. **失败不落库** —— dump 失败清理本批文件后报 500「获取失败」；OCR 失败清理后报 500「OCR 识别失败，请稍后重试」；其它未捕获异常记日志后报 500「获取失败」。
   8. **落库** —— 成功写 `di_snapshots` 一行；`created_by` 记当前 `user_id`；`device` 外键按 `serial` 回查（查不到则空，`SET_NULL`）；`screen_w/screen_h` 取设备 `displayWidth/Height`。
   9. **回写截图标识** —— 落库后把快照 ID 作为 `screenshot_id` 塞回 `dump_json` / `ocr_json`，标识这次结果对应哪张图。
   10. **不写 Redis、不加锁、不写 `el_` 表**。
   `apps/device_inspector/service.py` · `api.py`
3. **返回**
   1. `200` 快照全量 JSON（`snapshot_id` · `serial` · `method` · `package` · `activity` · `screen_w/h` · `element_count` · `actionable_count` · `elements` · `actionable` · `ocr_count` · `texts` · `screenshot_path` · `created_at`）。
   2. `400` 获取方法非法。
   3. `409` 设备不可用（未选 / 未注册 / 被引擎占用）。
   4. `500` 抓取失败。
   5. 统一信封 `{status, data}` / `{status, message}`；截图与缩略图只给**相对路径字符串**，前端经 `/media/` 拉取（不是 base64，也不是文件下载）。
   `shared/renderers.py`
4. **校验** —— 这个端点会给出的提示，共 6 条（按源码顺序）：
   1.「无效的获取方法」
   2.「未选择设备，请先连接设备」
   3.「设备未注册」
   4.「设备正被执行引擎占用（{occupied_by}），请等待执行完毕」
   5.「获取失败」
   6.「OCR 识别失败，请稍后重试」

#### 数据表单

| 表单 | 字段 | 类型 | 必填 | 约束 | 落到哪一列 |
|---|---|---|---|---|---|
| 获取快照 | `serial`（设备序列号） | 字符串 | 必填 | 前后空白先去掉；必须已在设备池注册且非执行引擎占用 | `di_snapshots.serial` |
| 获取快照 | `method`（抓取方式） | 字符串 | 否 | 只许 `dump` / `ocr`，缺省 `dump` | `di_snapshots.method` |

`di_snapshots` 的列（本模块**唯一自有表**，★ 是检查器真正读写的列）：

| 列 | 类型 | 长度 | 约束 / 说明 |
|---|---|---|---|
| ★ `id` | BigAutoField | — | 主键 · 唯一 · 非空 |
| ★ `device_id` | ForeignKey(`device_pool.Device`) | — | 可空；`on_delete=SET_NULL`；设备删除后快照仍留 |
| ★ `serial` | CharField | 100 | 默认空串；不随设备删除而清 |
| ★ `method` | CharField | 10 | 默认 `dump`（历史值 `both` 已由迁移 0002 改掉） |
| ★ `dump_json` | JSONField | — | 默认 `{}`；存 elements / actionable / counts / package / activity / screenshot_id |
| ★ `ocr_json` | JSONField | — | 默认 `{}`；存 texts / ocr_count / screenshot_id（前端已不展示） |
| ★ `screenshot_path` | CharField | 1000 | 默认空串；media 目录内相对路径 |
| ★ `package` / `activity` | CharField | 500 | 默认空串；dump 时取前台应用（取不到则空，不报错） |
| ★ `screen_w` / `screen_h` | IntegerField | — | 默认 0；设备 `displayWidth/Height` |
| `element_count` | IntegerField | — | 默认 0；裁剪后元素总数 |
| `actionable_count` | IntegerField | — | 默认 0；可交互子集数 |
| `ocr_count` | IntegerField | — | 默认 0；OCR 文本条数 |
| ★ `created_by` | CharField | 200 | 默认空串；当前 `user_id` 字符串，**五个快照端点的归属过滤键** |
| ★ `created_at` | DateTimeField | — | `auto_now_add`；列表倒序键 |

索引两枚：`created_at`、`device_id`。

落盘文件（媒体目录 `MEDIA_ROOT/inspector/`，不进数据库，只存相对路径）：

| 文件 | 谁写 | 说明 |
|---|---|---|
| `inspector/shots/capture_{时间戳}.png` | `capture_page_screenshot` | 整屏页面截图；时间戳 = `%Y%m%d_%H%M%S_%f` |
| `inspector/thumbs/{时间戳}/el_{i}.png` | `capture_dump_payload` | 按 bounds 从截图上裁的元素缩略图，`i` 是 actionable 子集下标 |
| `inspector/thumbs/{时间戳}/ocr_{i}.png` | `capture_ocr_payload` | OCR 文本缩略图（前端已不展示） |

> 后端 `method` 入参与 `ocr_json` 落库口径**保留不变**，但前端已不再发 `ocr`、界面也不再呈现 OCR —— 见文末附录第 5 条。

### 历史快照与回看

#### UI交互

1. **模版** —— 「历史快照」抽屉（宽 380px，标题「检查器快照」）：顶部一行总数；下面是快照条目列表，每条含
   1. 标题行 —— 「Dump · serial」（或历史 OCR 快照的「OCR · serial」）
   2. 副行 —— `package · 元素 N`
   3. 时间行 —— 本地化创建时间
   4. 右侧删除图标键
   `components/SnapshotListDrawer.vue`
2. **业务逻辑**
   1. 点「历史快照」打开抽屉；空列表时提示「暂无快照 / 获取成功后自动保存到这里」。
   2. **总数如实 + 一键清空** —— 顶部显示后端给的快照总数（不因列表封顶而变小）；右侧「清空」键删除本人全部历史快照，需二次确认（文案写明不可恢复），无快照时禁用。列表本身最多呈现近 10 条（后端保留上限）：第 11 条出现时自动淘汰最早的一条。
   3. 点条目（或回车 / 空格）→ 取该快照的**分层数据**载入元素表；抽屉随即关闭。
   4. 载入后展示态复位（与抓取成功同一套复位口径）。
   5. 列表与回看请求失败时给出可读原因并可「重试」。
   `store.ts`（`fetchSnapshots` · `viewSnapshot`）
3. **样式** —— 以实际代码为准（条目为硬边卡片，悬停变高亮）。
4. **校验** —— 无字段级校验。
5. **出口** —— 列表 `GET /api/inspector/snapshots/`，回看 `GET /api/inspector/snapshots/{id}/layers/`，清空 `DELETE /api/inspector/snapshots/clear/`。
   `api.ts`（`apiGetSnapshots` · `apiGetLayers` · `apiClearSnapshots`）

#### API契约

快照列表接口：GET api/inspector/snapshots/

1. **入口**
   1. 方法与路径：`GET api/inspector/snapshots/`；尾斜杠必须带。
   2. **需要登录**。
   3. 查询参数：`offset`（默认 0）/ `limit`（默认 100）；服务端另按**保留上限 10** 封顶（无论请求多大条数），`total` 恒为真实总数。
   `apps/device_inspector/urls.py` · `views.py`
2. **业务规则**
   1. **只列本人的快照** —— 按 `created_by = 当前 user_id` 过滤。
   2. 按创建时间倒序（同一时间再按 ID 倒序，与保留淘汰口径一致 —— 避免「展示的十条」与「保留的十条」不是同一批）。
   3. **保留近十条** —— 采集成功后自动淘汰本人最早的一条，保留上限 10。
   4. **一键清空** —— `DELETE /api/inspector/snapshots/clear/` 删除本人全部快照，媒体文件按「仍被元素定位引用则保留」判定；返回删除条数，无快照时返回 0（幂等）。
   5. 行内只给元信息，不含全量元素。
   `api.py`（`list_snapshots` · `snapshot_meta_dict`）
3. **返回**
   1. `200` `{total, items[]}`；`items[]` 字段：`id` · `serial` · `method` · `package` · `element_count` · `ocr_count` · `created_by` · `created_at`。
   2. `400` `offset` / `limit` 非整数。
   3. 统一信封。
4. **校验** —— 1 条：「无效的分页参数」（`int()` 转换失败时）。

快照详情接口：GET api/inspector/snapshots/{id}/

1. **入口**
   1. 方法与路径：`GET api/inspector/snapshots/{id}/`；尾斜杠必须带。
   2. **需要登录**；携带路径参数 `id`（快照 ID）。
   `apps/device_inspector/urls.py`
2. **业务规则**
   1. 只读，不改任何东西。
   2. **只给本人的快照** —— 按 `id + created_by` 联合查询；不存在或非本人一律同一个结论，不透露他人快照是否存在。
   3. 返回体与「获取快照」成功体同构（`snapshot_to_dict` 共用）。
   `views.py` · `api.py`
3. **返回**
   1. `200` 快照全量 JSON。
   2. `404`「快照不存在」。
   3. 统一信封。
4. **校验** —— 1 条：「快照不存在」。

#### 数据表单

无表单，只读 `di_snapshots`；列表不返回 `dump_json` / `ocr_json`，详情返回。

### 元素分组（分层查询）

> 这一节覆盖「元素分组列表」「元素档案表」与「手机屏幕」三栏联动 —— 它们是同一份分层数据的三个消费面。分组判定与主定位口径以 `openspec/specs/element-layering` 为准，查询契约以 `device-inspector-layers` 为准。

#### UI交互

1. **模版** —— 工作区两栏（左栏内部再分两列）：
   1. **元素分组列表** —— 纵向筹码列，标题「元素分组」，共五个固定顺序项：布局容器 · 滚动·集合容器 · 内容控件·文本 · 内容控件·图标 · 内容控件·其它；每项显示「分组名 + 元素数」。**不提供「全部」复位项**（已选分组不可清空）；无数据时空态「暂无分组数据」。
   2. **元素档案表** —— 分页栏（「第 X / Y 页 · 共 N 条」+「上一页 / 下一页」）压在表纸之上；表纸 15 列：选择 · 缩略图 · 元素名称 · 序号 · 类名 · 资源标识 · 文本 · 描述 · 坐标 · 层级 · 父内序号 · 细类 · 保留 · 交互标志 · 主定位。
   3. **手机屏幕** —— 按截图真实像素比例适配的手机框，叠一层 canvas 高亮；框用**当前分组色**画出该分组全部元素（实线＝被展示裁剪保留，虚线＝被裁）；无截图时是空态（圆环动画 +「暂无页面快照」+ 提示语）。
   4. 覆盖层：缩略图放大预览弹窗。
   `components/StructureAnalysisPanel.vue` · `components/ScreenshotView.vue`
2. **业务逻辑**
   1. **分组视图是唯一视图** —— 工具条上没有「结构分析 / 返回元素列表」切换键，也没有第二张元素表；抓取或回看后**自动**取一次分层数据。
   2. **分组联动** —— 点某一分组筹码 → 表格只列该分组元素、手机屏幕只画该分组的框。**没有复位项**；切分组只改本地展示范围，不发请求。
   3. **行选中联动** —— 写入选中（手机画面红描边 + 淡红填充，同一时间只保留一个）有两条入口：**左键双击数据格**（序号 / 类名 / 资源标识 / 文本 / 描述 / 坐标 / 层级 / 父内序号 / 细类 / 保留 / 交互标志 / 主定位，含格内文字上下空白）；**左键单击「缩略图」列整格**（含该列为空占位的情形）。单击其它单元格不改动选中；单击「元素名称」只进入重命名；双击「元素名称」「勾选」「缩略图」也不改选中。
   4. **元素名称口径** —— 当次自定义名 > 已存别名 `alias` > `text` > `resource_id` >「—」；**单击名称格进入内联重命名**（Enter 提交 / 失焦提交 / 清空即撤销自定义名），且仅在展示真实快照（`snapshot_id` 非空）时可改。
   5. **主定位列口径** —— 显示 `primary.xpath`；`primary.stable` 为假时追加「不稳定」标签；无主定位显示「—」。
   6. **交互标志列** —— 七项标志（可点击 / 可长按 / 可滚动 / 可勾选 / 已勾选 / 启用 / 可聚焦）按固定顺序渲染为标签，全为假时不渲染标签。**没有「指标」列**（该列已随分层改版删除）。
   7. **缩略图** —— 列宽 66px 的缩略图格：左键单击＝定位（在手机画面上高亮该元素），双击＝打开放大预览（附名称 / Class / ID / Desc / Bounds / 细类 / 交互标志 / 主定位）；无缩略图数据或图片加载失败一律显示「—」占位，放大图失效显示「缩略图已失效」。
   8. **勾选 = 保存范围** —— 表头全选**只作用于当前页所示行**；已勾选行跨页、跨分组保持（切分组不清空勾选）。
   9. **分页固定 14 行** —— 不提供「显示行数」选择器；切分组或换快照后回到第 1 页。
   10. **空态统一一句** —— 未选设备、未获取、分组无元素，表体统一显示「未选中设备」（说明语「选择设备后点击「获取」，或从快照列表回看」）。
   11. **无 WebView 提示** —— 检查器不判定也不提示 WebView（第一代分区算法退役后无此能力）。
   12. **手机屏幕高亮** —— 当前分组全部元素按分组色画框（实线 / 虚线区分保留与被裁）；悬停元素填橙并加粗描边（命中取面积最小的那个元素）；选中的元素填淡红 + 红描边；选中后若在可视区外，手机框平滑滚到它。
   13. **横向滚动与首列冻结** —— 列宽合计超出栏宽时横向滚动由表格自身承载，并支持按住拖拽平移；选择 / 缩略图 / 元素名称三列左侧冻结，冻结列底色不透明。
   14. **分层来源如实标注** —— 历史快照没有全量节点索引时，工具条显示「历史快照无全量索引：当前为该快照的保留集，不含被展示裁剪丢弃的元素」。
   `store.ts`（`fetchLayers` · `activeGroupId` · `selectElement` · `toggleCheck` · `nameOverrides` · `retry`）· `StructureAnalysisPanel.vue` · `ScreenshotView.vue`
3. **样式** —— 以实际代码为准。五个分组各有一色（登记在 `constants.ts` 的 `LAYER_GROUPS`）、冻结列底色、缩略图边长、放大预览落影等登记在组件与模块令牌；列宽与表格最小宽（= `ELEMENT_COLUMN_WIDTHS` 各列之和）唯一登记在 `constants.ts`。
   `StructureAnalysisPanel.vue` · `ScreenshotView.css` · `constants.ts` · `tokens.css`
4. **校验** —— 无字段级校验；门槛提示为按键可用性一类（两个冻结入口的原因见「页面骨架与设备选择」）。
5. **出口** —— `GET /api/inspector/snapshots/{id}/layers/`。
   `api.ts`（`apiGetLayers`）

#### API契约

分层查询接口：GET api/inspector/snapshots/{id}/layers/

1. **入口**
   1. 方法与路径：`GET api/inspector/snapshots/{id}/layers/`；尾斜杠必须带。
   2. **需要登录**；路径参数 `id` 为快照 ID。
   3. 查询参数（全部可选）：`group`（一级分组 key）/ `sub`（二级分组 key，仅当 `group=content_widget` 时有效）/ `flag`（交互标志，可重复）/ `q`（关键词，对文本、资源标识、内容描述、类名做忽略大小写的子串匹配）/ `only_kept=1` / `only_stable=1` / `offset` / `limit`。
   `apps/device_inspector/urls.py` · `views.py`
2. **业务规则**
   1. **纯计算、不落库、不碰设备** —— 分层由快照的全量节点索引即时算出；查询不建立设备连接，无设备在线时同样成功。
   2. **只查本人的快照** —— 按 `id + created_by` 查；不存在或非本人 → `404`。
   3. **摘要恒为全量、条目按筛减** —— `summary.groups` 的分组计数（元素数 / 保留数 / 主定位稳定数 / 可点击数 / 可滚动数）与筛减条件无关，`total_matched` 才是筛减后的条数；条目里的主定位恒为一条，**不含候选列表**。
   4. **缺省条数不截断** —— 未给 `limit` 时返回自 `offset` 起的全部命中，响应 `limit` 为 `null`（不透支一个未生效的上限）；显式给 `limit` 时服务端再按 500 封顶。
   5. **历史快照降级** —— 没有全量节点索引的快照降级为「仅保留集」，响应 `source` 标注为 `legacy`（有索引时为 `index`）。
   6. **非法值不静默** —— 未知一级 / 二级分组、`sub` 与 `group` 不匹配、未知交互标志、不可解析的分页参数一律 `400` 与可读消息。
   `apps/device_inspector/api.py`（`list_layers`）· `algorithms/element_layers.py`（`build_layers`）
3. **返回**
   1. `200` `{snapshot_id, source, package, activity, screen{w,h}, screenshot_path, summary{total, groups[]}, total_matched, offset, limit, elements[]}`；`groups[]` 每项 `{key, name, level, count, kept, stable_primary, clickable, scrollable, children[]}`（仅 `content_widget` 带三个 `children`）。
   2. 元素条目字段见接口文档「快照分层查询接口」。
   3. `400`「未知的一级分组 / 未知的二级分组 / 二级分组只在一级分组为内容控件时有效 / 未知的交互标志 / 无效的分页参数」。
   4. `404`「快照不存在」。
   5. 统一信封。
4. **校验** —— 5 类：未知一级分组、未知二级分组、二级与一级不匹配、未知交互标志、无效分页参数。

#### 数据表单

无表单、**不写库**；分层查询的输入是 `di_snapshots.nodes_json`（全量节点索引，历史快照降级为 `dump_json.elements`），输出是即时计算的 JSON。

> **前端当前未使用服务端筛减参数** —— `store.fetchLayers` 只传快照 ID，取回全量条目后按分组在本地过滤（分组筹码的计数取后端摘要）；服务端筛减参数保留给将来需要它的调用方。

### 保存到元素定位

> **当前冻结**：「保存到元素定位」入口处于禁用态（原因「元素下标口径已随全量元素展示变更，保存链路待后续变更对齐，暂不可用」），点按只提示原因、不发请求；下列是冻结前的实现口径，后端端点与代码路径均保留。

#### UI交互

1. **模版** —— 「保存到元素定位」弹窗（宽 520px，点遮罩不关闭）：
   1. 目录路径 —— 级联选择器，占位「逐层选择目录（不选 = 根目录）」，清空即根目录，只列目录节点。
   2. 保存目标 —— 单选「已有页面 / 新建页面」。
   3. 已有页面 —— 下拉「选择该目录下的页面」。
   4. 新建页面 —— 输入「新页面名称」，打开时默认填当前快照的 `package`。
   5. 页脚「取消 / 保存」，保存键在请求中转圈。
   `components/SaveToElementsDialog.vue`
2. **业务逻辑**
   1. 打开即拉元素定位的页面树，并把表单复位到「已有页面」。
   2. **筛减口径** —— 勾选非空且少于全量时按勾选筛减；勾选为空（点击时）直接拦截；勾选为全量时不带 `element_ids`（等价全量）。
   3. **内联重命名 → 别名** —— 结构表里改过的「元素名称」按 `resource_id` 映射成 `aliases` 一起提交；`resource_id` 为空的元素不带别名。
   4. 成功提示「已保存 N 个元素（M 个已更新，K 个跳过）」，关闭弹窗并刷新历史快照列表。
   5. 失败提示后端给的可读原因（同级重名等冲突文案原样呈现），**不吞成通用文案**。
   6. **回看态不可保存** —— 当前展示的是「已保存页面」时（无 `snapshot_id`），「保存到元素定位」是灰键，点它只提示。
   `store.ts`（`saveToElements` · `checkedIds` · `nameOverrides`）· `index.vue`
3. **样式** —— 以实际代码为准（弹窗内 EP 按键沿用页面作用域的硬边皮肤）。
4. **校验** —— 2 条表单必填（走 EP `:rules`，字段内联提示）：
   1. 已有页面模式：「请选择要保存到的页面」
   2. 新建页面模式：「请填写新页面名称」
   另 1 条门槛提示（非表单校验）：「请先勾选要保存的数据」（勾选为空时拦截，**不发请求**）。
5. **出口** —— `POST /api/inspector/snapshots/{id}/save-elements/`，请求体 `{page_label, folder_path, page_id?, element_ids?, aliases?}`，**恒不带 `include_ocr`**。
   `api.ts`（`apiSaveToElements`）

#### API契约

元素保存接口：POST api/inspector/snapshots/{id}/save-elements/

1. **入口**
   1. 方法与路径：`POST api/inspector/snapshots/{id}/save-elements/`；尾斜杠必须带。
   2. **需要登录**；路径参数 `id` 为快照 ID。
   3. 请求字段：`page_label` / `folder_path` / `page_id` / `element_ids` / `aliases`，全部可选，按组合决定模式。
   `apps/device_inspector/urls.py` · `views.py`
2. **业务规则**
   1. **两种模式** —— 传 `page_id`（须为整数字符串）= 保存到已有页面（元素 upsert 追加）；否则 `page_label`（+ `folder_path`）= 新建页面（目录按 `/` 逐层查找或创建）。
   2. **本地校验三连**（全部经 `ValueError` 翻译成 `400`）：
      - 快照不存在或非本人 → 「快照不存在」；
      - 未传 `page_id` 且 `page_label` 为空 → 「页面名称不能为空」；
      - 快照 `dump_json.elements` 为空 → 「该快照无元素数据」。
   3. **筛减** —— 按下标取勾选元素（越界 / 非整数下标直接丢弃）；勾选为空则取全量。
   4. **别名回填** —— 按 `resource_id` 命中 `aliases` 的元素写入 `alias`。
   5. **写库经对方白名单** —— 元素与页面一律经 `element_locator.api.import_snapshot_page`，**本模块不直接 ORM 写 `el_` 表**（防火墙）。
   6. **元素 upsert 口径** —— 按 `(page, resource_id, bounds)` 去重；命中即更新，否则新增；别名兜底顺序 `alias` → `text` → `resource_id`；最后重算目标页面的 `element_count`。
   7. **已有页面补全** —— 目标页面的截图 / OCR / `snapshot_id` 为空时才补，已有内容不覆盖。
   8. **页面级 OCR 不落库** —— 传给 `import_snapshot_page` 的 `ocr_json` 恒为 `None`；快照自身的 OCR 仍留在 `di_snapshots.ocr_json`。
   9. **冲突翻译** —— 目录层级超限 / 同级页面重名 / 目标目录异常经 `ImportConflictError` 翻成 `409`。
   `apps/device_inspector/api.py`（`save_snapshot_to_elements`）· `apps/element_locator/api_snapshot.py`（`import_snapshot_page`）
3. **返回**
   1. `200` `{saved, updated, skipped, page_id}`（`skipped` 当前实现恒为 0，是预留字段）。
   2. `400` 快照不存在 / 页面名称不能为空 / 该快照无元素数据 / 元素数据不能为空 / 目标页面不存在。
   3. `409` 同级页面已存在 / 目录层级超限 / Android 项目或目标目录异常。
   4. `500`「保存失败」（其它未捕获异常，已记日志）。
   5. 统一信封。
4. **校验** —— 这个端点会给出的提示（按源码顺序）：
   1.「快照不存在」
   2.「页面名称不能为空」
   3.「该快照无元素数据」
   4.「元素数据不能为空」
   5.「目标页面不存在」
   6.「同级页面「{page_label}」已存在」
   7.「目录最多嵌套 20 层」
   8.「Android 项目不存在」
   9.「目标目录不存在」
   10.「保存失败」

   > 第 7 条的上限是 `api_snapshot.MAX_DEPTH = 20`；接口文档写的「5 层」（取自 `page_tree.MAX_PAGE_TREE_DEPTH`，属元素定位页面树自己的口径）与代码相反，本 PRD 以**代码**为准。

#### 数据表单

| 表单 | 字段 | 类型 | 必填 | 约束 | 落到哪一列 |
|---|---|---|---|---|---|
| 保存到元素定位 | `page_label`（新页面名称） | 字符串 | 新建模式必填 | 去空白后非空；同级不可重名 | `el_pages.label` |
| 保存到元素定位 | `folder_path`（目录路径） | 字符串 | 否 | 按 `/` 逐段查找或创建；空 = 项目根 | `el_directories`（跨模块） |
| 保存到元素定位 | `page_id`（已有页面 ID） | int | 与上二者二选一 | 必须指向非目录页面 | `el_pages.id` |
| 保存到元素定位 | `element_ids`（勾选下标） | int[] | 否 | 相对 `dump_json.elements` 的下标；空 = 全部 | 决定写入 `el_elements` 的行集合 |
| 保存到元素定位 | `aliases`（别名映射） | object | 否 | `{resource_id: 中文别名}` | `el_elements.alias` |

写入目标（跨模块，字段名以元素定位为准）：

| 表 | 键字段 | 本接口写入方式 |
|---|---|---|
| `el_pages` | `label` · `package` · `activity` · `screenshot_path` · `snapshot_id` · `element_count` | 新建一行，或对已有页面补全空值 |
| `el_elements` | `class_name` · `text_val` · `content_desc` · `resource_id` · `bounds` · `xpath_candidates` · 坐标四件套 · 交互标志 · `thumbnail_path` · `alias` | 按 `(page, resource_id, bounds)` upsert |

> 快照元素字段名与元素定位字段名不同名：快照是 `text`，元素定位是 `text_val`；`xpaths` 落库时序列化成 `xpath_candidates` 字符串，读回时解析为 list。

### 已保存页面只读回看

> **当前冻结**：「已保存页面」入口处于禁用态（原因「存量已保存页面数据已作废，功能冻结」），点按只提示原因、不发请求；下列是冻结前的实现口径，入口与代码路径均保留（见规格 `device-inspector-page` 的「已保存页面入口冻结」）。

#### UI交互

1. **模版** —— 「已保存页面」弹窗（宽 560px）：
   1. 自绘标题 —— 「已保存页面」+ 一枚「只读」标签。
   2. 页面树 —— 目录节点可展开 / 收起，页面节点为叶子；页面节点两行：名称一行，`package（无则 —） · 元素 N` 一行；目录下的页面与子目录相对父目录逐层缩进。
   3. 空态 —— 「暂无已保存页面 / 请先在元素定位保存页面」。
   `components/SavedPagePicker.vue`
2. **业务逻辑**
   1. 打开即拉元素定位页面树并默认展开所有目录。
   2. **点目录只展开 / 收起**，不切换回看；**点页面**才打开该页的只读回看，弹窗随即关闭。
   3. 回看态把元素挂进**同一张结构表格**：分组列按后端摘要照常显示、主定位列按条目如实显示（**无「指标」列**）；缩略图 / 元素名称 / 资源标识 / 文本 / 主定位 / 坐标六列口径与快照视图一致。
   4. 回看态**不伪造分组** —— 不调分层端点，直接把已保存页面视图的元素塞进结构视图。
   5. 回看态的 `snapshot_id` 为空 → 「保存到元素定位」自动变灰键。
   6. 请求失败给出可读原因。
   `store.ts`（`viewSavedPage`）· `components/SavedPagePicker.vue`
3. **样式** —— 以实际代码为准（页面节点有墨线卡片与悬停高亮，目录节点无卡片；树行最小高 52px 以容纳两行）。
4. **校验** —— 本选择器**不提供**搜索、删除或重命名；无字段级校验。
5. **出口** —— `GET /api/inspector/pages/{page_id}/`（页面树本身来自元素定位的页面列表接口）。
   `api.ts`（`apiGetPageView`）

#### API契约

页面只读视图接口：GET api/inspector/pages/{id}/

1. **入口**
   1. 方法与路径：`GET api/inspector/pages/{id}/`；尾斜杠必须带。
   2. **需要登录**；路径参数 `id` 是**元素定位页面 ID**（`el_pages`），不是快照 ID。
   `apps/device_inspector/urls.py` · `views.py`
2. **业务规则**
   1. 只读，不改任何东西。
   2. 页面不存在、或该节点其实是目录 → `404`「页面不存在」。
   3. 转发给 `element_locator.api.get_page_full`，返回元素定位自己的字段口径（`text_val` / `alias` / `is_test_point` 等）。
   4. 该端点**没有按 `created_by` 过滤** —— 见文末附录第 3 条。
   `apps/device_inspector/api.py`（`get_page_view`）· `apps/element_locator/api_snapshot.py`（`get_page_full`）
3. **返回**
   1. `200` `{page_id, label, package, activity, screenshot_path, element_count, ocr_json, elements[]}`；`elements[]` 含 `id` / `class_name` / `text_val` / `content_desc` / `resource_id` / `bounds` / `xpaths` / 坐标四件套 / `depth` / `index` / `clickable` / `enabled` / `scrollable` / `checked` / `thumbnail_path` / `alias` / `is_test_point`。
   2. `404`「页面不存在」。
   3. 统一信封。
4. **校验** —— 1 条：「页面不存在」。

#### 数据表单

无表单、不写库；只读 `el_pages` 与 `el_elements`。前端把 `text_val` 映射回 `text`、补上 `_idx` / `_rowKey` 后复用同一张结构表。

### 删除快照

#### UI交互

1. **模版** —— 历史快照条目右侧的删除图标键（无底无边的图标形态，危险色）。
2. **业务逻辑**
   1. 点删除 → 先弹二次确认（标题「删除快照」，文案「删除后该快照与其截图 / 缩略图文件不可恢复」，确认键「删除」/ 取消键「取消」）。
   2. 取消（或按 ESC）**不发请求**，列表不变。
   3. 确认后调删除接口；成功提示「快照已删除」并刷新列表。
   4. **删的正是当前展示的那一份** → 元素表、元素分组、选中元素与勾选集合立即回到无快照空态，工具条计数消失、手机屏幕回到无截图空态。
   5. 失败给出可读原因。
   `components/SnapshotListDrawer.vue` · `store.ts`（`deleteSnapshot`）
3. **样式** —— 以实际代码为准（图标键被页面皮肤正向排除，不套硬边按钮几何）。
4. **校验** —— 无字段级校验；二次确认是唯一门槛。
5. **出口** —— `DELETE /api/inspector/snapshots/{id}/delete/`。
   `api.ts`（`apiDeleteSnapshot`）

#### API契约

快照删除接口：DELETE api/inspector/snapshots/{id}/delete/

1. **入口**
   1. 方法与路径：`DELETE api/inspector/snapshots/{id}/delete/`；尾斜杠必须带。
   2. **需要登录**；无请求体，路径参数 `id` 为快照 ID。
   `apps/device_inspector/urls.py`
2. **业务规则**
   1. **只删本人的** —— 按 `id + created_by` 查；不存在或非本人 → `404`。
   2. 先尽力清理关联文件，再删数据库行：截图文件直接按 `screenshot_path`；缩略图目录从元素或 OCR 的首个 `thumbnail_path` 反推（`thumbs/{时间戳}`）。
   3. **文件清理是尽力而为** —— 失败只告警，**不影响删除结果**（数据库行照删）。
   `apps/device_inspector/api.py`（`delete_snapshot`）· `service.py`（`delete_snapshot_files`）
3. **返回**
   1. `200` `data: {deleted: true}`。
   2. `404`「快照不存在」。
   3. 统一信封。
4. **校验** —— 1 条：「快照不存在」。

#### 数据表单

无表单。删除会动两类存储：

| 存储 | 操作 | 说明 |
|---|---|---|
| `di_snapshots` | `DELETE` 一行 | 数据库行的删除是硬性的 |
| `MEDIA_ROOT/inspector/…` | 删截图 + 删该批缩略图目录 | 尽力清理，失败仅 `logger.debug` 告警 |

> 本模块**不写 Redis**，与登录模块的令牌吊销无关。

### 跨模块消费：AI 截图

#### UI交互

1. **模版** —— **无界面**。消费方是 AI 助手的视觉链路工具 `screenshot_page`（工具箱里挂在「设备检查器」分类下，标记为只读）。
2. **业务逻辑**
   1. 工具调 `device_inspector.api.capture_screen(serial)` 取当前屏幕图 —— **只截屏，不 dump、不 OCR、不落快照记录**。
   2. 截图仍由检查器落盘（媒体目录），工具把文件读出来压到 1280px 内、转 JPEG 后回给视觉模型；`keep_local` 为真时才在摘要里回传相对路径。
   3. 路径由工具回传真相，禁止模型在 JSON 里自己抄路径。
   `apps/ai_assistant/tools.py`（`screenshot_page`）· `apps/device_inspector/api.py`（`capture_screen`）
3. **样式** —— 无。
4. **校验** —— 同「获取快照」的设备三连校验（复用 `open_inspector_engine`）。
5. **出口** —— 同进程直调 `api.capture_screen`，**不走 HTTP**。

#### API契约

本功能不新增 HTTP 端点，走同进程的跨模块白名单函数：

1. **入口** —— `apps.device_inspector.api.capture_screen(serial)`，属 `api.py` 的 `__all__` 白名单（8 个函数之一）。
2. **业务规则**
   1. 设备可用性校验与「获取快照」同源；`serial` 非法直接抛错。
   2. 只截屏落盘并回 `{screenshot_path, serial, package, activity, screen_w, screen_h}`。
   3. **不产生 `di_snapshots` 记录** —— 因此不占历史快照列表。
   4. 调用方（AI 助手）只经 `api.py`，不 import `service.py`，也不直写 `di_` 表。
3. **返回** —— 上述 dict；异常由调用方翻译。
4. **校验** —— 无独立文案；错误沿用设备校验口径，由 AI 工具层包装。

#### 数据表单

无表单、**不落库**；只在媒体目录新增一张截图文件，不进 `di_snapshots`。

### 失败呈现与重试

> 这一节不是端点，是「页面上的每次请求失败怎么被看见、怎么被重发」，横跨上面各功能。

#### UI交互

1. **模版** —— 工具条右侧的错误条（共享 `ErrorState` 组件），显示后端给的可读原因 +「重试」键。
2. **业务逻辑**
   1. 失败原因**必须**取后端返回的 `message`（经共享净化 `formatApiError`），**不允许**用与该原因无关的通用文案顶替。
   2. 「重试」**真的重发最近失败的那一个请求**，不是只清提示；请求成功后错误条消失。
   3. 同一来源的请求成功即撤掉该来源的失败提示，避免旧错误常驻。
   4. 可重试的来源共四类：设备列表 / 快照列表 / 抓取 / 分层查询。
   `store.ts`（`setError` · `clearErrorFor` · `retry`）
3. **样式** —— 以实际代码为准（共享件，本页不改其外观）。
4. **校验** —— 无。
5. **出口** —— 按来源重发对应的 `api.ts` 函数。

#### API契约

本节不新增端点；约束落在各端点的 `message` 质量与前端 `formatApiError` 的净化口径上。

#### 数据表单

错误记录只存在前端内存：`{message, source}` 加一个 `lastFailedSnapshotId`，不持久化。

---

## 测试

> 本模块各功能的测试资产按功能分节登记，每节含「业务场景 · 接口自动化测试用例 · 前端单元层测试用例」；逐条用例文档见 `dev_docs/DEV_TEST/`。
> **现状**：本模块有**接口层**、**灰盒单元层**、**灰盒集成层**与**前端 P0 单测**四层资产；**端到端层为 0**（e2e 套件当前只覆盖登录模块）。

### 页面骨架与设备选择

1. **业务场景** —— 从功能出发；每条末尾的【】标出它覆盖了哪一项。

   **UI交互侧**
   - 骨架常驻【模版 · 业务逻辑 1】—— WHEN 打开 `/inspector` 且无任何快照 → THEN 工具条、元素分组列表、元素表列与手机屏幕列同时出现，各数据区显示空态
   - 未选设备时灰键【业务逻辑 4】—— WHEN 没选设备就点「获取」或「保存到元素定位」→ THEN 不发请求，只提示「按键不可用，请先选择设备」
   - 下拉过滤【业务逻辑 2】—— WHEN 设备列表里有被执行引擎占用的设备 → THEN 它不出现在下拉里
   - 已保存页面回看态的保存键【业务逻辑 5】—— WHEN 当前展示的是已保存页面 → THEN 「保存到元素定位」为灰键
   - 窄屏折行【业务逻辑 6】—— WHEN 窗口宽度 ≤1200px → THEN 结构区与手机屏幕折成上下两行

2. **测试用例** —— **无自动化**：本功能的接口资产不在检查器内（设备列表归设备管理），前端骨架断言目前零覆盖。

3. **自动化覆盖的测试用例**
   - 无。**缺口：页面骨架与设备选择的灰键 / 复位行为没有任何自动化断言。**

### 获取快照

1. **业务场景**

   **UI交互侧**
   - 一键获取并自动载入分层【业务逻辑 1】—— WHEN 选定可用设备点「获取」→ THEN 成功后元素表立即填充、分组徽标立即出现，无需再点按键
   - 成功提示与列表刷新【业务逻辑 2】—— WHEN 抓取成功 → THEN 提示「获取成功（元素 N）」且历史快照列表多出一条
   - 提交中不可重复点【业务逻辑 3】—— WHEN 点了「获取」→ THEN 按钮转圈且不能再点
   - 失败显示后端原因【业务逻辑 4】—— WHEN 设备被执行引擎占用 → THEN 提示含占用原因（形如「设备正被执行引擎占用（runner-xxx），请等待执行完毕」），不是「获取失败」
   - 展示态复位【业务逻辑 6】—— WHEN 载入新快照 → THEN 选中元素、勾选与重命名全部清空，当前分组复位到第一个非空分组

   **业务功能侧**
   - 未选设备【业务规则 2】—— WHEN `serial` 为空 → THEN `409`「未选择设备，请先连接设备」
   - 未注册设备【业务规则 2】—— WHEN `serial` 不在设备池 → THEN `409`「设备未注册」
   - 方式非法【业务规则 1】—— WHEN `method` 不是 `dump` / `ocr` → THEN `400`「无效的获取方法」
   - 成功落库【业务规则 8】—— WHEN 校验通过且抓取成功 → THEN `di_snapshots` 多一行，`created_by` 为当前用户，返回体与详情端点同构
   - 失败不落库【业务规则 7】—— WHEN dump 抓取抛异常 → THEN 返回 `500`，且不产生快照行、本批截图与缩略图被清理
   - 不占设备【业务规则 3 · 10】—— WHEN 完成一次抓取 → THEN 设备的 `occupied_by` 与 `status` 未被本模块改写，Redis 无新键

   > **对应规格**：`openspec/specs/device-inspector-page`（抓取方式恒为 Dump · 请求失败如实呈现原因）· `api-path-convention`

2. **测试用例** —— 活体用例**已落地**（`tests/api/case/inspector.yaml`，由 `tests/api/test_inspector.py` 驱动）：

   | 编号 | 标题 | 请求 | 期望 |
   |---|---|---|---|
   | TC-INS-001 | 快照抓取未登录 | `POST /api/inspector/capture/`（无 token） | `HTTP 401` +「请先登录」|
   | TC-INS-010 | 抓取非法 method | `method=both` | `HTTP 400` +「无效的获取方法」|
   | TC-INS-011 | 抓取未选设备 | `serial=""` | `HTTP 409` +「未选择设备，请先连接设备」|
   | TC-INS-012 | 抓取未注册设备 | `serial=no_such_serial_xyz` | `HTTP 409` +「设备未注册」|

   > **未落地**：抓取成功路径（需真机）、执行引擎占用冲突（需造占用）、dump 失败清理（需注入故障）。

3. **自动化覆盖的测试用例**
   - `tests/api/test_inspector.py` —— 驱动上述 YAML 用例（与其它端点共用同一份驱动）
   - **缺口：抓取成功、占用冲突、失败清理三条均无自动化。**

### 历史快照与回看

1. **业务场景**

   **UI交互侧**
   - 空态【业务逻辑 1】—— WHEN 还没有任何快照 → THEN 抽屉提示「暂无快照 / 获取成功后自动保存到这里」
   - 总数如实与一键清空【业务逻辑 2 · 4】—— WHEN 快照数超过保留上限 → THEN 顶部仍显示真实总数、列表最多近 10 条；WHEN 点「清空」并在确认框点「清空」→ THEN 本人全部快照被删除，列表、表格与画面回到空态
   - 回看自动载入分层【业务逻辑 3】—— WHEN 点一条快照 → THEN 元素填入表格且分组徽标立即出现，抽屉关闭
   - 回看复位【业务逻辑 4】—— WHEN 回看另一条快照 → THEN 展示态与抓取成功时一样复位

   **业务功能侧**
   - 列表分页【业务规则 1 · 2】—— WHEN 带 `offset/limit` 请求 → THEN 只返回本人快照、按创建时间倒序
   - limit 上限【入口 3】—— WHEN `limit=500` → THEN 实际返回不超过保留上限 10 条，而 `total` 仍是真实总数
   - 分页参数非法【校验】—— WHEN `offset` / `limit` 非整数 → THEN `400`「无效的分页参数」
   - 详情只给本人【业务规则 2】—— WHEN 用他人的快照 ID 请求详情 → THEN `404`「快照不存在」，不透露存在性

   > **对应规格**：`device-inspector-page`（快照列表如实反映总量）

2. **测试用例** —— 活体用例**已落地**（`tests/api/case/inspector.yaml`）：

   | 编号 | 标题 | 请求 | 期望 |
   |---|---|---|---|
   | TC-INS-002 | 快照列表未登录 | `GET /api/inspector/snapshots/`（无 token） | `HTTP 401` +「请先登录」|
   | TC-INS-003 | 快照详情未登录 | `GET /api/inspector/snapshots/1/`（无 token） | `HTTP 401` +「请先登录」|
   | TC-INS-020 | 快照列表正常返回 | 带 token | `HTTP 200` + schema `snapshot_list`（`{total, items}`）|
   | TC-INS-030 | 快照详情不存在 | `.../snapshots/999999999/` | `HTTP 404` +「快照不存在」|

   > **未落地**：**跨用户归属**（需两个账号）与 `limit` 截断到保留上限的边界断言。

3. **自动化覆盖的测试用例**
   - `tests/api/test_inspector.py` —— 驱动 `snapshot_list` / `error` 两种 schema 断言
   - **缺口：跨用户越权与分页截断无自动化。**

### 元素分组（分层查询）

1. **业务场景**

   **UI交互侧**
   - 自动载入分层，无切换键【业务逻辑 1】—— WHEN 抓取或回看成功 → THEN 分组徽标立即出现，工具条上没有「结构分析 / 返回元素列表」
   - 分组联动【业务逻辑 2】—— WHEN 点某分组筹码 → THEN 表格只列该分组元素、手机屏幕只画该分组的框；没有「全部」复位项，切分组不发请求
   - 双击数据格画红框【业务逻辑 3】—— WHEN 单击「资源标识」→ THEN 手机画面不变；WHEN 左键双击数据格 → THEN 该元素坐标出现红描边 + 淡红填充，再双击另一行则红框移走
   - 单击缩略图列画红框【业务逻辑 3】—— WHEN 左键单击「缩略图」列（含该列为空占位）→ THEN 手机画面高亮该元素，且不进入重命名、不改动勾选
   - 单击名称只重命名【业务逻辑 4】—— WHEN 单击「元素名称」→ THEN 该格进入重命名，手机画面红框不变
   - 主定位口径【业务逻辑 5】—— WHEN 元素的候选里没有唯一命中项 → THEN 主定位列显示最接近的一条并带「不稳定」标签
   - 勾选跨页跨分组保持【业务逻辑 8】—— WHEN 第 1 页勾 3 行、翻到第 2 页勾 2 行、再切到另一分组 → THEN 已勾选 5 行仍在，保存范围含这 5 行
   - 表头全选只作用当前页【业务逻辑 8】—— WHEN 点表头全选 → THEN 当前 14 行被勾选，其他页已勾选行不被清空
   - 固定 14 行分页【业务逻辑 9】—— WHEN 共 40 行 → THEN 首屏 14 行、显示「第 1 / 3 页 · 共 40 条」，无「显示行数」选择器；切分组后回第 1 页
   - 空态统一一句【业务逻辑 10】—— WHEN 未选设备 / 未获取 / 分组无元素 → THEN 表体统一显示「未选中设备」
   - 分层来源如实标注【业务逻辑 14】—— WHEN 打开一份没有全量节点索引的历史快照 → THEN 工具条出现「历史快照无全量索引…」提示
   - 手机屏幕高亮【业务逻辑 12】—— WHEN 悬停某元素 → THEN 它填橙并加粗描边，命中取面积最小的元素；WHEN 选中在可视区外的元素 → THEN 手机框平滑滚到它
   - 横向滚动与冻结列【业务逻辑 13】—— WHEN 表格横向拖到最右 → THEN 选择 / 缩略图 / 元素名称三列仍可见，冻结列底色不透出下层

   **业务功能侧**
   - 纯计算不落库【业务规则 1 · 3】—— WHEN 请求分层数据 → THEN 由全量节点索引即时算出，**不产生任何写库动作**、不访问设备
   - 分组判定与计数【业务规则 3】—— WHEN 元素类名不在任何集合内 → THEN 归「其它」；摘要里一级四个分组与内容控件三个二级分组的计数恒为全量（与筛减条件无关）
   - 条目只给一条主定位【业务规则 3】—— WHEN 返回任一元素 → THEN 含一条主定位，**不含候选列表**
   - 缺省不截断【业务规则 4】—— WHEN 不带 `limit` 请求 → THEN 返回全部命中且响应 `limit` 为 `null`
   - 历史快照降级【业务规则 5】—— WHEN 快照没有全量节点索引 → THEN 降级为保留集并置 `source=legacy`，不报错
   - 非法值被拒【业务规则 6】—— WHEN 传未知分组或不可解析的分页参数 → THEN `400` 与可读消息，不静默忽略
   - 不可查【业务规则 2】—— WHEN 快照不存在或非本人 → THEN `404`「快照不存在」

   > **对应规格**：`device-inspector-layers`（分层查询契约）· `element-layering`（分组与主定位口径）· `device-inspector-page`（分组视图唯一 · 固定 14 行分页 · 双击或单击缩略图才画红框 · 横向滚动与首列冻结 · 元素表列宽集中登记）

2. **测试用例** —— **接口层无专有自动化**；分层端点的守护在灰盒集成层（见下）。

3. **自动化覆盖的测试用例**
   - `tests/graybox/unit/test_element_layers.py` —— 分组判定（仅按类名 / 未知类归「其它」/ 细类）、主定位唯一性与位置型排除、坐标排序、被裁元素保留标记、摘要结构、候选按需生成
   - `tests/graybox/integration/test_inspector_layers_api.py` —— 分层查询端点的分组摘要、筛减、分页、缺省不截断、降级与错误码
   - `frontend/tests/device-inspector/p0/StructureAnalysisPanel.spec.ts` —— 14 行分页（首屏 / 满页 / 末页）
   - `frontend/tests/device-inspector/p0/StructureAnalysisPanel-thumbnail-locate.spec.ts` —— 单击缩略图列定位、单击不放大、空占位同样可点
   - **缺口：** 手机屏幕的 canvas 绘制（分组框 / 悬停 / 选中后滚动）无自动化；点分组筹码后的截图侧表现无断言。

### 保存到元素定位

1. **业务场景**

   **UI交互侧**
   - 勾选为空被拒【校验】—— WHEN 未勾选就点保存 → THEN 提示「请先勾选要保存的数据」，**不发请求**
   - 按勾选筛减【业务逻辑 2】—— WHEN 共 10 行勾 3 行后保存 → THEN 请求只带这 3 行下标，目标页面只新增 / 更新这 3 个元素
   - 必填校验【校验】—— WHEN 已有页面模式没选页面 / 新建模式没填名称 → THEN 字段内联报错，不发请求
   - 内联重命名变别名【业务逻辑 3】—— WHEN 改过「元素名称」再保存 → THEN 别名按 `resource_id` 映射写入元素
   - 保存冲突显示后端原因【业务逻辑 5】—— WHEN 同级重名（409）→ THEN 提示含冲突原因，不是「保存失败」
   - 保存成功提示与刷新【业务逻辑 4】—— WHEN 保存成功 → THEN 提示「已保存 N 个元素（M 个已更新，K 个跳过）」并关弹窗刷新列表
   - 回看态不可保存【业务逻辑 6】—— WHEN 当前是已保存页面回看 → THEN 保存键灰着

   **业务功能侧**
   - 新建页面模式【业务规则 1】—— WHEN 只传 `page_label`（+ `folder_path`）→ THEN 逐层建目录并新建页面，写入元素
   - 已有页面模式【业务规则 1 · 7】—— WHEN 传 `page_id` → THEN 元素 upsert 追加，页面截图 / OCR / `snapshot_id` 仅在为空时补全
   - upsert 口径【业务规则 6】—— WHEN 同 `(page, resource_id, bounds)` 再次保存 → THEN 更新而不是新增，`updated` 计数增加
   - 别名兜底【业务规则 6】—— WHEN 元素无 alias、有 text → THEN 落库 alias 取 text；两者都无则取 resource_id
   - 页面级 OCR 不落库【业务规则 8】—— WHEN 用历史含 OCR 的快照保存 → THEN 目标页面 `ocr_json` 为空
   - 快照不存在【业务规则 2】—— WHEN `id` 不存在或非本人 → THEN `400`「快照不存在」
   - 页面名为空【业务规则 2】—— WHEN 未传 `page_id` 且 `page_label` 为空 → THEN `400`「页面名称不能为空」
   - 无元素数据【业务规则 2】—— WHEN 快照 `dump_json.elements` 为空 → THEN `400`「该快照无元素数据」
   - 同级重名【业务规则 9】—— WHEN 新建页面且同级已存在同名 → THEN `409`「同级页面「{label}」已存在」
   - 写库走白名单【业务规则 5】—— WHEN 保存 → THEN 写库只经 `element_locator.api`，检查器不 import 其内部实现、不直接写 `el_` 表

   > **对应规格**：`device-inspector-page`（勾选驱动的筛减保存）· `api-path-convention`

2. **测试用例** —— 活体用例**已落地**（`tests/api/case/inspector.yaml`）：

   | 编号 | 标题 | 请求 | 期望 |
   |---|---|---|---|
   | TC-INS-006 | 保存到元素定位未登录 | `POST .../save-elements/`（无 token） | `HTTP 401` +「请先登录」|
   | TC-INS-060 | 保存到元素定位快照不存在 | `.../999999999/save-elements/` | `HTTP 400` +「快照不存在」|

   > **未落地**：真正建页面并写入元素（需真机快照或造 `dump_json`）、同级重名 409、目录层级与别名回填。

   **前端单元层**（`frontend/tests/device-inspector/p0/`，P0，4 个文件 / 19 个用例；下表只列与本功能相关的前三条）：

   | 用例 | 覆盖 |
   |---|---|
   | 抓取失败时提示后端返回的原因，而不是通用文案 | 【获取快照 · 业务逻辑 4】+【失败呈现】|
   | 「重试」按失败来源重发请求，并在成功后撤掉错误 | 【失败呈现 · 业务逻辑 2 · 3】|
   | 删除当前展示的快照后，元素分组与选中元素一起复位 | 【删除快照 · 业务逻辑 4】|

3. **自动化覆盖的测试用例**
   - `tests/api/test_inspector.py` —— 鉴权 + 快照不存在的 400 分支
   - `frontend/tests/device-inspector/p0/store.spec.ts` —— store 层的失败原因 / 重试 / 删除复位
   - **缺口：勾选筛减、必填校验、别名回填、409 冲突呈现四条零覆盖；保存弹窗与已保存页面选择器两个组件零覆盖。**

### 已保存页面只读回看

1. **业务场景**

   **UI交互侧**
   - 名称与元信息分行【模版 2】—— WHEN 页面有包名与元素数 → THEN 名称单独一行，下一行是「包名 · 元素 N」
   - 无包名仍分行【模版 2】—— WHEN 页面没有包名 → THEN 下一行以「—」表示包名并带上元素数
   - 点目录不打开【业务逻辑 2】—— WHEN 点目录节点 → THEN 只展开 / 收起，不回看
   - 点页面只读打开【业务逻辑 2 · 3】—— WHEN 点页面 → THEN 以只读方式打开该页，走**同一张结构表**，弹窗关闭
   - 回看态不伪造分组【业务逻辑 4】—— WHEN 打开已保存页面 → THEN 分组列按后端摘要显示、无「指标」列（该入口当前冻结）
   - 空列表提示【模版 3】—— WHEN 元素定位里没有任何页面 → THEN 提示「暂无已保存页面」

   **业务功能侧**
   - 读页面视图【业务规则 3】—— WHEN 带有效令牌请求存在的页面 → THEN `200` 并返回元素定位字段口径（`text_val` / `alias` 等），且**只读**
   - 页面不存在【业务规则 2】—— WHEN 页面 ID 不存在或该节点是目录 → THEN `404`「页面不存在」

   > **对应规格**：`device-inspector-page`（已保存页面选择器按行展示 · 回看用同一张表格）

2. **测试用例** —— 活体用例**已落地**（`tests/api/case/inspector.yaml`）：

   | 编号 | 标题 | 请求 | 期望 |
   |---|---|---|---|
   | TC-INS-007 | 页面只读回看未登录 | `GET /api/inspector/pages/1/`（无 token） | `HTTP 401` +「请先登录」|
   | TC-INS-070 | 页面只读回看不存在 | `GET /api/inspector/pages/999999999/` | `HTTP 404` +「页面不存在」|

   > **未落地**：真实已保存页面的字段映射（`text_val` → `text`）、目录节点 404、以及跨用户归属（见附录第 3 条）。

3. **自动化覆盖的测试用例**
   - `tests/api/test_inspector.py` —— 仅覆盖鉴权与 404
   - **缺口：页面选择器组件与回看态字段映射零覆盖。**

### 删除快照

1. **业务场景**

   **UI交互侧**
   - 二次确认后删除【业务逻辑 1 · 3】—— WHEN 点删除并在确认框点「删除」→ THEN 发起删除请求，成功后提示「快照已删除」并刷新列表
   - 取消不删除【业务逻辑 2】—— WHEN 点「取消」或按 ESC → THEN 不发请求，列表不变
   - 删当前展示的快照后复位【业务逻辑 4】—— WHEN 删的正是当前展示的那份 → THEN 元素表、元素分组、选中元素一起回到空态，工具条计数消失、手机屏幕回空态

   **业务功能侧**
   - 删记录与文件【业务规则 2 · 3】—— WHEN 删除成功 → THEN `di_snapshots` 行删除，截图与缩略图目录尽力清理
   - 清理失败不阻断【业务规则 3】—— WHEN 文件清理抛异常 → THEN 只告警，接口仍返回 `200` 且数据库行已删
   - 只删本人的【业务规则 1】—— WHEN 用他人的快照 ID 删除 → THEN `404`「快照不存在」

   > **对应规格**：`device-inspector-page`（快照删除需二次确认）

2. **测试用例** —— 活体用例**已落地**（`tests/api/case/inspector.yaml`）：

   | 编号 | 标题 | 请求 | 期望 |
   |---|---|---|---|
   | TC-INS-005 | 快照删除未登录 | `DELETE .../snapshots/1/delete/`（无 token） | `HTTP 401` +「请先登录」|
   | TC-INS-050 | 快照删除不存在 | `DELETE .../snapshots/999999999/delete/` | `HTTP 404` +「快照不存在」|

   > **未落地**：真实删除一条快照并核对文件清理（需先有快照，属集成层）。

3. **自动化覆盖的测试用例**
   - `tests/api/test_inspector.py` —— 鉴权与 404
   - `frontend/tests/device-inspector/p0/store.spec.ts` —— 「删除当前展示的快照后，元素分组与选中元素一起复位」（store 层，不发真实请求）
   - **缺口：二次确认框（取消不删、ESC 关闭）与文件清理零覆盖。**

### 跨模块消费：AI 截图

1. **业务场景**

   **业务功能侧**
   - 只截屏不落库【业务规则 2 · 3】—— WHEN AI 工具调 `capture_screen` → THEN 只新增一张截图文件，`di_snapshots` 不新增行、历史快照列表不变
   - 设备校验同源【业务规则 1】—— WHEN 传未注册或缺省 `serial` → THEN 抛与抓取同一套的领域错误
   - 只经白名单【业务规则 4】—— WHEN AI 助手要用截图能力 → THEN 只 import `device_inspector.api`，不 import `service.py`、不直写 `di_` 表

   > **对应规格**：`openspec/specs/ai-screen-vision` · `ai-page-flow-capture`

2. **测试用例** —— **无专有自动化**。

3. **自动化覆盖的测试用例**
   - `tests/graybox/unit/test_ai_api_public_exports.py` —— 属 AI 侧的公开导出对齐（间接覆盖白名单存在性）
   - **缺口：`capture_screen` 的「不落库」与设备校验无直接断言。**

### 失败呈现与重试

1. **业务场景**

   **UI交互侧**
   - 失败取后端原因【业务逻辑 1】—— WHEN 抓取被占用 / 保存冲突 → THEN 提示含后端 `message`，不是通用文案
   - 重试真的重发【业务逻辑 2】—— WHEN 某请求失败后点「重试」→ THEN 重新发起刚刚失败的那一个请求，成功后错误条消失
   - 同源成功清旧错【业务逻辑 3】—— WHEN 同来源的下一次请求成功 → THEN 该来源的旧错误提示被撤掉

   **业务功能侧**
   - 四类来源可重试【业务逻辑 4】—— WHEN 失败来源是设备列表 / 快照列表 / 抓取 / 分层查询之一 → THEN 「重试」路由到对应请求

2. **测试用例** —— 前端单元层**已落地**（`frontend/tests/device-inspector/p0/store.spec.ts`）：见「保存到元素定位」一节的前端单元层表（前两条即本功能用例）。

3. **自动化覆盖的测试用例**
   - `frontend/tests/device-inspector/p0/store.spec.ts` —— 覆盖「捕获后端原因」与「按来源重试」，是模块内论证最完整的一段
   - **缺口：`snapshot`（详情）重试分支未断言；错误条组件本身未测。**

### 怎么跑这些测试

```
python -m pytest tests/api/test_inspector.py -q             # 检查器接口用例（14 条；需后端 :8766 已启动）
python -m pytest tests/graybox/unit -q                      # 灰盒单元层（含 test_element_layers.py · test_inspector_*.py）
python -m pytest tests/graybox/integration -q               # 灰盒集成层（含 test_inspector_layers_api.py 等四个文件）
cd frontend && npx vitest run tests/device-inspector        # 前端检查器 P0（4 个文件 / 19 个用例）
```

> 端到端层（`python -m pytest tests/e2e`）当前只覆盖登录模块，**不含检查器用例**。

---

## 附录：已知缺口

1. **接口文档有两处与代码相反** —— `dev_docs/DEV_TEST/接口文档/API-设备检查器.md` 的 save-elements 错误表写「目录最多嵌套 5 层」（`:380`），而实际执行路径 `apps/element_locator/api_snapshot.py:48` 是 `MAX_DEPTH = 20`、文案也是 20 层（文档里的 5 层来自 `page_tree.MAX_PAGE_TREE_DEPTH`，是元素定位页面树自己的口径）；同一张表还列了「同名节点「{segment}」不是目录」，**全仓代码里不存在这句文案**（目录解析只查 `LocatorDirectory`，不会撞到页面节点）。本 PRD 以**代码**为准。

2. **同一资源的不存在语义有两套状态码** —— 快照详情 / 删除两处在「不存在或非本人」时返回 `404`，而保存端点的同一条件返回 `400`（`apps/device_inspector/api.py:210` 抛 `ValueError`，`views.py:98-99` 统一翻 400）。原因是该分支与「页面名称不能为空」共用 `ValueError` 出口。前端按文案呈现，不受影响；但契约上不一致。

3. **页面回看端点没有归属过滤** —— `api.get_page_view(page_id)` 直接转发 `element_locator.api.get_page_full`，**不带 `created_by` 条件**（`apps/device_inspector/api.py:258-262`）；而快照的五个端点全部按 `created_by` 限定本人。任何已登录用户只要知道（或枚举）`page_id` 就能读到任意元素定位页面的截图路径与元素，属跨用户越权的潜在面。本次只登记，不改动。

4. **`page_id` 非整数会漏出 Python 内部文案** —— `views.py:91` 的 `int(page_id) if page_id else None` 在传字符串（如 `"abc"`）时抛 `ValueError`，被 `views.py:98-99` 捕获后 `str(e)` 直接进 `message`，前端会显示 `invalid literal for int() with base 10: 'abc'`。接口文档要求 `page_id` 为整数字符串，但非法输入没有被翻成产品文案。

5. **OCR 链路只剩后端** —— 后端 `method='ocr'`、`ocr_json` 落库与 `capture_ocr_payload` 完整保留，前端**恒发 `dump`**（`store.ts:172`），界面也不呈现 OCR 计数、OCR 框选与页面级 OCR 落库。历史 `method='ocr'` 的快照仍可打开，但只展示元素链路。后端口径未变是刻意的（规格 `device-inspector-page` 的「检查器只保留 Dump 链路」只约束前端）。

6. **抓取不加设备锁** —— `open_inspector_engine` 只做校验，`open_engine` 明示「不做缓存 / 锁 / 租用」（`engines/device/registry.py:75-82`）。两个用户可同时对同一台在线设备抓取，同屏画面可能互相干扰。这是「不与执行引擎抢设备」之外的空白，本次只登记。

7. **`release_occupy` 的文案与真实归属已漂移** —— 视图与 manager 的 docstring 都写「释放设备检查器占用」（`apps/device_pool/views.py:325`、`manager.py:514`），但检查器抓取全程**只读不写** `occupied_by`；实际占用者是设备管理的观察连接（`occupy_observe`，把 `occupied_by` 设为 `user_id`）。用「释放」键前需知道它解除的不是检查器。

9. **快照详情端点已无前端调用方** —— `GET /api/inspector/snapshots/{id}/` 仍在路由表与接口文档中、并有两条接口用例（未登录 401 / 不存在 404），但前端已改为一律消费分层端点：`store.viewSnapshot` 内部就是 `fetchLayers`（`store.ts:237-241`），`api.ts` 中已无 `apiGetSnapshot`。端点的去留与「已无产品入口的端点如何处理」是产品决定，本次只登记。

10. **「保存到元素定位」前端已冻结，而规格仍按可用描述** —— 前端 `SAVE_TO_ELEMENTS_FROZEN = true`（`store.ts:41`），入口为灰键、点按只提示「元素下标口径已随全量元素展示变更，保存链路待后续变更对齐，暂不可用」；但规格 `device-inspector-page` 的「元素表格勾选驱动保存」等条款仍按链路可用描述（含「勾选 3 行后保存」的场景）。规格与实现在此分歧，本次只登记，不改规格也不改代码。

8. **测试覆盖仍不完整** —— 现存资产：接口 `tests/api/case/inspector.yaml` 14 条；灰盒单元 `test_element_layers.py` / `test_inspector_capture_dump.py` / `test_inspector_ocr_tool.py`；灰盒集成 `test_inspector_layers_api.py` / `test_inspector_snapshot_retention.py` / `test_inspector_snapshot_media.py` / `test_inspector_save_element_aliases.py`；前端 P0 `frontend/tests/device-inspector/p0/` 4 个文件。**空白有三块**：
   1. **手机屏幕的绘制无自动化** —— canvas 上的分组框（实线 / 虚线）、悬停命中、选中后滚动，jsdom 下无法覆盖，只有代码阅读与人工验证。
   2. **组件层只覆盖了元素表** —— 结构面板的分页与缩略图列有断言，但勾选筛减、内联重命名、快照抽屉的删除二次确认之外的交互，以及保存弹窗、已保存页面选择器仍无断言。
   3. **端到端层为 0** —— 端到端套件目前只覆盖登录模块，检查器的骨架常驻、灰键门槛、删除与清空复位、保存筛减都没有真链路守护。
   另需注意：**抓取成功路径本身需要真机**，接口层按约定留给集成测试与真机验证，因此 `capture` 的成功体、占用冲突与失败清理在任何自动化层都还没有守护。
