# frontend · Vue 代码编写规范

> 归属模块：`frontend/src/` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/shared/styles/tokens.css`、`frontend/src/shared/icons/index.ts`、`frontend/src/shared/api-client.ts`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## Vue 代码编写规范

### 1. 硬性规范

1. 组件文件（`.vue`）只负责 UI 渲染和事件绑定。严禁在组件内编写复杂的业务逻辑、数据处理算法或正则解析

2. 严禁在代码中直接使用魔法字符串（Magic Strings）或硬编码的正则

3. Vue 组件文件名必须使用 PascalCase（大驼峰），且后缀必须为 .vue

4. 公开 TypeScript 签名与实现参数必须同步；禁止实现多参、导出类型少参；单测随职责迁移

5. 新 SVG 图标在 `shared/icons/index.ts` 用 `makeIcon` 导出；禁止无必要的独立 `IconXxx.vue`

6. 当 vue 代码行数超过 500 行时，请务必进行代码拆分，先拆分**样式层**，再拆分**逻辑层**。

7. 字号只能取 `tokens.css` 的字号刻度（T0 原子 `--font-size-*`；过渡期 `--app-size-*` 为等价别名，最小 12px），禁止硬编码 `font-size` 字面量。


### 2. API 风格偏好

1. 采用组合式 API + 单文件组件构建 Vue 单页应用.代码示例如下
```vue
<script setup>
import { ref, onMounted } from 'vue'

// 响应式状态
const count = ref(0)

// 用来修改状态、触发更新的函数
function increment() {
  count.value++
}

// 生命周期钩子
onMounted(() => {
  console.log(`The initial count is ${count.value}.`)
})
</script>

<template>
  <button @click="increment">Count is: {{ count }}</button>
</template>
```
