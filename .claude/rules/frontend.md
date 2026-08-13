
## 代码编写规范

1. 组件文件（.vue）只负责 UI 渲染和事件绑定。严禁在组件内编写复杂的业务逻辑、数据处理算法或正则解析
2. 严禁在组件内直接使用 fetch 或 axios
3. 严禁在代码中直接使用魔法字符串（Magic Strings）或硬编码的正则
4. Vue 组件文件名必须使用 PascalCase（大驼峰），且后缀必须为 .vue
5. API/认证类 composable 不做表单校验；校验与 ElMessage 警告放在调用方（handleXxx）
6. 公开 TypeScript 签名与实现参数必须同步；禁止实现多参、导出类型少参
7. 新 SVG 图标在 `shared/icons/index.ts` 用 `makeIcon` 导出；禁止无必要的独立 `IconXxx.vue`
8. 抽 shared 组件等第二个真实消费方；单处使用不提前抽象

> 完整取舍与反例 → `dev_docs/项目笔记/前端claude笔记.md` → 编码行为规范（默认取舍）

## 代码拆分规范

1. 当vue代码行数超过 500 行时，请务必进行代码拆分，先拆分**样式层**，再拆分**逻辑层**。
