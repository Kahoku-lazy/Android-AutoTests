# animal-island-ui 设计素材 & 组件参考

> 来源：https://guokaigdg.github.io/animal-island-ui/
> 设计风格：任天堂《集合啦！动物森友会》游戏界面
> npm 包：`animal-island-vue` (Vue 3 版本) | React 版：`animal-island-ui`
>
> **文档首页**：https://guokaigdg.github.io/animal-island-ui/#/

---

## 本地包路径

```
npm 包根目录     node_modules/animal-island-vue/
类型定义          node_modules/animal-island-vue/dist/types/components/
入口导出          node_modules/animal-island-vue/dist/types/index.d.ts
组件源码(打包)    node_modules/animal-island-vue/dist/es/index.js
样式入口          node_modules/animal-island-vue/dist/index.css
README           node_modules/animal-island-vue/README.md
CHANGELOG        node_modules/animal-island-vue/CHANGELOG.md
```

### 所有组件类型文件速查表

| 组件 | 类型文件路径 |
|------|------------|
| Button | `.../types/components/Button/types.d.ts` |
| Card | `.../types/components/Card/types.d.ts` |
| Checkbox | `.../types/components/Checkbox/types.d.ts` |
| CodeBlock | `.../types/components/CodeBlock/types.d.ts` |
| Collapse | `.../types/components/Collapse/types.d.ts` |
| Cursor | `.../types/components/Cursor/types.d.ts` |
| Divider | `.../types/components/Divider/types.d.ts` |
| Footer | `.../types/components/Footer/types.d.ts` |
| Icon | `.../types/components/Icon/types.d.ts` |
| Input | `.../types/components/Input/types.d.ts` |
| Loading | `.../types/components/Loading/types.d.ts` |
| Modal | `.../types/components/Modal/types.d.ts` |
| Phone | `.../types/components/Phone/types.d.ts` |
| Radio | `.../types/components/Radio/types.d.ts` |
| Select | `.../types/components/Select/types.d.ts` |
| Switch | `.../types/components/Switch/types.d.ts` |
| Table | `.../types/components/Table/types.d.ts` |
| Tabs | `.../types/components/Tabs/types.d.ts` |
| Time | `.../types/components/Time/types.d.ts` |
| Title | `.../types/components/Title/types.d.ts` |
| Tooltip | `.../types/components/Tooltip/types.d.ts` |
| Typewriter | `.../types/components/Typewriter/types.d.ts` |
| WeddingInvitation | `.../types/components/WeddingInvitation/types.d.ts` |

> 📁 以上路径均相对于 `./frontend/node_modules/animal-island-vue/dist/`

---

## 安装与引入

```bash
npm install animal-island-vue
```

```js
// main.js — 全局注册
import AnimalIslandVue from 'animal-island-vue'
import 'animal-island-vue/style'
app.use(AnimalIslandVue)

// 或按需引入
import { Button, Card, Modal, Tabs, Table, Collapse, Divider, Switch, Select, Input, Title, Tooltip, Typewriter, CodeBlock, Footer, Checkbox, Radio, Loading, Cursor, Icon, Time, Phone } from 'animal-island-vue'
import 'animal-island-vue/style'
```

---

## 组件清单（22 个）

### 🧱 基础组件

#### 1. Button — [/#/button](https://guokaigdg.github.io/animal-island-ui/#/button)
> 📁 `types/components/Button/types.d.ts`

```ts
type ButtonType = 'primary' | 'default' | 'dashed' | 'text' | 'link'
type ButtonSize = 'small' | 'middle' | 'large'

interface ButtonProps {
  type?: ButtonType
  size?: ButtonSize
  danger?: boolean
  ghost?: boolean
  block?: boolean
  loading?: boolean
  disabled?: boolean
  htmlType?: 'submit' | 'reset' | 'button'
}
```

```vue
<Button type="primary" size="small" @click="handle">主要按钮</Button>
<Button type="dashed">虚线按钮</Button>
<Button type="danger" ghost>危险幽灵</Button>
<Button :loading="true">加载中</Button>
<Button block>块级按钮</Button>
```

| 平台使用 | ✅ 全局使用 |

---

#### 2. Title — [/#/title](https://guokaigdg.github.io/animal-island-ui/#/title)
> 📁 `types/components/Title/types.d.ts`

```ts
type TitleSize = 'small' | 'middle' | 'large'
type TitleColor = 'app-pink' | 'purple' | 'app-blue' | 'app-yellow' | 'app-orange' | 'app-teal' | 'app-green' | 'app-red' | 'lime-green' | 'yellow-green' | 'brown' | 'warm-peach-pink'
```

```vue
<Title size="large" color="app-yellow">欢迎来到无人岛</Title>
```

| 平台使用 | 🔲 未使用 — 可替代 el-h1/h2 标题 |

---

#### 3. Divider — [/#/divider](https://guokaigdg.github.io/animal-island-ui/#/divider)
> 📁 `types/components/Divider/types.d.ts`

```ts
type DividerType =
  | 'line-brown' | 'line-teal' | 'line-white' | 'line-yellow'
  | 'wave-yellow'
  | 'dashed-brown' | 'dashed-teal' | 'dashed-white' | 'dashed-yellow'
```

```vue
<Divider type="wave-yellow" />
<Divider type="dashed-teal" />
```

| 平台使用 | ✅ AI 助手配置页（Step 4 工具区） |

---

#### 4. Icon — [/#/icon](https://guokaigdg.github.io/animal-island-ui/#/icon)
> 📁 `types/components/Icon/types.d.ts`

```ts
type IconName = 'icon-miles' | 'icon-camera' | 'icon-chat' | 'icon-critterpedia'
  | 'icon-design' | 'icon-diy' | 'icon-helicopter' | 'icon-map'
  | 'icon-shopping' | 'icon-variant'

interface IconProps {
  name: IconName
  size?: number | string
  bounce?: boolean  // 弹跳动画
}
```

```vue
<Icon name="icon-chat" :size="32" :bounce="true" />
<Icon name="icon-miles" :size="24" />
```

| 平台使用 | 🔲 未使用 — 10 种动森原生图标 |

---

### 📦 容器/布局

#### 5. Card — [/#/card](https://guokaigdg.github.io/animal-island-ui/#/card)
> 📁 `types/components/Card/types.d.ts`

```ts
type CardType = 'default' | 'dashed'
type CardColor = 'app-pink' | 'purple' | 'app-blue' | 'app-yellow' | 'app-orange' | 'app-teal' | 'app-green' | 'app-red' | 'lime-green' | 'yellow-green' | 'brown' | 'warm-peach-pink'
type CardPattern = 'none' | CardColor

interface CardProps {
  type?: CardType
  color?: CardColor
  pattern?: CardPattern
}
```

```vue
<Card color="app-blue" pattern="app-blue" type="dashed">
  <p>虚线边框蓝色卡片</p>
</Card>
```

**配色速查：**
- `app-green` — 草绿（设备/成功）
- `app-blue` — 蓝（模型/信息）
- `app-yellow` — 黄（AI/智能体）
- `app-pink` — 粉（执行中）
- `app-teal` — 青绿（用例）
- `purple` — 紫（元素定位）
- `app-orange` — 橙（AI 助手卡片）
- `brown` — 棕（通用/表格）
- `app-red` — 红（危险/删除）
- `lime-green` — 柠檬绿
- `yellow-green` — 黄绿
- `warm-peach-pink` — 暖桃粉

| 平台使用 | ✅ AI 助手卡片、测试用例表格、执行引擎任务卡片 |

---

#### 6. Collapse — [/#/collapse](https://guokaigdg.github.io/animal-island-ui/#/collapse)
> 📁 `types/components/Collapse/types.d.ts`

```ts
interface CollapseProps {
  question?: string    // 标题文本（或使用 #question 插槽）
  answer?: string      // 内容文本（或使用 default 插槽）
  defaultExpanded?: boolean
  expanded?: boolean   // 受控展开
  disabled?: boolean
}
// Events: change, update:expanded
// Slots: #question, default
```

```vue
<Collapse question="设备 RF8N21MSW7A · 2 个任务" :default-expanded="true">
  <Card>任务卡片内容...</Card>
</Collapse>
```

| 平台使用 | ✅ 执行引擎设备分组 |

---

#### 7. Modal — [/#/modal](https://guokaigdg.github.io/animal-island-ui/#/modal)
> 📁 `types/components/Modal/types.d.ts`

```ts
interface ModalProps {
  open: boolean
  title?: string
  width?: number | string
  maskClosable?: boolean   // 点击遮罩关闭
  showFooter?: boolean
  typewriter?: boolean     // 标题打字机效果
  typeSpeed?: number       // 打字速度 (ms)
}
// Events: close, ok, update:open
// Slots: default, #title, #footer
```

```vue
<Modal v-model:open="visible" title="新建任务" width="480" :typewriter="true" :type-speed="80">
  <el-form>表单内容...</el-form>
  <template #footer>
    <Button @click="visible = false">取消</Button>
    <Button type="primary" @click="save">确定</Button>
  </template>
</Modal>
```

| 平台使用 | ✅ 全局替换 el-dialog（8 处） |

---

#### 8. Tabs — [/#/tabs](https://guokaigdg.github.io/animal-island-ui/#/tabs)
> 📁 `types/components/Tabs/types.d.ts`

```ts
interface TabItem {
  key: string
  label: string
}
interface TabsProps {
  items: TabItem[]
  modelValue?: string
  defaultActiveKey?: string
  leafAnimation?: boolean   // 叶子摆动动画
  shadow?: boolean          // 选中项阴影
}
// Events: change, update:modelValue
```

```vue
<Tabs
  :items="[{ key: 'all', label: '全部' }, { key: 'running', label: '运行中' }]"
  v-model="activeTab"
  :leaf-animation="true"
  :shadow="true"
/>
```

| 平台使用 | ✅ AI 助手筛选、执行引擎状态切换、测试用例分类 |

---

#### 9. Table — [/#/table](https://guokaigdg.github.io/animal-island-ui/#/table)
> 📁 `types/components/Table/types.d.ts`

```ts
interface TableColumn<T> {
  title: string | (() => VNode | string)
  dataIndex?: keyof T & string
  render?: (value, record, index) => VNode | string | null
  width?: string | number
  align?: 'left' | 'center' | 'right'
  style?: CSSProperties
}
interface TableProps<T> {
  columns?: TableColumn<T>[]
  dataSource?: T[]
  rowKey?: string | ((record) => string)
  striped?: boolean
  showHeader?: boolean
  loading?: boolean
  emptyText?: string
  scroll?: { x?: number | string; y?: number | string }
}
// Slots: cell-{dataIndex}({ value, record, index }), header-{dataIndex}, empty
```

```vue
<Table
  :columns="columns"
  :data-source="data"
  row-key="id"
  :striped="true"
  :loading="loading"
  empty-text="暂无数据"
>
  <template #cell-status="{ value }">
    <el-tag :type="value ? 'success' : 'info'">{{ value ? '启用' : '停用' }}</el-tag>
  </template>
</Table>
```

| 平台使用 | ✅ 测试用例管理页 |

---

### 📝 表单输入

#### 10. Input — [/#/input](https://guokaigdg.github.io/animal-island-ui/#/input)
> 📁 `types/components/Input/types.d.ts`

```ts
type InputSize = 'small' | 'middle' | 'large'

interface InputProps {
  modelValue?: string
  size?: InputSize
  allowClear?: boolean
  status?: 'error' | 'warning'
  shadow?: boolean
  disabled?: boolean
  placeholder?: string
  type?: string
  readonly?: boolean
  maxlength?: number
}
```

```vue
<Input v-model="text" size="middle" placeholder="请输入..." :allow-clear="true" :shadow="true" />
```

| 平台使用 | 🔲 未使用 — 可替换所有 el-input |

---

#### 11. Select — [/#/select](https://guokaigdg.github.io/animal-island-ui/#/select)
> 📁 `types/components/Select/types.d.ts`

```ts
interface SelectOption {
  key: string
  label: string
}
interface SelectProps {
  modelValue: string
  options: SelectOption[]
  placeholder?: string
  disabled?: boolean
}
```

```vue
<Select v-model="selected" :options="[{ key:'a', label:'选项A' }, { key:'b', label:'选项B' }]" />
```

| 平台使用 | 🔲 未使用 — 可替换简单 el-select |

---

#### 12. Switch — [/#/switch](https://guokaigdg.github.io/animal-island-ui/#/switch)
> 📁 `types/components/Switch/types.d.ts`

```ts
type SwitchSize = 'small' | 'default'

interface SwitchProps {
  modelValue?: boolean
  defaultChecked?: boolean
  size?: SwitchSize
  disabled?: boolean
  loading?: boolean
}
```

```vue
<Switch v-model="enabled" size="small" />
```

| 平台使用 | ✅ AI 智能体配置页 |

---

#### 13. Checkbox — [/#/checkbox](https://guokaigdg.github.io/animal-island-ui/#/checkbox)
> 📁 `types/components/Checkbox/types.d.ts`

```ts
type CheckboxSize = 'small' | 'middle' | 'large'

interface CheckboxOption {
  label: string
  value: string | number
  disabled?: boolean
}
interface CheckboxProps {
  modelValue?: (string | number)[]
  options: CheckboxOption[]
  size?: CheckboxSize
  disabled?: boolean
  direction?: 'horizontal' | 'vertical'
}
```

```vue
<Checkbox v-model="checked" :options="opts" direction="vertical" />
```

| 平台使用 | 🔲 未使用 — 可替换 el-checkbox-group |

---

#### 14. Radio — [/#/radio](https://guokaigdg.github.io/animal-island-ui/#/radio)
> 📁 `types/components/Radio/types.d.ts`

```ts
type RadioSize = 'small' | 'middle' | 'large'

interface RadioOption {
  label: string
  value: string | number
  disabled?: boolean
}
interface RadioProps {
  modelValue?: string | number
  options: RadioOption[]
  size?: RadioSize
  disabled?: boolean
  direction?: 'horizontal' | 'vertical'
}
```

```vue
<Radio v-model="mode" :options="[{ label:'立即', value:'now' }, { label:'定时', value:'scheduled' }]" />
```

| 平台使用 | 🔲 未使用 — 可替换 el-radio-group |

---

### 🎨 视觉/装饰

#### 15. Tooltip — [/#/tooltip](https://guokaigdg.github.io/animal-island-ui/#/tooltip)
> 📁 `types/components/Tooltip/types.d.ts`

```ts
type TooltipPlacement = 'top' | 'bottom' | 'left' | 'right' | 'top-start' | 'top-end' | 'bottom-start' | 'bottom-end' | 'left-start' | 'left-end' | 'right-start' | 'right-end'
type TooltipTrigger = 'hover' | 'focus' | 'click'
type TooltipVariant = 'default' | 'island'  // island = 不规则有机气泡

interface TooltipProps {
  title?: string
  placement?: TooltipPlacement
  trigger?: TooltipTrigger
  variant?: TooltipVariant
  bordered?: boolean
}
```

```vue
<Tooltip title="这是提示" placement="top" variant="island" :bordered="true">
  <span>悬停查看提示</span>
</Tooltip>
```

| 平台使用 | 🔲 未使用 — 不规则气泡是新拟态移动端风格差异点 |

---

#### 16. Cursor — [/#/cursor](https://guokaigdg.github.io/animal-island-ui/#/cursor)
> 📁 `types/components/Cursor/types.d.ts`

```ts
interface CursorProps {
  forceAll?: boolean  // true=全覆盖所有后代 cursor
}
```

```vue
<Cursor :force-all="true">
  <div>此区域内所有元素使用动森自定义光标</div>
</Cursor>
```

| 平台使用 | 🔲 未使用 — 全局更换光标 |

---

#### 17. Loading — [/#/loading](https://guokaigdg.github.io/animal-island-ui/#/loading)
> 📁 `types/components/Loading/types.d.ts`

```ts
interface LoadingProps {
  active?: boolean
}
```

```vue
<Loading :active="loading" />
```

| 平台使用 | 🔲 未使用 |

---

#### 18. Footer — [/#/footer](https://guokaigdg.github.io/animal-island-ui/#/footer)
> 📁 `types/components/Footer/types.d.ts`

```ts
type FooterType = 'sea' | 'tree'  // 海浪 | 树木

interface FooterProps {
  type?: FooterType
}
```

```vue
<Footer type="sea" />
```

| 平台使用 | 🔲 未使用 — 适合作为页面底部装饰 |

---

### 🧩 特殊组件

#### 19. Time — [/#/time](https://guokaigdg.github.io/animal-island-ui/#/time)
> 📁 `types/components/Time/types.d.ts`

```ts
// 无 props，显示游戏内时钟风格的时间
```

| 平台使用 | 🔲 未使用 |

---

#### 20. Typewriter — [/#/typewriter](https://guokaigdg.github.io/animal-island-ui/#/typewriter)
> 📁 `types/components/Typewriter/types.d.ts`

```ts
interface TypewriterProps {
  // 逐字打印文本效果
}
```

```vue
<Typewriter text="正在加载..." />
```

| 平台使用 | 🔲 未使用 — AI 对话流式输出可结合 |

---

#### 21. CodeBlock — [/#/codeblock](https://guokaigdg.github.io/animal-island-ui/#/codeblock)
> 📁 `types/components/CodeBlock/types.d.ts`

```ts
interface CodeBlockProps {
  code: string
}
```

```vue
<CodeBlock :code="jsonString" />
```

| 平台使用 | 🔲 未使用 — 可替代 JSON 配置预览 |

---

#### 22. Phone — [/#/phone](https://guokaigdg.github.io/animal-island-ui/#/phone)
> 📁 `types/components/Phone/types.d.ts`

```ts
// 无 props，手机外框模拟器（屏幕截图外框）
```

| 平台使用 | 🔲 未使用 — 适合设备截图预览 |

---

#### 23. WeddingInvitation — [/#/weddinginvitation](https://guokaigdg.github.io/animal-island-ui/#/weddinginvitation)
> 📁 `types/components/WeddingInvitation/types.d.ts`

```ts
interface WeddingInvitationProps { /* ... */ }
interface WeddingInvitationExpose { /* ... */ }

// 婚礼请柬组件 + WeddingInvitationExportButton（导出按钮）
```

| 平台使用 | 🔲 未使用 |

---

## 配色板（13 色）

```
app-green        #6fba2c  ████████  草绿 — 设备在线/成功
app-blue         #889df0  ████████  蓝 — 模型/信息
app-yellow       #f7cd67  ████████  黄 — AI/智能体
app-pink         #f8a6b2  ████████  粉 — 执行中
app-teal         #19c8b9  ████████  青绿 — 用例/元素
purple           #b39ef3  ████████  紫 — 元素定位
app-orange       #f7a8c4  ████████  橙 — 功能入口
brown            #8b7355  ████████  棕 — 通用/表格
app-red          #e85f5f  ████████  红 — 危险/错误
lime-green       #b6e663  ████████  柠檬绿
yellow-green     #c5db5a  ████████  黄绿
warm-peach-pink  #f5c6a3  ████████  暖桃粉
default          inherit  ████████  继承
```

---

## 全局样式变量

```css
--animal-primary-color          /* 主色 */
--animal-bg-color               /* 背景 */
--animal-bg-color-secondary     /* 次要背景 */
--animal-text-color             /* 文本 (#794f27 暖棕) */
--animal-text-color-secondary   /* 次要文本 (#9f927d 米灰) */
--animal-border-radius-lg       /* 大圆角 (24px) */
--animal-border-radius-md       /* 中圆角 (16px) */
--animal-border-radius-sm       /* 小圆角 (10px) */
--font-display                  /* 标题字体 (Nunito) */
--font-body                     /* 正文字体 (系统默认) */
```

---

## 平台组件使用对照

| 功能 | Element Plus | → animal-island-vue |
|------|-------------|---------------------|
| 按钮 | `el-button` | `Button` |
| 卡片 | `el-card` | `Card` |
| 弹窗 | `el-dialog` | `Modal` |
| 标签页 | `el-tabs` | `Tabs` |
| 表格 | `el-table` | `Table` |
| 折叠 | — | `Collapse` |
| 输入框 | `el-input` | `Input` |
| 选择器 | `el-select` | `Select` |
| 开关 | `el-switch` | `Switch` |
| 多选 | `el-checkbox-group` | `Checkbox` |
| 单选 | `el-radio-group` | `Radio` |
| 提示 | `el-tooltip` | `Tooltip` |
| 分割线 | `el-divider` | `Divider` |
| 标题 | `h1/h2/h3` | `Title` |
| 加载 | `v-loading` | `Loading` |
| 代码 | `pre/code` | `CodeBlock` |
| 页脚 | 自定义 div | `Footer` |

---

## 快速参考模板

### 列表卡片页
```vue
<PageHeader title="..." subtitle="..." color="app-yellow" />
<Tabs :items="tabs" v-model="filter" :leaf-animation="true" :shadow="true" />
<div class="card-grid">
  <Card v-for="item in items" :key="item.id" :color="itemColor(item)" :pattern="itemPattern(item)">
    <div class="card-avatar">{{ item.avatar }}</div>
    <div class="card-name">{{ item.name }}</div>
    <div class="card-tags"><el-tag round effect="plain" size="small">标签</el-tag></div>
    <div class="card-actions">
      <Button size="small" type="primary">操作</Button>
      <Button size="small" type="danger" plain>删除</Button>
    </div>
  </Card>
</div>
```

### 表格式管理页
```vue
<Card color="brown" pattern="brown">
  <Table :columns="cols" :data-source="data" row-key="id" :striped="true">
    <template #cell-actions="{ record }">
      <Button size="small" type="primary" @click="edit(record)">编辑</Button>
      <Button size="small" type="danger" plain @click="remove(record)">删除</Button>
    </template>
    <template #empty><p>暂无数据</p></template>
  </Table>
</Card>
```

### 折叠分组页
```vue
<Tabs :items="statusTabs" v-model="activeTab" />
<Collapse v-for="group in groups" :key="group.key" :question="group.label" :default-expanded="true">
  <div class="task-list">
    <Card v-for="task in group.items" :key="task.id" :color="task.color" :pattern="task.color">
      <div class="task-header">{{ task.title }}</div>
      <div class="task-body">...</div>
      <div class="task-actions">
        <Button>操作</Button>
      </div>
    </Card>
  </div>
</Collapse>
```

### 弹窗表单
```vue
<Modal v-model:open="visible" title="表单标题" width="480" :typewriter="true">
  <el-form label-width="80px">
    <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
    <el-form-item label="选择"><el-select v-model="form.type">...</el-select></el-form-item>
  </el-form>
  <template #footer>
    <Button @click="visible = false">取消</Button>
    <Button type="primary" @click="save">确定</Button>
  </template>
</Modal>
```
