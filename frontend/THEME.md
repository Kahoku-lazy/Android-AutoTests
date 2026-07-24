# Doodle Craft 主题规范

> 极简几何 · 粗线涂鸦 · 彩绘卡通 · 手稿纸

## 设计令牌

**文件**：`frontend/src/shared/styles/tokens.css` 的 `:root` 块

```css
--ink: #1e1e24;       /* 墨黑 — 文字、边框 */
--paper: #fefcf5;     /* 纸白 — 背景 */
--dot: #d8d2c4;       /* 点阵灰 — 底纹点 */

/* 8 模块色 */
--c-dashboard: #F7C948;  --c-device:  #6BCB77;
--c-element:   #A78BFA;  --c-case:    #4ECDC4;
--c-runner:    #FFB5A7;  --c-report:  #7C6F83;
--c-ai:        #E879F9;  --c-workflow:#89CFF0;
```

## 字体

| 用途 | 字体 | 加载 |
|------|------|------|
| 正文 | `Quicksand` 500-800 | `index.html` Google Fonts |
| 手写标题 | `Caveat` 600-700 | `index.html` |
| 等宽 | `JetBrains Mono` 500-700 | `index.html` |

## 全局样式映射

| 元素 | 规则 | 文件 |
|------|------|------|
| `body` | 点阵纸底 `radial-gradient(circle, var(--dot) 0.6px, transparent)` 15px间距 + `var(--paper)` | style.css |
| `.el-card` | `border: 2.5px solid var(--ink)` + `border-radius: 6px 10px` + 白底，**无 blur** | style.css |
| `.el-button--primary` | 黄底黑框 `background: var(--c-dashboard); border: 2.5px solid var(--ink)` | style.css |
| `.el-table th` | `background: #f8f6f2` + `border-bottom: 2px solid var(--ink)` | style.css |
| `.el-tag` | `border-radius: 3px 6px 3px 6px` | style.css |
| `.el-input__wrapper` | 白底 `border: 2px solid var(--ink)`，focus 黄色光晕 | style.css |
| `.el-dialog` | `border: 2.5px solid var(--ink)` + `border-radius: 6px 10px` | style.css |
| `.doc-section` | 白底 `border: 2.5px solid var(--ink)`，**无 blur** | style.css |
| `.wb-btn` | 粗框 `border: 2px solid var(--ink)` + hover 黄底 | workbench-theme.css |
| `.ac-card` | 白底 `border: 2.5px solid var(--ink)`，**无 blur** | workbench-theme.css |
| `.ac-tabs` | 按钮组风格 `border: 2px solid`，活跃态黄底 | workbench-theme.css |

## 组件模式

### 拍立得卡片
- 白底 + `border: 2.5px solid var(--ink)` + `border-radius: 6px 10px`
- `padding: 8px 8px 30px 8px`（宽底边）
- 图钉 `::before`：`radial-gradient(#e8e0d5, #a09080)` 9×9
- 照片区：44-60px 彩色底 + `border: 2px solid var(--ink)`
- 微旋转 `nth-child(3n+1) rotate(-0.6deg)`，hover 回正
- 阴影 `2px 3px 0 rgba(0,0,0,0.05)`

### 纸艺卡片
- 白底 + `border: 2.5px solid var(--ink)` + `border-radius: 4px 10px 6px 8px`
- 阴影 `2px 2px 0 rgba(0,0,0,0.04)`，hover `translate(1px,1px)`

### KPI 统计卡
- `border: 3px solid var(--ink)`，菱形色点 `8×8 rotate(45deg)`
- 数字 `Caveat` 28px，涂鸦 `~` 右下角

### Badge
- `border-radius: 3px 6px 3px 6px` + `border: 1.5px solid var(--ink)`
- 绿底 `#C8F5D0` / 粉底 `#FFE0DB` / 紫底 `#E8DDF8` / 黄底 `#FFF9E0` / 蓝底 `#D4E8FF`

### 按钮
- 默认：白底 + `border: 2px solid var(--ink)` + `border-radius: 4px 8px`
- 活跃：黄底 `var(--c-dashboard)`+ 黑框
- hover：黄底 + `translate(1px,1px)`

### 分区标题
- `Caveat` 18-20px + SVG 波浪下划线 `::after`

### 侧边栏
- `var(--paper)` 底 + `border-right: 3px solid var(--ink)`
- 品牌 `Caveat` 18px，活跃项黄底 + `✦` 闪烁

## 禁止事项

- ❌ `backdrop-filter: blur()` — 全局清零
- ❌ `var(--app-glass-*)` — 已设为透明/白底，不要重新启用
- ❌ `#4a4e69` `#9a8c98` `#89CFF0` 硬编码色值
- ❌ `border-radius: 50px` / `16px` / `20px` 对称大圆角
- ❌ 新模块引入玻璃态样式
