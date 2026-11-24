# 组合式函数（Composables）

把有状态的逻辑收进 `use*` 函数，供多个组件复用。本仓库已有 `shared/composables/`（分页、筛选、图表、展开折叠、侧栏拖拽）与各模块私有 `composables/`，新函数先看这里有没有能复用的。

## 核心规则

1. **只在 setup 顶层调用**，不要放进事件回调、条件分支或循环。
2. **不做「异步 composable」**：在别的 composable 里 `await` 之后会丢生命周期上下文；需要异步就返回 `execute()`，由调用方触发。
3. **返回具名对象**，不要返回数组或散装 ref。
4. **内部状态用 `readonly()` 包一层**，除非确实要让调用方改。
5. **必须有清理**：监听器、定时器、订阅在 `onUnmounted` / `onScopeDispose` 里收掉。
6. **不引入 VueUse**（本仓库没有这个依赖）。需要 debounce/throttle 就写 20 行本地方案，或先在方案里说明要加依赖。

## 结构

```ts
// 示例：shared/composables/usePager.ts（仓库已有 usePagination，先复用它）
import { computed, readonly, ref } from "vue"

export function usePager<T>(items: Ref<T[]>, pageSize = 10) {
  const page = ref(1)
  const totalPages = computed(() => Math.max(1, Math.ceil(items.value.length / pageSize)))
  const paged = computed(() =>
    items.value.slice((page.value - 1) * pageSize, page.value * pageSize),
  )

  function go(next: number) {
    page.value = Math.min(Math.max(1, next), totalPages.value)
  }

  return { page: readonly(page), totalPages, paged, go }
}
```

- 文件名 = 函数名（`usePager.ts` → `usePager`）。
- 选项多就收一个 options 对象，别堆位置参数。
- 返回的 ref 在模板里自动解包，在 JS 里记得 `.value`。

## 生命周期与清理

```ts
import { onMounted, onScopeDispose } from "vue"

export function useSerialStream(port: Ref<string>) {
  let timer: ReturnType<typeof setInterval> | undefined

  onMounted(() => {
    timer = setInterval(() => poll(port.value), 1000)
  })

  onScopeDispose(() => {
    if (timer) clearInterval(timer)
  })
}
```

- `onScopeDispose` 比 `onUnmounted` 更通用：组件卸载、effect scope 结束都会触发。
- 只在组件里用的监听器，`onMounted` + `onUnmounted` 成对出现即可。

**侦听器清理（Vue 3.5+）**：`watch` 里开的定时器/请求用 `onWatcherCleanup()` 收，避免写成 return 函数。

```ts
import { watch, onWatcherCleanup } from "vue"

watch(keyword, () => {
  const controller = new AbortController()
  onWatcherCleanup(() => controller.abort())
  void search(keyword.value, controller.signal)
})
```

## 异步与错误

```ts
export function useLoad<T>(fetcher: () => Promise<T>) {
  const data = ref<T | null>(null)
  const error = ref("")
  const loading = ref(false)

  async function run() {
    loading.value = true
    error.value = ""
    try {
      data.value = await fetcher()
    } catch (e) {
      error.value = formatApiError(e, "加载失败")
    } finally {
      loading.value = false
    }
  }

  return { data, error, loading, run }
}
```

- 请求一律走 `shared/api-client.ts`，错误文案用 `formatApiError`，别在 composable 里手写 `axios`。
- 三态（loading / error / empty）由组件用共享件渲染；composable 只提供状态，不塞 UI。

## 跨组件通信

- 父子：`props` + `emits`，不要为了「方便」把事件一路 `$emit` 上去。
- 远距离、非父子：用 `provide/inject` 配合组合式函数封装，或把共享状态收敛到模块 composable；**不要引入第三方事件总线**（`mitt` 已移除），也不要拿 `provide/inject` 当全局状态。

## 响应式坑

**ref 在 reactive 对象里自动解包，在数组 / Map / Set 里不会：**

```ts
const state = reactive({ count: ref(0) })
state.count++ // 正常

const list = reactive([ref(1)])
list[0].value // 必须 .value

const map = reactive(new Map([["k", ref(1)]]))
map.get("k")!.value // 必须 .value
```

**`watchEffect` 的条件分支不会补追踪：**

```ts
// 条件为 false 时 dep 不会被追踪
watchEffect(() => {
  if (enabled.value) console.log(dep.value)
})

// 条件依赖用显式 watch
watch([enabled, dep], ([on, value]) => {
  if (on) console.log(value)
})
```

**keep-alive 页面里的轮询**：`onDeactivated` 停、`onActivated` 起，否则切走还在跑。

## 常见错误

```ts
// ❌ 内部状态直接暴露，调用方能改
return { count }

// ✅ 只读出口 + 显式动作
return { count: readonly(count), increment }

// ❌ 在事件回调里调 composable
function onClick() {
  usePager(items) // 拿不到组件上下文
}
```

## 相关

- 纯函数（格式化、解析）放 `shared/helpers/`，见 [helpers.md](helpers.md)
- 组件内 props/emits 见 [components.md](components.md)
- 响应式基础见 [reactivity.md](reactivity.md)
