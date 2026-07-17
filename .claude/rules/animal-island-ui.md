# animal-island-ui 设计系统 — Android-AutoTests

> **npm 包**：`animal-island-vue` | **文档**：https://guokaigdg.github.io/animal-island-ui/#/
> **设计风格**：任天堂《集合啦！动物森友会》游戏界面 — 暖木色、大圆角、布纹质感、手绘风格

## 使用原则

1. **优先使用 animal-island-vue 组件**，不满足时再用 Element Plus
2. **Modal 必须替代 el-dialog**：全局 8 处弹窗已全部迁移
3. **Tabs 替代 el-tabs**：所有筛选/分类切换使用动森标签页（leaf-animation + shadow）
4. **配色遵循 13 色语义**：不同模块/状态对应固定颜色，不可随意混用
5. **动画统一用 animejs**：预设 30 种，不超过预设范围

## 配色板（13 色 + 语义映射）

```
app-green        #6fba2c  ████████  草绿 → 设备在线、成功状态（device-pool）
app-blue         #889df0  ████████  蓝   → 模型、信息、Agent 配置（ai-assistant）
app-yellow       #f7cd67  ████████  黄   → AI 智能体、主入口（dashboard）
app-pink         #f8a6b2  ████████  粉   → 执行中、进行中（test-runner）
app-teal         #19c8b9  ████████  青绿 → 用例管理、页面元素（case-manager）
purple           #b39ef3  ████████  紫   → 元素定位、XPath（element-locator）
app-orange       #f7a8c4  ████████  橙   → AI 助手卡片、功能入口
brown            #8b7355  ████████  棕   → 通用/表格/文件管理（report-generator）
app-red          #e85f5f  ████████  红   → 危险操作、删除、错误状态
lime-green       #b6e663  ████████  柠檬绿 → 辅助点缀
yellow-green     #c5db5a  ████████  黄绿   → 辅助点缀
warm-peach-pink  #f5c6a3  ████████  暖桃粉 → 辅助点缀
```

### 模块↔颜色对应

| 模块 | 主色 | 用途 |
|------|------|------|
| dashboard | `app-yellow` | 仪表盘卡片、统计数字 |
| device-pool | `app-green` | 设备卡片（在线/BUSY/OFFLINE） |
| element-locator | `purple` | 元素列表、XPath 展示 |
| case-manager | `app-teal` | 用例卡片、步骤列表 |
| test-runner | `app-pink` | 执行中任务、进度条 |
| report-generator | `brown` | 报告表格、文件列表 |
| ai-assistant | `app-orange` | 智能体卡片、对话气泡 |

## 组件 API 速查

### 必须使用的组件（已全面替换）

**Card** — 所有卡片容器
```vue
<Card color="app-blue" pattern="app-blue" type="dashed">
  <!-- type: default | dashed -->
  <!-- color/pattern: 13 色之一 -->
</Card>
```

**Modal** — 所有弹窗（替代 el-dialog）
```vue
<Modal v-model:open="visible" title="标题" width="480" :typewriter="true" :type-speed="80">
  <template #footer>
    <Button @click="visible = false">取消</Button>
    <Button type="primary" @click="save">确定</Button>
  </template>
</Modal>
```

**Tabs** — 所有标签页切换（替代 el-tabs）
```vue
<Tabs :items="[{ key:'all', label:'全部' }, { key:'running', label:'运行中' }]"
      v-model="activeTab" :leaf-animation="true" :shadow="true" />
```

**Table** — 数据表格（替代 el-table）
```vue
<Table :columns="columns" :data-source="data" row-key="id"
       :striped="true" :loading="loading" empty-text="暂无数据">
  <template #cell-status="{ value }">
    <el-tag>{{ value }}</el-tag>
  </template>
</Table>
```

**Collapse** — 折叠分组（替代手风琴或手写 expand）
```vue
<Collapse question="设备 RF8N21MSW7A · 2 个任务" :default-expanded="true">
  <Card>内容...</Card>
</Collapse>
```

**Button** — 所有按钮
```vue
<Button type="primary" size="small">主要</Button>
<Button type="dashed">虚线</Button>
<Button :loading="true">加载中</Button>
<Button block>块级</Button>
<!-- type: primary | default | dashed | text | link -->
<!-- size: small | middle | large -->
```

### 推荐替换的组件

**Input** → 替代 `el-input`
```vue
<Input v-model="text" size="middle" placeholder="请输入..." :allow-clear="true" :shadow="true" />
```

**Select** → 替代简单 `el-select`

> 🔴 **严禁在 Modal 内使用 Select**：animal-island-vue Modal 的 `.animal-modal__body` 有 `overflow: hidden` + `clip-path`，Select 下拉列表渲染在组件内部会被裁剪。Modal 内请用 `el-select`（Teleport 到 body）。

```vue
<Select v-model="selected" :options="[{ key:'a', label:'A' }, { key:'b', label:'B' }]" />
```

**Switch** → 替代 `el-switch`（已用于 AI 配置页）
```vue
<Switch v-model="enabled" size="small" />
```

**Checkbox / Radio** → 替代 `el-checkbox-group` / `el-radio-group`
```vue
<Checkbox v-model="checked" :options="opts" direction="vertical" />
<Radio v-model="mode" :options="[{ label:'立即', value:'now' }]" />
```

### 装饰性组件

| 组件 | 场景 |
|------|------|
| **Title** | 页面 Hero 标题，替代 `h1/h2`，支持 13 色 |
| **Divider** | 分隔线，`wave-yellow` `dashed-teal` 等 9 种样式 |
| **Tooltip** | 提示气泡，`variant="island"` 不规则有机形状 |
| **Typewriter** | 打字机效果，适合 AI 对话流式输出 |
| **CodeBlock** | JSON 配置/代码展示，适合 Agent 配置预览 |
| **Icon** | 10 种动森原生图标（`icon-chat` `icon-miles` 等）+ bounce 动画 |
| **Phone** | 手机外框，适合设备截图预览 |
| **Footer** | 页面底部装饰，`type="sea"`(海浪) 或 `"tree"`(树木) |
| **Cursor** | 全局自定义动森光标，`force-all` 覆盖所有后代 |
| **Loading** | 动森风格加载动画 |
| **Time** | 游戏内时钟风格时间显示 |

## 全局 CSS 变量

```css
--animal-primary-color          /* 主色 */
--animal-bg-color               /* 背景色（暖米色） */
--animal-bg-color-secondary     /* 次要背景 */
--animal-text-color             /* 文本 (#794f27 暖棕) */
--animal-text-color-secondary   /* 次要文本 (#9f927d 米灰) */
--animal-border-radius-lg       /* 大圆角 (24px) */
--animal-border-radius-md       /* 中圆角 (16px) */
--animal-border-radius-sm       /* 小圆角 (10px) */
--font-display                  /* 标题字体 (Nunito) */
--font-body                     /* 正文字体 */
```

## Element Plus → animal-island-vue 对照

| 功能 | Element Plus | → | animal-island-vue |
|------|-------------|---|-------------------|
| 按钮 | `el-button` | → | `Button` |
| 卡片 | `el-card` | → | `Card` |
| 弹窗 | `el-dialog` | → | `Modal` |
| 标签页 | `el-tabs` | → | `Tabs` |
| 表格 | `el-table` | → | `Table` |
| 折叠 | — | → | `Collapse` |
| 输入框 | `el-input` | → | `Input` |
| 选择器 | `el-select` | → | `Select` |
| 开关 | `el-switch` | → | `Switch` |
| 多选 | `el-checkbox-group` | → | `Checkbox` |
| 单选 | `el-radio-group` | → | `Radio` |
| 提示 | `el-tooltip` | → | `Tooltip` |
| 分割线 | `el-divider` | → | `Divider` |
| 标题 | `h1/h2/h3` | → | `Title` |
| 加载 | `v-loading` | → | `Loading` |
| 代码 | `pre/code` | → | `CodeBlock` |
| 页脚 | 自定义 div | → | `Footer` |

## 页面布局模板

### 卡片网格（仪表盘/AI 助手/设备池）
```vue
<PageHeader title="标题" subtitle="副标题" color="app-yellow" />
<Tabs :items="tabs" v-model="filter" :leaf-animation="true" :shadow="true" />
<div class="card-grid">
  <Card v-for="item in items" :key="item.id" :color="itemColor(item)" :pattern="itemPattern(item)">
    <div class="card-content">...</div>
    <div class="card-actions">
      <Button size="small" type="primary">操作</Button>
      <Button size="small" type="danger" plain>删除</Button>
    </div>
  </Card>
</div>
```

### 表格管理（用例/报告/元素管理）
```vue
<Card color="brown" pattern="brown">
  <Table :columns="cols" :data-source="data" row-key="id" :striped="true">
    <template #cell-actions="{ record }">
      <Button size="small" type="primary" @click="edit(record)">编辑</Button>
      <Button size="small" type="danger" plain @click="remove(record)">删除</Button>
    </template>
  </Table>
</Card>
```

### 折叠分组（执行引擎）
```vue
<Tabs :items="statusTabs" v-model="activeTab" />
<Collapse v-for="group in groups" :key="group.key" :question="group.label" :default-expanded="true">
  <div class="task-list">
    <Card v-for="task in group.items" :key="task.id" :color="task.color" :pattern="task.color">
      <div class="task-header">{{ task.title }}</div>
      <div class="task-body">...</div>
      <div class="task-actions"><Button>操作</Button></div>
    </Card>
  </div>
</Collapse>
```

### 弹窗表单
```vue
<Modal v-model:open="visible" title="表单标题" width="480" :typewriter="true">
  <el-form label-width="80px">
    <!-- 表单内部仍可用 Element Plus 表单组件 -->
  </el-form>
  <template #footer>
    <Button @click="visible = false">取消</Button>
    <Button type="primary" @click="save">确定</Button>
  </template>
</Modal>
```

> 注意：Modal 打开后内部表单仍可混用 Element Plus 组件（`el-form`、`el-input` 等），但操作按钮必须用 animal-island-vue 的 `Button`。
