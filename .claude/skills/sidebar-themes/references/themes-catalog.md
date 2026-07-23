# 侧边栏主题完整属性表

18 套主题的 8 维度详细属性，用于精确选型和混搭。

---

## 第一组：现代玻璃/极简

### A · Prism 暗色指挥中心

| 维度 | 属性 |
|------|------|
| 底色 | `linear-gradient(180deg, rgba(15,23,42,0.92), rgba(20,30,55,0.88))` |
| 边框 | `1px solid rgba(255,255,255,0.08)` |
| 圆角 | `20px` |
| 品牌字体 | gradient chroma-flow 动画（5 色渐变） |
| 分区标签 | 小写灰色 `#64748b`，无装饰 |
| 菜单项 | 圆角 `12px`，hover 白色微透明 |
| 活性指示器 | **左边缘 3px 模块色霓虹条** + `radial-gradient` 光晕 + `box-shadow: 0 0 14px` |
| 签名 | `::before` 霓虹条从 0→0.7→1 opacity，hover 时 spring 弹性 |
| 用户卡片 | `rgba(255,255,255,0.05)` + `1px solid rgba(255,255,255,0.08)` |
| Badge | `rgba(137,207,240,0.2)` 背景，`#BDE0FE` 文字 |
| 字体 | `Quicksand` |

### B · Frost 精炼毛玻璃

| 维度 | 属性 |
|------|------|
| 底色 | `rgba(255,255,255,0.48)` + `backdrop-filter: blur(28px)` |
| 边框 | `1px solid rgba(255,255,255,0.72)`（仅右侧） |
| 圆角 | `20px` |
| 品牌字体 | gradient chroma-flow（4 色） |
| 分区标签 | `#9a8c98`，无装饰 |
| 菜单项 | 圆角 `12px`，hover `rgba(255,255,255,0.7)` |
| 活性指示器 | **浮动白色玻璃药丸** + 左侧 6px 彩色圆点 + `box-shadow` 四层 |
| 签名 | 活性项 `::after` 圆点呼吸发光 |
| 用户卡片 | `rgba(255,255,255,0.45)` |
| Badge | 渐变蓝紫 `rgba(137,207,240,0.3)` |
| 字体 | `Quicksand` |

### C · Silk 极简实体

| 维度 | 属性 |
|------|------|
| 底色 | `linear-gradient(180deg, #fdfdfc, #f8f7f5)` |
| 边框 | 无边框，`1px shadow` 模拟分割 |
| 圆角 | `20px` |
| 品牌字体 | 纯黑 `#1e293b`，无渐变 |
| 分区标签 | `#94a3b8`，无装饰 |
| 菜单项 | 圆角 `12px`，hover `#f1f5f9` |
| 活性指示器 | **模块色浅底**（`color-mix 12%`）+ 加粗文字 |
| 签名 | `::before` 全高 3px 八色渐变左边缘条纹 |
| 用户卡片 | `#f8fafc` + `1px #e8ecf1` |
| Badge | `#f1f5f9` 背景 |
| 字体 | `Quicksand` |

### D · Terminal 开发者工具

| 维度 | 属性 |
|------|------|
| 底色 | `#1a1d23` |
| 边框 | `1px shadow` |
| 圆角 | `20px` |
| 品牌字体 | `Inter` sans-serif，14px，英文标题 |
| 分区标签 | `JetBrains Mono`，`#484f58`，`// ` 前缀 |
| 菜单项 | 圆角 `6px`，高 36px，hover `#252830` |
| 活性指示器 | **左边缘 2px 模块色** + 右侧闪烁光标 `::after` |
| 签名 | 光标 `animation: terminal-cursor 1.2s steps(1) infinite` |
| 用户卡片 | `#252830` + `1px #30363d` |
| Badge | `JetBrains Mono`，`#252830` 背景 |
| 字体 | `Inter` + `JetBrains Mono` |

### E · Bloom 有机生长

| 维度 | 属性 |
|------|------|
| 底色 | `linear-gradient(rgba(255,252,248,0.7), rgba(248,245,240,0.6))` + `blur(16px)` |
| 边框 | `1px solid rgba(180,160,130,0.18)` |
| 圆角 | `20px` |
| 品牌字体 | `#5a4e3c`，暖棕 |
| 分区标签 | `#b8a088`，10px |
| 菜单项 | 圆角 `14px`，高 44px，hover 暖米色 |
| 活性指示器 | **图标 scale(1.18) 弹性放大** + 左侧 8px 彩色圆点脉冲 |
| 签名 | 圆点 `box-shadow` 呼吸：`0 0 8px` ↔ `0 0 20px`，2.8s |
| 用户卡片 | `rgba(255,252,248,0.55)` + `0.5px border` |
| Badge | `rgba(180,160,130,0.16)` |
| 字体 | `Quicksand` |

### F · Grid 瑞士国际风

| 维度 | 属性 |
|------|------|
| 底色 | `#ffffff` |
| 边框 | `1px solid #e8ecf1`（shadow 模拟） |
| 圆角 | `0` |
| 品牌字体 | `#0f1419`，`Inter` sans-serif，700 weight |
| 分区标签 | `Inter` 11px，`#536471`，上边界 1px 细线 |
| 菜单项 | 圆角 `4px`，高 38px，hover `#f7f9f9` |
| 活性指示器 | **黑底白字纯色块**（Swiss 招贴），`#0f1419` 背景 |
| 签名 | 无装饰，纯对比反色 |
| 用户卡片 | `#fafbfc` + `1px #e8ecf1` |
| Badge | `#f0f3f5` 背景 |
| 字体 | `Inter` |

---

## 第二组：手绘混合

### G · Crayon 蜡笔涂色

| 维度 | 属性 |
|------|------|
| 底色 | `#fffef9` |
| 边框 | **3px solid #2d2d2d** + `3px 3px 0 0 #2d2d2d` 偏移阴影 |
| 圆角 | `18px 22px 16px 20px`（不规则） |
| 品牌字体 | `Caveat` cursive，20px，#2d2d2d |
| 分区标签 | **蜡笔色块**：`#FFE066` 底 + 2.5px 黑框 + `rotate(-0.8deg)` + 偏移红阴影 |
| 菜单项 | 圆角 `10px 16px 12px 14px`，hover 边框出现 |
| 活性指示器 | **整行填色**（`#FFEBEB`）+ 2.5px 黑框 + `box-shadow: 3px 3px 0 0 #2d2d2d` |
| 签名 | 弹跳动画 `crayon-pop`：`scale(0.96)→scale(1)`，spring easing |
| 用户卡片 | `#fff` + 2.5px 黑框 + 偏移阴影 |
| Badge | 粗框色块 + 偏移黑阴影 |
| 字体 | `Caveat`（品牌/标签）+ `Quicksand`（菜单） |

### H · Notepad 手账笔记

| 维度 | 属性 |
|------|------|
| 底色 | `radial-gradient(circle, #d4cdc0 1px, transparent 1px)` 点阵 + `#fefcf6` |
| 边框 | `2px solid #d4cdc0` |
| 圆角 | `6px` |
| 品牌字体 | `Reenie Beanie` cursive，19px，`rotate(-0.5deg)` |
| 分区标签 | **和纸胶带条**：渐变底 + `rotate(-1deg)` + `width: calc(100%+8px)` 超宽 |
| 菜单项 | 圆角 `4px`，左侧 3px 透明边框 |
| 活性指示器 | **左侧彩色便签标签**（4px 宽）+ 右侧阴影卡片 |
| 签名 | Badge `::before` 伪元素折角（旋转 45° 三角形） |
| 用户卡片 | 信纸横线背景（`repeating-linear-gradient`） |
| Badge | 便签纸折角 `::before` 伪元素 |
| 字体 | `Reenie Beanie`（标签）+ `Patrick Hand`（状态）+ `Quicksand`（菜单） |

### I · Doodle 白板涂鸦

| 维度 | 属性 |
|------|------|
| 底色 | `#fffeff` |
| 边框 | **3.5px solid #1a1a2e** + `4px 4px 0 0 #1a1a2e` |
| 圆角 | `8px` |
| 品牌字体 | `Caveat` cursive，20px，SVG 波浪下划线 |
| 分区标签 | **荧光笔涂抹**：`::before` 伪元素 55% 高度彩色底色 + `rotate(-0.5deg)` |
| 菜单项 | 圆角 `4px`，hover `#fafafa` |
| 活性指示器 | **荧光笔扫过**（`linear-gradient` 55%-80% 彩色）+ 右侧 ★ 旋转闪烁 |
| 签名 | ★ 动画 `doodle-twinkle`：`rotate(0)→rotate(20deg)` + `scale(1)→scale(1.3)` |
| 用户卡片 | `#fff` + 3px 黑框 + 偏移阴影 |
| Badge | 粗框白底 + 偏移黑阴影 |
| 字体 | `Caveat`（品牌/标签）+ `Quicksand`（菜单） |

### J · Chalkboard 黑板粉笔

| 维度 | 属性 |
|------|------|
| 底色 | `#2f3e44` + 木纹边框 `6px solid #8b7b65` + 噪点 SVG 叠层 |
| 边框 | 木纹画框：`outline: 3px solid #a09070` + `outline-offset: 2px` |
| 圆角 | `4px` |
| 品牌字体 | `Caveat` cursive，20px，`#FFE066` 粉笔色 + `text-shadow` 辉光 |
| 分区标签 | `Caveat`，`#A5F0C5` 绿色粉笔 + `text-shadow` + 下划线辉光 |
| 菜单项 | 圆角 `6px`，hover `rgba(255,255,255,0.06)` |
| 活性指示器 | **彩色粉笔块**（`var(--item-color)` 底色）+ 模糊外晕 + `inset` 高光 |
| 签名 | `::after` 模糊粉末散落（`filter: blur(5px)`） |
| 用户卡片 | `rgba(255,255,255,0.05)` + `1px rgba(255,255,255,0.1)` |
| Badge | `rgba(255,255,255,0.1)` 半透背景 |
| 字体 | `Caveat`（品牌/标签）+ `Quicksand`（菜单） |

### K · Watercolor 水彩晕染

| 维度 | 属性 |
|------|------|
| 底色 | 三色 `radial-gradient` 湿笔触渗透 + `#fefdfb` |
| 边框 | `2px solid #ddd8d0` |
| 圆角 | `8px` |
| 品牌字体 | `Reenie Beanie` cursive，19px |
| 分区标签 | `Reenie Beanie`，`#8a7b6e`，毛笔质感 |
| 菜单项 | 圆角 `6px`，hover 暖米色 |
| 活性指示器 | **双层 radial-gradient 水彩团** + 不规则圆角 `8px 14px 10px 12px` |
| 签名 | `::before` 右下角水滴形状（`border-radius: 50% 40% 50% 45%`） |
| 用户卡片 | `rgba(255,255,255,0.6)` + `1px #e8e0d5` |
| Badge | `rgba(200,180,150,0.12)` 半透背景 |
| 字体 | `Reenie Beanie`（标签）+ `Quicksand`（菜单） |

### L · Comic 漫画波普

| 维度 | 属性 |
|------|------|
| 底色 | **Ben-Day 网点**：`radial-gradient(circle, #FFE066 1.5px, transparent 1.5px)` 12px 间距 |
| 边框 | **4px solid #111** + `6px 6px 0 0 #111` 偏移 |
| 圆角 | `8px` |
| 品牌字体 | `Bangers` display，18px，`#111` |
| 分区标签 | **斜切标题框**：`clip-path: polygon(0% 0%, 100% 0%, 95% 100%, 0% 100%)`，黑底白字 |
| 菜单项 | 圆角 `4px`，字体 `Gochi Hand` |
| 活性指示器 | **对话气泡**：`border-radius: 8px 16px 12px 12px` + 左侧 CSS 三角（`::before` 黑 + `::after` 白） |
| 签名 | 品牌区 `::after` 爆裂星形 `clip-path` polygon |
| 用户卡片 | `#fff` + 3px 黑框 + 偏移阴影 |
| Badge | `Bangers` 字体，`#FF6B6B` 红底，字母间距 |
| 字体 | `Bangers`（品牌/badge）+ `Gochi Hand`（菜单）+ `Quicksand`（回退） |

---

## 第三组：五元素融合

### M · Neural Sketch 神经手稿

| 维度 | 属性 |
|------|------|
| 底色 | `radial-gradient(circle, rgba(137,207,240,0.06) 1px, transparent 1px)` 18px 点阵 + `#fdfdfc` |
| 边框 | `1.5px solid #e0e4e8` |
| 圆角 | `16px` |
| 手绘 | 品牌 `::after` 手写 `⬡ ⬡ ⬡` 节点 |
| 几何 | 点阵网格 + 六边形节点 |
| AI | SVG 神经网络连线装饰（虚线连接圆点） |
| 科技 | 活性项 `::after` 突触脉冲动画（`scale` + `opacity`） |
| 商务 | 白底 + `#e0e4e8` 细线 + 克制动效 |
| 分区标签 | `JetBrains Mono`，`#a0aec0`，左侧 2px `#89CFF0` 竖线 |
| 活性指示器 | 左侧 10px 双层圆点（白 + 蓝脉冲） |
| 字体 | `Quicksand` + `JetBrains Mono` |

### N · Cyber Blueprint 赛博蓝图

| 维度 | 属性 |
|------|------|
| 底色 | `#0f1d2e` + 16px 工程网格（`linear-gradient` 十字线） |
| 边框 | `2px solid #1e3a5f` + 多层辉光阴影 |
| 圆角 | `16px` |
| 手绘 | 品牌 `::after` Caveat 手写 `← v2.0.4` 版本标注 |
| 几何 | 16px 蓝图网格 + `::after` 标尺线 |
| AI | 活性项 `::before` 蓝光节点 `box-shadow` 脉冲 |
| 科技 | 霓虹蓝 `#64c8ff` + `filter: drop-shadow` |
| 商务 | `Orbitron`/`JetBrains Mono` 等宽科技字体 |
| 分区标签 | `JetBrains Mono` 9px，`text-shadow` 辉光 |
| 活性指示器 | 左侧 4px 蓝光圆点 + 1px 竖线 + `linear-gradient` 微底 |
| 字体 | `Orbitron` + `JetBrains Mono` + `Caveat` |

### O · Crystal Prism 水晶棱镜

| 维度 | 属性 |
|------|------|
| 底色 | `#fdfdfc` + 交叉菱形线几何纹理 |
| 边框 | `1.5px solid #e8ecf1` |
| 圆角 | `16px` |
| 几何 | `background-size: 24px` 交叉线网格 |
| AI | 品牌区 5 色棱镜色散装饰线（`linear-gradient` 彩虹） |
| 科技 | 品牌图标 `clip-path: polygon` 六边形 + 活性项菱形指示器 |
| 商务 | 极简白 + 细灰线 + Inter 字体 |
| 分区标签 | `Inter` 10px，前缀短线（`::before` 12px 渐变横线） |
| 活性指示器 | 左侧 6px 菱形（`clip-path`）+ 渐变背景 + `inset` 高光 |
| 字体 | `Inter` + `Quicksand` |

### P · Data Flow 数据流线

| 维度 | 属性 |
|------|------|
| 底色 | `#0d1117` + 双 `radial-gradient` 椭圆光晕 |
| 边框 | `1px solid rgba(255,255,255,0.06)` + 多层深阴影 |
| 圆角 | `16px` |
| 几何 | `::before` 贝塞尔流线（`linear-gradient` 竖线 + 圆点装饰） |
| AI | 活性项 `::before` 数据粒子汇聚脉冲（`height` + `opacity` 变化） |
| 科技 | 品牌 `::after` 数据粒子 `• • •` + `box-shadow` 辉光 |
| 商务 | 暗色专业 + `JetBrains Mono` 等宽字体 |
| 分区标签 | `JetBrains Mono` 9px，`rgba(100,200,255,0.45)` |
| 活性指示器 | 左侧 1px 流线 + `linear-gradient(90deg)` 渐变底 |
| 字体 | `JetBrains Mono` + `Inter` |

### Q · Origami Tech 折纸科技

| 维度 | 属性 |
|------|------|
| 底色 | `linear-gradient(180deg, #fdfdfc, #f8f9fb)` |
| 边框 | `1.5px solid #e8ecf1` |
| 圆角 | `16px` |
| 几何 | 活性项 `clip-path` 切角（右上角 10px 缺角） |
| AI | 活性项 `::after` 旋转 45° 菱形 Core + 蓝底 |
| 科技 | 品牌图标 `clip-path` 五边形 + 分区 `::after` 折线 |
| 商务 | 纯黑白极简 + `Inter` 字体 + 克制动效 |
| 分区标签 | `Inter` 10px，`::after` 渐隐折线 |
| 活性指示器 | `clip-path` 切角 + 黑色边框 + 菱形 Core |
| 字体 | `Inter` |

### R · Constellation AI 星座智能

| 维度 | 属性 |
|------|------|
| 底色 | 多层 `radial-gradient` 星光 + `linear-gradient` 深空 `#0a0e17→#111827→#0d1520` |
| 边框 | `1px solid rgba(255,255,255,0.06)` + 多层深阴影 |
| 圆角 | `16px` |
| 手绘 | `Caveat` 手写分区标签 |
| 几何 | SVG 星座连线（竖线 + 圆点节点） |
| AI | 活性项 `::before` 星点辉光 `box-shadow` 脉冲（`0 0 4px` ↔ `0 0 24px`） |
| 科技 | 品牌图标 `text-shadow` 辉光 + `filter: drop-shadow` |
| 商务 | 暗色 + 星点克制 + `Quicksand`  |
| 分区标签 | `Caveat` cursive，14px，`rgba(137,207,240,0.5)` |
| 活性指示器 | `radial-gradient` 光晕底 + 左侧 4px 白色星点 |
| 字体 | `Caveat` + `Quicksand` |
