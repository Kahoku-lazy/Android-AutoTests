# Paper × Polaroid 设计系统参考

> 三个模块（侧边栏 / 仪表盘 / 设备管理）当前主题的统一模板。

---

## 一、色彩体系

### 模块色（8 色）

```css
--c-dashboard: #F7C948   /* 仪表盘 — 柠黄 */
--c-device:    #6BCB77   /* 设备管理 — 薄荷绿 */
--c-element:   #A78BFA   /* 元素定位 — 薰衣草紫 */
--c-case:      #4ECDC4   /* 用例管理 — 青绿 */
--c-runner:    #FFB5A7   /* 执行引擎 — 桃粉 */
--c-report:    #7C6F83   /* 测试报告 — 灰紫 */
--c-ai:        #E879F9   /* AI 助手 — 柔粉 */
--c-workflow:  #89CFF0   /* 工作流 — 天蓝 */
```

### 语义色

```css
文本主色:    #2d2d2d
文本副色:    #999
在线/成功:   #6BCB77 (绿底 #C8F5D0)
使用中/警告: #FFB5A7 (粉底 #FFE0DB)
离线/禁用:   #d4d8dc (灰底 #f0ede8)
锁定/绑定:   #A78BFA (紫底 #E8DDF8)
占用/排队:   #F7C948 (黄底 #FFF9E0)
高亮/hover:  #FFE066
```

### Badge 配色模式

```css
/* 模式：彩色底 + 同系深色边框 + 深色文字 */
.badge-online  { background: #C8F5D0; color: #2d7a2d; border: 1.5px solid #6BCB77; }
.badge-busy    { background: #FFE0DB; color: #a03030; border: 1.5px solid #FFB5A7; }
.badge-locked  { background: #E8DDF8; color: #5a3fa0; border: 1.5px solid #A78BFA; }
.badge-process { background: #FFF9E0; color: #7a5a10; border: 1.5px solid #F7C948; }
.badge-offline { background: #f0ede8; color: #999;    border: 1.5px solid #d4d8dc; }
```

---

## 二、背景

```css
background:
  radial-gradient(circle, #d4cdc0 0.8px, transparent 0.8px);
background-size: 14px 14px;
background-color: #fefcf6;
```

---

## 三、字体

```css
品牌/标题:  'Caveat', cursive         /* 手写风格 — 页面标题、分区标签 */
菜单/数据:  'Quicksand', sans-serif   /* 圆润几何 — 导航、统计数字 */
等宽:       'JetBrains Mono', monospace /* 序列号、计数徽章 */
正文回退:   'Inter', 'PingFang SC', 'Microsoft YaHei'
```

**加载方式**: `index.html` 引入 Google Fonts: `Caveat:wght@600;700`

---

## 四、组件模式

### 4.1 页面 Header（WorkbenchHeader）

三模块统一使用 `WorkbenchHeader.vue`：

```css
背景: #fff
底边: 2.5px solid #2d2d2d
图标容器: 40×40, border: 2.5px solid #2d2d2d, border-radius: 8px 16px 6px 14px, rotate(-2deg)
标题: 'Caveat', cursive, 22-24px, #2d2d2d, rotate(-0.5deg)
副标题: 10px, #999
操作按钮: 2.5px solid #2d2d2d, border-radius: 6px 12px 6px 12px, hover → #FFE066
```

### 4.2 KPI 统计条（dashboard / device-pool）

```css
容器: grid 4列, border: 2.5px solid (模块色), border-radius: 4px 8px 4px 8px, bg: #fff
卡片: 内部分割 border-right: 2px solid #e8ecf1
菱形色点: 8×8, rotate(45deg), border-radius: 1px
数值: 'Caveat', 28px, #2d2d2d
标签: 9px, uppercase, #999
```

### 4.3 拍立得卡片（StatsCard / DeviceCard）

```css
容器: bg #fff, border: 2.5px solid (模块色), border-radius: 6px 10px 6px 10px
内边距: 8px 8px 30px 8px (宽底边模拟照片纸)
图钉: radial-gradient(#e8e0d5, #a09080), 9×9, border-radius: 50%, top:4px center
照片区: height 44-60px, border: 2px solid, border-radius: 3px 5px 3px 5px
  .online → bg #C8F5D0, border #6BCB77
  .busy   → bg #FFE0DB, border #FFB5A7  
  .offline→ bg #f0ede8, border #d4d8dc
微旋转: nth-child(3n+1) rotate(-0.8deg) / (3n+2) rotate(0.5deg) / (3n+3) rotate(-0.4deg)
hover: rotate(0) scale(1.03), shadow: 2px 4px 0 rgba(0,0,0,0.08)
阴影: 2px 3px 0 rgba(0,0,0,0.05)
```

### 4.4 纸艺卡片（ModuleNavigator）

```css
容器: bg #fff, border: 2.5px solid #2d2d2d, border-radius: 6px 10px 6px 10px
阴影: 2px 2px 0 rgba(0,0,0,0.04)
hover: translate(1px,1px), shadow: 1px 1px 0 rgba(0,0,0,0.06)
图标: 42×42, border: 2px solid #2d2d2d, border-radius: 4px 8px 4px 8px
进入按钮: border-radius: 4px 8px 4px 8px, 渐变背景
```

### 4.5 表格容器

```css
卡片: el-card, border: 2.5px solid #89CFF0, border-radius: 6px 10px 6px 10px
阴影: 2px 3px 0 rgba(137,207,240,0.12)
表头: bg #f8f6f2, color #2d2d2d, 11px bold, border-bottom: 2px solid #e8ecf1
单元格: color #2d2d2d, border-bottom: 1px solid #f0ede8
hover行: bg #fefdfb
滚动条: #d4cdc0
```

### 4.6 按钮

```css
/* 主要操作按钮 */
.btn-primary {
  border: 2px solid (模块色);
  border-radius: 4px 8px 4px 8px;
  background: #fff;
  font-weight: 700;
}
.btn-primary:hover { background: (模块色浅底); }

/* 危险操作 */
.btn-danger {
  border-color: #FFB5A7;
  color: #a03030;
  background: #FFE0DB;
}

/* 筛选标签按钮组 */
.filter-tab {
  border: 2px solid transparent;
  border-radius: 4px 8px 4px 8px;
  color: #999; font-weight: 700;
}
.filter-tab.active {
  background: #FFE066;
  border-color: #2d2d2d;
  color: #2d2d2d;
}

/* 视图切换 */
.view-toggle {
  border: 2px solid #89CFF0;
  border-radius: 4px 8px 4px 8px;
}
.view-btn.active { background: #89CFF0; color: #fff; }
```

### 4.7 分区标题

```css
/* Caveat 手写 + SVG 波浪下划线 */
font-family: 'Caveat', cursive;
font-size: 18-20px;
color: #2d2d2d;
::after {
  background: url("data:image/svg+xml,...波浪路径...") repeat-x;
  height: 2.5px;
}
```

### 4.8 侧边栏专用（Origami Tech）

```css
背景: linear-gradient(#fdfdfc, #f8f9fb)
边线: border-right: 1px solid #e8ecf1
菜单项: border-radius: 2px, height: 40px, color: #718096
hover: bg #f7fafc, color #1a202c
.active: clip-path折角 + 黑框 + 蓝色菱形Core
分区标签: 10px, #a0aec0, uppercase, ::after 渐隐折线
Badge: #f7fafc, border: 1px solid #e8ecf1
折叠按钮: border-radius: 4px, hover 黑底白字
用户卡片: bg #fff, border: 1px solid #e8ecf1, border-radius: 4px
退出按钮: hover bg #1a202c, color #fff
```

---

## 五、通用规则

| 规则 | 值 |
|------|-----|
| 圆角 | `4px 8px 4px 8px` (纸艺几何) |
| 卡片圆角 | `6px 10px 6px 10px` (拍立得) |
| Badge 圆角 | `3px 6px 3px 6px` |
| 边框粗度 | `2.5px` (主要), `2px` (次要), `1.5px` (Badge) |
| 阴影 | `2px 3px 0 rgba(0,0,0,0.05)` (轻) |
| 黑色锚点 | `#2d2d2d` (仅 Header 底线, 部分标题, 按钮hover) |
| 灰色分割 | `#e8ecf1` (内部线), `#f0ede8` (表格线) |

---

## 六、三模块风格对比

| 元素 | 侧边栏 | 仪表盘 | 设备管理 |
|------|--------|--------|---------|
| 底色 | `#fdfdfc→#f8f9fb` 渐变 | 点阵纸底 14px | 点阵纸底 14px |
| 品牌字 | Inter, 纯黑, 14px | Caveat, 24px, 旋转 | Caveat, 22px, 旋转 |
| 卡片 | 无 | 拍立得: 白框+照片区+图钉 | 纸艺: 粗框+折角 |
| 边框主色 | `#e8ecf1` 灰 | `#2d2d2d` 黑 | 模块色(绿/粉/蓝) |
| 活性指示 | clip-path 折角+菱形 | 旋转放大+阴影 | 粗框+彩色 |
| 数据字体 | Quicksand | Caveat 手写数字 | Caveat KPI / JetBrains序列号 |
| 按钮 | 方角 2px radius | 几何 6px 12px | 模块色粗框 |
