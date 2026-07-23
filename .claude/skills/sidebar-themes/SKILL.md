---
name: sidebar-themes
description: "侧边栏主题模板库。18 套预设计主题，支持快速预览、混搭组合、应用到 AppSidebar.vue。触发条件：(1) 设计/修改侧边栏主题，(2) 侧边栏风格选型，(3) sidebar redesign，(4) 导航栏样式设计，(5) 侧边栏配色方案，(6) 组合多个主题元素。"
---

# 侧边栏主题模板库

18 套预设计侧边栏主题，覆盖三种风格流派：现代玻璃/极简、手绘混合、五元素融合。支持按需加载单个主题 CSS、混搭设计元素、直接应用到 `AppSidebar.vue`。

## 参考文件

| 文件 | 内容 | 何时加载 |
|------|------|----------|
| [themes-catalog.md](references/themes-catalog.md) | 18 套主题完整属性表（底色/轮廓/分区/活性/签名） | 需要浏览全部主题时加载 |
| [theme-composer.md](references/theme-composer.md) | 混搭引擎：如何组合 6 个设计维度的元素 | 需要混搭或创建新主题时加载 |

## 快速预览

在浏览器打开以下文件查看所有主题的并排对比：

```
.claude/skills/sidebar-themes/previews/sidebar-prototypes-all.html       ← 12 款 (A–L)
.claude/skills/sidebar-themes/previews/sidebar-prototypes-fusion.html    ← 6 款融合 (M–R)
```

## 主题索引

### 第一组：现代玻璃/极简（glass/minimal）

| # | 名称 | 底色 | 一句描述 | 适合场景 |
|---|------|------|---------|---------|
| A | Prism 暗色指挥中心 | 深海军蓝玻璃 | 模块色霓虹边缘+径向光晕 | 沉浸式工具、夜间使用 |
| B | Frost 精炼毛玻璃 | 白色半透明玻璃 | 浮动药丸+色点呼吸 | 当前平台风格进化 |
| C | Silk 极简实体 | 暖白实体 | 全高八色渐变左边缘 | 企业级、严肃专业 |
| D | Terminal 开发者工具 | 深灰 #1a1d23 | 等宽+闪烁光标 | 开发者导向 |
| E | Bloom 有机生长 | 暖米玻璃 | 图标放大+呼吸色点 | 温和亲和 |
| F | Grid 瑞士国际风 | 纯白 | 黑底反白+1px 细线 | 极简秩序 |

### 第二组：手绘混合（hand-drawn × business）

| # | 名称 | 技法 | 签名 | 适合场景 |
|---|------|------|------|---------|
| G | Crayon 蜡笔涂色 | 2.5px 纯黑轮廓+不规则圆角 | 填色动画+偏移阴影 | 创意工具、教育 |
| H | Notepad 手账笔记 | 点阵纸底+和纸胶带 | 便签标签贴+折角 badge | 笔记/文档类 |
| I | Doodle 白板涂鸦 | 3.5px 马克笔+荧光笔底 | SVG 波浪下划线+★ | 协作白板 |
| J | Chalkboard 黑板粉笔 | 木纹框+粉笔灰噪点 | 粉笔块填充+粉末辉光 | 教学/演示 |
| K | Watercolor 水彩晕染 | radial-gradient 湿笔触 | 颜料滴+不规则色团 | 创意/设计类 |
| L | Comic 漫画波普 | Ben-Day 网点+4px 黑框 | 对话气泡三角+偏移阴影 | 游戏化/趣味 |

### 第三组：五元素融合（hand-drawn · geometry · AI · tech · business）

| # | 名称 | 🖐️ 手绘 | 📐 几何 | 🤖 AI | 🚀 科技 | 💼 商务 |
|---|------|:--:|:--:|:--:|:--:|:--:|
| M | Neural Sketch | 手写标注+突触脉冲 | 六边形节点+点阵 | 神经网络连线 | 节点激活动画 | 白底+淡蓝灰 |
| N | Cyber Blueprint | Caveat 手写版本号 | 工程网格+标尺线 | AI 节点蓝光 | 蓝图暗底+霓虹 | 等宽字体+暗色 |
| O | Crystal Prism | — | 六边形+菱形切面 | 棱镜色散 5 色 | clip-path 晶面折射 | 极简白+细线 |
| P | Data Flow | — | 贝塞尔流线+粒子 | 数据汇聚脉冲 | 暗色+粒子流光 | 等宽字体+暗色 |
| Q | Origami Tech | — | 锐角折面+切角 | 菱形 AI 核心 | 折纸褶皱阴影 | 纯黑白极简 |
| R | Constellation AI | Caveat 手写分区 | 星座连线+星点 | 星点辉光动画 | 深空底+多层星场 | 暗色+星点克制 |

## 工作流

### 步骤 1：确定需求

向用户确认：
- **风格偏好**：现代/手绘/融合？暗色/亮色？
- **业务场景**：开发者工具？企业平台？创意工具？
- **现有约束**：是否需要与当前 Soft Glass 主题兼容？是否需要保留现有布局？

### 步骤 2：选型推荐

根据需求从 18 套中推荐 2–3 个方向，简述理由。需要时加载 [themes-catalog.md](references/themes-catalog.md) 获取详细属性。

### 步骤 3：预览确认

引导用户在浏览器打开对应 HTML 文件并排对比。用户选定后进入实施。

### 步骤 4：快速应用

**方式 A：完整应用**（选定一个主题直接替换）

1. 从原型 HTML 中提取目标主题的 CSS
2. 将 CSS 变量适配到 `tokens.css` 的 `--app-*` 体系
3. 修改 `AppSidebar.vue` 的 `<style scoped>` 替换为新样式
4. 保留平台 Lucide 图标映射（`layout-dashboard` / `smartphone` / `crosshair` / `layers` / `play-circle` / `file-bar-chart` / `bot` / `git-branch` / `user-round`）

**方式 B：混搭组合**（从多个主题中提取元素）

加载 [theme-composer.md](references/theme-composer.md)，按 6 个维度选择：

```
维度 1: 底色       → 从 {A,B,C,...} 选
维度 2: 轮廓/边框   → 从 {A,B,C,...} 选
维度 3: 分区标签    → 从 {A,B,C,...} 选
维度 4: 活性指示器  → 从 {A,B,C,...} 选
维度 5: 字体       → 从 {A,B,C,...} 选
维度 6: 装饰元素    → 从 {A,B,C,...} 选
```

### 步骤 5：验证

- [ ] 所有 9 个 Lucide 图标正确渲染
- [ ] 8 个模块色映射保持一致
- [ ] 3 个分组（仪表盘 / 测试全流程 / AI 与编排）层级清晰
- [ ] 折叠/展开、拖拽调整宽度功能正常
- [ ] 用户卡片和退出按钮可用
- [ ] 与主内容区（Soft Glass 主题）视觉协调

## 设计令牌映射

所有主题共享 8 个模块色。应用主题时保持此映射不变：

```css
--c-dashboard: #F7C948;   /* 仪表盘 — 柠黄 */
--c-device:    #6BCB77;   /* 设备管理 — 薄荷绿 */
--c-element:   #A78BFA;   /* 元素定位 — 薰衣草紫 */
--c-case:      #4ECDC4;   /* 用例管理 — 青绿 */
--c-runner:    #FF6B6B;   /* 执行引擎 — 桃红 */
--c-report:    #7C6F83;   /* 测试报告 — 灰紫 */
--c-ai:        #E879F9;   /* AI 助手 — 柔粉紫 */
--c-workflow:  #60A5FA;   /* 工作流工作台 — 天蓝 */
```

## 平台图标映射

```javascript
const NAV_ICONS = {
  dashboard:      'layout-dashboard',
  device_pool:    'smartphone',
  element_locator:'crosshair',
  case_manager:   'layers',
  test_runner:    'play-circle',
  report:         'file-bar-chart',
  ai_assistant:   'bot',
  workflow:       'git-branch',
  digital_human:  'user-round',
}
```

## 文件结构

```
.claude/skills/sidebar-themes/
├── SKILL.md                          ← 本文件（入口）
├── references/
│   ├── themes-catalog.md             ← 18 套主题完整属性表
│   └── theme-composer.md             ← 混搭引擎 + 6 维度组件矩阵
└── previews/
    ├── sidebar-prototypes-all.html   ← 12 套并排预览 (A–L)
    ├── sidebar-prototypes-fusion.html← 6 套融合预览 (M–R)
    ├── sidebar-prototypes.html       ← 原始 A–F
    ├── sidebar-prototypes-handdrawn.html  ← 原始 G–I
    └── sidebar-prototypes-handdrawn2.html ← 原始 J–L
```
