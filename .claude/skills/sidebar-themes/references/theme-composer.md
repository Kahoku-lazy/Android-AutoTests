# 主题混搭引擎

将侧边栏设计分解为 6 个独立维度，每个维度可从不同主题中选取，自由组合。

---

## 6 维度组件矩阵

### 维度 1：底色 (Background)

| 代码 | 名称 | CSS 片段 | 来源 |
|:--:|------|---------|:--:|
| BG1 | 暗海軍蓝玻璃 | `linear-gradient(180deg, rgba(15,23,42,0.92), rgba(20,30,55,0.88))` + `blur(30px)` | A |
| BG2 | 白玻璃 | `rgba(255,255,255,0.48)` + `blur(28px)` | B |
| BG3 | 暖白实体 | `linear-gradient(180deg, #fdfdfc, #f8f7f5)` | C |
| BG4 | 深灰 | `#1a1d23` | D |
| BG5 | 暖米玻璃 | `rgba(255,252,248,0.7)` + `blur(16px)` | E |
| BG6 | 纯白 | `#ffffff` | F |
| BG7 | 蜡笔米白 | `#fffef9` | G |
| BG8 | 点阵纸 | `radial-gradient(circle, #d4cdc0 1px, transparent 1px)` + `#fefcf6` | H |
| BG9 | 白板白 | `#fffeff` | I |
| BG10 | 黑板绿灰 | `#2f3e44` + 木纹边框 | J |
| BG11 | 水彩渗透 | 三色 `radial-gradient` 湿笔触 + `#fefdfb` | K |
| BG12 | Ben-Day 网点 | `radial-gradient(circle, #FFE066 1.5px, transparent 1.5px)` 12px | L |
| BG13 | 神经点阵 | `radial-gradient(circle, rgba(137,207,240,0.06) 1px, transparent 1px)` 18px | M |
| BG14 | 蓝图暗蓝 | `#0f1d2e` + 16px 工程网格 | N |
| BG15 | 水晶交错 | `#fdfdfc` + 24px 菱形交叉线 | O |
| BG16 | 数据深空 | `#0d1117` + 双椭圆光晕 | P |
| BG17 | 折纸白 | `linear-gradient(180deg, #fdfdfc, #f8f9fb)` | Q |
| BG18 | 星座深空 | 多层星光 + `#0a0e17` | R |

### 维度 2：轮廓/边框 (Border)

| 代码 | 名称 | CSS 片段 | 来源 |
|:--:|------|---------|:--:|
| BR1 | 细光边框 | `1px solid rgba(255,255,255,0.08)` + `box-shadow` 辉光 | A |
| BR2 | 玻璃单边 | `border-right: 1px solid rgba(255,255,255,0.72)` | B |
| BR3 | 阴影分割 | `box-shadow: 0 0 0 1px rgba(0,0,0,0.04)` | C |
| BR4 | 极简阴影 | `box-shadow: 8px 0 32px rgba(0,0,0,0.3)` | D |
| BR5 | 暖色半透 | `border-right: 1px solid rgba(180,160,130,0.18)` | E |
| BR6 | 细线分割 | `box-shadow: 1px 0 0 0 #e8ecf1` | F |
| BR7 | 粗黑+偏移 | `3px solid #2d2d2d` + `3px 3px 0 0 #2d2d2d` | G |
| BR8 | 淡棕细线 | `2px solid #d4cdc0` | H |
| BR9 | 极粗黑+偏移 | `3.5px solid #1a1a2e` + `4px 4px 0 0 #1a1a2e` | I |
| BR10 | 木纹画框 | `6px solid #8b7b65` + `outline: 3px solid #a09070` | J |
| BR11 | 淡纸纹 | `2px solid #ddd8d0` | K |
| BR12 | 粗黑双层 | `4px solid #111` + `6px 6px 0 0 #111` | L |
| BR13 | 细灰 | `1.5px solid #e0e4e8` + `box-shadow` | M |
| BR14 | 蓝图双层 | `2px solid #1e3a5f` + 多层辉光 | N |
| BR15 | 水晶细线 | `1.5px solid #e8ecf1` | O |
| BR16 | 暗色微边 | `1px solid rgba(255,255,255,0.06)` + 深阴影 | P |
| BR17 | 折纸细线 | `1.5px solid #e8ecf1` | Q |
| BR18 | 深空微边 | `1px solid rgba(255,255,255,0.06)` + 深阴影 | R |

### 维度 3：分区标签 (Section Label)

| 代码 | 名称 | 视觉 | 来源 |
|:--:|------|------|:--:|
| SL1 | 低调灰 | 小写，`#64748b`，无装饰 | A |
| SL2 | 中灰 | `#9a8c98`，无装饰 | B |
| SL3 | 浅灰 | `#94a3b8`，无装饰 | C |
| SL4 | Mono 注释 | `JetBrains Mono`，`// ` 前缀，`#484f58` | D |
| SL5 | 暖棕细字 | `#b8a088`，10px | E |
| SL6 | Inter 细线 | `Inter` 11px，上边界 1px `#f0f3f5` | F |
| SL7 | 蜡笔色块 | `Caveat` 16px，`#FFE066` 底 + 2.5px 黑框 + `rotate(-0.8deg)` + 红阴影 | G |
| SL8 | 和纸胶带 | `Reenie Beanie` 15px，渐变底 + `rotate(-1deg)` + 超宽 | H |
| SL9 | 荧光笔底 | `Caveat` 18px，`::before` 55% 彩色底 + `rotate(-0.5deg)` | I |
| SL10 | 粉笔下划线 | `Caveat` 16px，`#A5F0C5` + `text-shadow` + `::after` 辉光下划线 | J |
| SL11 | 毛笔手写 | `Reenie Beanie` 17px，`#8a7b6e` | K |
| SL12 | 漫画标题框 | `Bangers` 16px，黑底白字，`clip-path` 斜切 | L |
| SL13 | Mono 竖线 | `JetBrains Mono` 10px，左侧 2px `#89CFF0` 竖线 | M |
| SL14 | Mono 辉光 | `JetBrains Mono` 9px，`text-shadow` 蓝光辉光 | N |
| SL15 | Inter 短横线 | `Inter` 10px，`::before` 12px 渐变横线 | O |
| SL16 | Mono 暗蓝 | `JetBrains Mono` 9px，`rgba(100,200,255,0.45)` | P |
| SL17 | Inter 折线 | `Inter` 10px，`::after` 渐隐折线 | Q |
| SL18 | Caveat 手写 | `Caveat` 14px，`rgba(137,207,240,0.5)` | R |

### 维度 4：活性指示器 (Active Indicator)

| 代码 | 名称 | 机制 | 来源 |
|:--:|------|------|:--:|
| AI1 | 霓虹光条 | 左边缘 3px 模块色 + `box-shadow` 辉光 + `radial-gradient` 光晕 | A |
| AI2 | 玻璃药丸 | 浮动白色卡片 + 左 6px 彩色圆点 + 四层 `box-shadow` | B |
| AI3 | 色底加粗 | `color-mix 12%` 模块色底 + 加粗 + `inset` 边框 | C |
| AI4 | 光标闪烁 | 左 2px 模块色 + 右 `::after` 闪烁光标（`steps(1)` 硬切） | D |
| AI5 | 图标放大 | `scale(1.18)` 弹性放大 + 左 8px 圆点呼吸脉冲 | E |
| AI6 | 黑底反白 | `#0f1419` 纯色底 + 白色文字，无装饰 | F |
| AI7 | 填色弹跳 | 全行 `#FFEBEB` 填色 + 2.5px 黑框 + 偏移阴影 + spring 弹跳 | G |
| AI8 | 便签标签 | 左 4px 模块色竖条 + `::after` 双层色条 + 阴影卡片 | H |
| AI9 | 荧光笔扫 | `linear-gradient` 55%-80% 模块色底 + 右 ★ 旋转闪烁 | I |
| AI10 | 粉笔块辉光 | 模块色块 + `box-shadow` 外晕 + `inset` 高光 + `::after` 模糊粉末 | J |
| AI11 | 水彩晕团 | 双层 `radial-gradient` 湿笔触 + 不规则圆角 + `::before` 水滴 | K |
| AI12 | 对话气泡 | `border-radius` 不规则 + `::before`/`::after` 双层 CSS 三角 | L |
| AI13 | 神经突触 | 左 10px 双层圆点（白 + `::after` 蓝脉冲 `scale` + `opacity`） | M |
| AI14 | 蓝光节点 | 左 4px 蓝光圆点 `box-shadow` 脉冲 + 竖线 + 微底 | N |
| AI15 | 菱形折射 | 左 6px `clip-path` 菱形 + `linear-gradient` 底 + `inset` 高光 | O |
| AI16 | 粒子汇聚 | 左 1px 流线 `opacity`/`height` 脉动 + `linear-gradient` 渐变底 | P |
| AI17 | 折角切面 | `clip-path` 切角 + 黑框 + `::after` 旋转菱形 Core | Q |
| AI18 | 星点辉光 | `radial-gradient` 光晕底 + 左 4px 白星 `box-shadow` 呼吸 | R |

### 维度 5：字体 (Typography)

| 代码 | 品牌/标签字体 | 菜单字体 | 来源 |
|:--:|-------------|---------|:--:|
| T1 | Quicksand（chroma-flow gradient） | Quicksand 600 | A,B |
| T2 | Quicksand（纯色） | Quicksand 600 | C |
| T3 | Inter + JetBrains Mono | Inter 500 | D |
| T4 | Quicksand（纯色） | Quicksand 600 | E |
| T5 | Inter（纯黑） | Inter 500 | F |
| T6 | Caveat cursive | Quicksand 600 | G,I,J,L |
| T7 | Reenie Beanie cursive | Quicksand 600 | H,K |
| T8 | Orbitron + Caveat + JetBrains Mono | Quicksand 600 | M,N,P,R |
| T9 | Inter（纯黑） | Inter 600 | O,Q |

### 维度 6：装饰元素 (Decorative)

| 代码 | 元素 | 来源 |
|:--:|------|:--:|
| DE1 | chroma-flow 品牌 gradient 动画 | A,B |
| DE2 | 全高八色渐变左条纹（`::before` 3px） | C |
| DE3 | 闪烁光标 + `//` 注释前缀 | D |
| DE4 | 图标弹性放大 + 圆点呼吸 | E |
| DE5 | 1px 细线上边界分割 | F |
| DE6 | 不规则圆角 + 偏移黑阴影 + Badge 粗框 | G |
| DE7 | 点阵纸底 + 折角 Badge + 信纸横线 | H |
| DE8 | SVG 波浪下划线 + ★ 闪烁 + 荧光笔底 | I |
| DE9 | 木纹画框 + 粉笔噪点 + 粉末散落 | J |
| DE10 | 三色水彩渗透底 + 水滴形状 | K |
| DE11 | Ben-Day 网点 + 爆裂星形 + 对话气泡三角 | L |
| DE12 | SVG 神经网络连线 + 突触脉冲 | M |
| DE13 | 蓝图网格 + 手写版本标注 + 标尺线 | N |
| DE14 | 交叉菱形纹理 + 棱镜色散 5 色线 | O |
| DE15 | 贝塞尔流线 + 数据粒子 `• • •` | P |
| DE16 | `clip-path` 五边形/切角 + 几何折线 | Q |
| DE17 | 多层星光 + SVG 星座连线 + 星点辉光 | R |

---

## 混搭示例

### 示例 1：「严肃中的俏皮」
```
BG6 (纯白) + BR6 (细线) + SL6 (Inter细线) + AI7 (填色弹跳) + T5 (Inter) + DE7 (点阵/折角)
→ F 的瑞士骨架 + G 的蜡笔活性 + H 的装饰 = 严肃但有趣的商务工具
```

### 示例 2：「暗色 AI 实验室」
```
BG16 (数据深空) + BR16 (暗色微边) + SL14 (Mono辉光) + AI18 (星点辉光) + T8 (Mono+Orbitron) + DE17 (星座连线)
→ P 的暗底 + R 的星座装饰 + N 的蓝图网格 = 沉浸式 AI 工具
```

### 示例 3：「温暖手绘工作台」
```
BG5 (暖米玻璃) + BR5 (暖色半透) + SL8 (和纸胶带) + AI5 (图标放大) + T7 (Reenie Beanie) + DE7 (点阵/折角)
→ E 的底色 + H 的胶带 + E 的活性 = 温和小众创意工具
```

### 示例 4：「极简科技白」
```
BG17 (折纸白) + BR15 (水晶细线) + SL17 (折线) + AI15 (菱形折射) + T9 (Inter) + DE16 (clip-path切角)
→ Q 的折纸 + O 的水晶 = 高端极简科技产品
```

---

## 混搭工作流

1. **选底色**：暗色（数据/工具）还是亮色（商务/创意）？
2. **选活性**：选最想让人记住的那个交互瞬间
3. **选边框**：与底色匹配的轮廓强度
4. **选分区标签**：字体风格 + 装饰密度
5. **选字体**：统一菜单可读性，变化留给品牌/标签
6. **选装饰**：最多 2 个装饰元素，避免过度设计

组合完成后，从对应原型 HTML 中提取 CSS，合并到一个样式块中，应用到 `AppSidebar.vue`。
