---
name: device-page-analysis
description: |
  设备页面元素分层分析 — 采集当前手机页面（截图 + UI XML dump），把全部 UI 元素按两级结构分组（L1：布局容器 / 滚动·集合容器 / 内容控件 / 其它；L2：内容控件再拆 文本 / 图标 / 其它），为每个分组生成一张圈选图（实线=平台保留、虚线=被裁、角标=元素 index），并输出带 ECharts 图表的自包含 HTML 分析报告（内嵌压缩预览图）。
  需要回答「这一页有多少元素 / 谁能稳定定位 / 图标能不能定位 / 点哪里」这类问题时使用；只要提到「页面分析、元素分层、圈选图、元素定位数据、UI 元素统计、页面元素报告、dump 分析、快照元素分析」就该使用本 skill，即使没明说「分层」。
  Keywords: 页面分析, 元素分析, 元素分层, 圈选图, UI 元素, 元素定位, 定位数据, 页面元素报告, dump 分析, 快照分析, 元素统计, 图标定位, overlay, element analysis, page report, ECharts, uiautomator dump
  Trigger: 用户要求分析某个手机页面/设备页面/详情页的元素构成，或要「元素分层」「圈选图」「各分组有多少元素」「元素定位数据」「页面元素报告」时。
---

# 设备页面元素分层分析

**目的**: 一次采集，把手机当前页面的全部 UI 元素按两级结构分组，产出**每组一张圈选图**与**一份自包含 HTML 分析报告**，用于回答元素构成、定位质量、交互落点这三类问题。

**能力模型**: 采集(Capture) → 分层(Layer) → 配图(Render) → 报告(Report)

## 一、两级分组口径

| 层级 | 分组 | 判据 |
|------|------|------|
| L1 | 布局容器 | 类名属于布局容器集合（FrameLayout / LinearLayout / RelativeLayout / ViewGroup / ConstraintLayout …） |
| L1 | 滚动·集合容器 | 类名属于滚动集合集合（RecyclerView / ListView / GridView / ScrollView / ViewPager …） |
| L1 | 内容控件 | 文本类 / 图形类 / 裸 View |
| L1 | 其它 | 不在以上任何集合内 —— **不猜**，单列一类 |
| L2 | 文本 | 文本类控件且 text 非空且非私用区字符（空文本也归此组） |
| L2 | 图标 | ImageView / ImageButton；或文本类但 text 是私用区码点（图标字体） |
| L2 | 其它 | 裸 View（可点热区 / 分隔线 / 色块 / 占位） |

完整类名集合、7 个细类定义与判定阈值见 `references/rules.md`。

## 二、脚本（本 skill 自带，不放别处）

| 脚本 | 作用 | 用法 |
|------|------|------|
| `scripts/capture_page.py` | 采当前页面：截图 + UI XML + manifest；目录名 `<workdir>/overlay_<包名>_<Activity>_n<元素数>`，同名且内容不同自动加 `_v2` 后缀 | `python scripts/capture_page.py [--serial S] [--workdir DIR]` |
| `scripts/build_layers.py` | 两级分组 + 每叶子一张圈选图 + `two_level_elements.json` | `python scripts/build_layers.py <页面目录>` |
| `scripts/make_report_html.py` | 压缩预览图（宽 380 JPEG）+ ECharts 自包含 HTML 报告 | `python scripts/make_report_html.py --dir <页面目录> --out <报告路径> --title-file <标题文件>` |
| `scripts/check_vendor.py` | 内联算法副本与平台来源文件的摘要对拍（防漂移；平台树不存在时跳过） | `python scripts/check_vendor.py` |
| `scripts/run_all.py` | 三步一条命令跑完 | `python scripts/run_all.py --out <报告路径> --title-file <标题文件>` |

**独立性**：脚本不使用平台任何模块（无 Django、无 `apps/`、无 `engines/`、无 `algorithms/`），只用 `adb` + `uiautomator2` + `Pillow` + 标准库；因此可从任意工作目录、在未初始化平台的环境下执行。

**内联算法副本**：解析与候选生成来自 `scripts/vendor/`（`hierarchy.py` / `xpath.py`），是从平台算法层一次性内联的副本，文件头记录了来源路径与来源文件摘要。副本与平台各自独立演进：平台侧改了算法，本副本**不会自动跟随**；需要同步时按来源文件重新覆盖并更新摘要。

**临时产物**：默认写进项目根下的 `temps/`（找不到项目根则落当前目录的 `temps/`），不写进 skill 目录。

### 中文标题的编码坑

Windows 控制台传中文参数有编码风险。**推荐把标题写进一个 UTF-8 文本文件再传 `--title-file`**；`--title` 仅在确认终端编码正常时使用。

## 三、标准执行顺序

```bash
# 1) 确认设备在线（skill 不负责连接设备，用平台既有命令）
python run.py status

# 2) 采集当前页面 → 输出页面目录
python <skill>/scripts/capture_page.py --serial <SERIAL>

# 3) 分层 + 圈选图 → 页面目录内
python <skill>/scripts/build_layers.py <页面目录>

# 4) 报告 → 按项目根 AGENTS.md 的文档位置约定放置
python <skill>/scripts/make_report_html.py --dir <页面目录> --out <报告路径> --title-file <标题文件>
```

一条命令版本：`python <skill>/scripts/run_all.py --out <报告路径> --title-file <标题文件>`

**报告输出位置不由本 skill 决定** —— 按项目根 `AGENTS.md` 的文档位置约定放置；`--out` 未给时默认落在页面目录内的 `report.html`。

## 四、圈选图约定

- **一叶子一张图**，不合成（合成后难以逐个分析）。
- 半透明填充 + 边框 = 该组元素范围；每组一个颜色（布局=青、滚动=橙、文本=紫、图标=蓝、其它=粉）。
- **实线** = 平台会写进快照；**虚线** = 被平台展示裁剪丢弃（`pure_container` / `bounds_dedup`）。
- **角标数字** = 该元素的 XML `index` 属性（父节点内的第几个孩子）。
- 图脚两行：层级路径 + 数量 + 保留数；细分计数 + 图例。
- 截图与 dump 在**同一次连接内**取得（先截图后 dump），保证框与画面严格对齐。

## 五、报告包含

1. 总览统计卡（元素总数 / 分组数 / 平台保留 / 稳定主定位 / 可点击）
2. ECharts：旭日图（L1→L2 层级与数量）、分组柱状图（总数 / 保留 / 稳定定位）、环形饼图（占比）、细类横向条形图
3. 五组数据表
4. 逐组卡片：**压缩预览图** + 定位说明 + 典型角色 + 关键数字 + 保留/被裁占比 + 类名与细类分布 + 「图上看什么 / 注意」
5. L2 判定依据表（7 细类 → 3 分组）
6. 口径与局限

图片以**压缩预览**内联（宽 380 JPEG，约为原图 4%~6%），报告自包含、可离线打开（ECharts 走 CDN，无网络时回落到常驻数据表）。

## 六、必须随报告一起说明的三件事

1. **主定位是分析口径，不是平台现状**：脚本用「先筛 `count==1` 且非位置型候选，再按 resource-id > content-desc > combined > text > class 排序」选主定位；平台当前没有这个字段。
2. **保留/被裁只影响写库的展示集合**，不代表元素不存在。
3. **单页单次采样**：计数随页面状态变化；换页必须重跑，不要跨页面复用数字。

## 七、自检清单（出报告前）

- [ ] 采集到的 `package` / `activity` 与用户说的页面一致（页面可能已被切走）
- [ ] 五个分组计数之和 = 元素总数；内容控件 = 文本 + 图标 + 其它
- [ ] 每张图都能打开，且框与画面贴合（若错位说明截图与 dump 不同源）
- [ ] 报告内联图片数量 = 非空叶子数
- [ ] 报告 HTML 标签平衡、内联脚本语法通过（`node --check`）
- [ ] 未覆盖已有报告文件（`--out` 指向新路径）