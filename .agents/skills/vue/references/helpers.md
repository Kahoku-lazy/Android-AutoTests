# 纯函数工具（shared/helpers）

放**无状态、无副作用**的纯函数：格式化、解析、纯计算。本仓库的落点是 `frontend/src/shared/helpers/`（现有 `sketchCard.ts`、`mediaUrl.ts`、`deviceOccupancy.ts`），模块私有的纯函数放各自 `helpers/`。

## 边界：什么该放这里，什么不该

| 逻辑 | 放哪 |
| --- | --- |
| 同一输入必得同一输出（格式化、换算、纯校验） | `shared/helpers/*.ts` |
| 需要 `ref` / 生命周期 / 监听 | `composables/` |
| 需要发请求、拼 URL、处理错误码 | `shared/api-client.ts` |
| 只在一个组件里用、且依赖组件状态 | 留在组件内 |

`helpers` 里**不要**出现：`ref`、`reactive`、`onMounted`、`axios`、`window` / `document`。出现任何一个，说明它放错了层。

## 规则

- 具名导出，不用 default。
- 命名写「做什么」：`formatDuration`、`parsePort`、`sketchTiltAt`。
- 一个文件一个主题，别做 `utils.ts` 大杂烩。
- 有分支就有测试：`frontend/tests/` 下放 Vitest 用例（纯函数最好测）。

## 示例

```ts
// shared/helpers/sketchCard.ts（仓库现有写法）
export function sketchTiltAt(index: number): number {
  return [-0.6, 0.5, -0.3, 0.4][index % 4]
}
```

```ts
// 格式化：把后端返回的秒数转可读时长
export function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "—"
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}
```

```ts
// 解析：容错优先，失败返回 null 而不是抛
export function parsePositiveInt(raw: string | null): number | null {
  const n = Number(raw)
  return Number.isInteger(n) && n > 0 ? n : null
}
```

## 错误文案

接口失败的统一文案在 `formatApiError`（`shared/api-client.ts`），不要在 helper 里再发明一套；helper 只负责纯转换，**不吞异常、不弹提示**。

## 常见错误

```ts
// ❌ 带状态：第二次调用结果依赖第一次
let last = 0
export function nextValue() {
  last += 1
  return last
}

// ✅ 纯函数：输入决定输出
export function addOne(value: number): number {
  return value + 1
}

// ❌ 在 helper 里发请求
export async function loadDevices() { ... }

// ✅ 请求进 api-client，helper 只处理数据
export function toDeviceLabel(device: { name: string; port: string }): string {
  return `${device.name} (${device.port})`
}
```

## 相关

- 需要响应式/生命周期 → [composables.md](composables.md)
- 写测试 → [testing.md](testing.md)
