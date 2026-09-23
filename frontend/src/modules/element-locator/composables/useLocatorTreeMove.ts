/**
 * 目录树移动编排（LocatorTree 的逻辑层）。
 *
 * - 桌面指针：交给 el-tree 原生拖放，这里只提供 allow-drop 与落点解析；
 * - 触摸：原生 HTML5 拖放不会被触摸触发，改为长按 1 秒进入拖动态，再用命中测试定落点；
 * - 批量勾选：勾选集合既可直接拖动其中任一节点，也可由「移动到…」弹窗选择目标目录。
 *
 * 组件只做渲染与事件绑定，本文件承载状态与判定，避免 LocatorTree.vue 超过 500 行。
 */
import { computed, onBeforeUnmount, ref } from "vue"
import { ElMessage } from "element-plus"
import type { LocatorFileKind, LocatorTreeNode } from "../types"
import type { LocatorMoveItem } from "../api"

/** el-tree 需要的扁平节点（key 稳定，与后端 id 解耦） */
export interface UiTreeNode {
  key: string
  type: "directory" | "file"
  id: number
  name: string
  kind?: LocatorFileKind
  children?: UiTreeNode[]
}

/** 触摸端从按下到进入拖动态需要按住的时长（毫秒） */
export const TOUCH_LONG_PRESS_MS = 1000

/** 触摸位移超过该阈值视为滚动，取消长按计时 */
const TOUCH_SCROLL_TOLERANCE_PX = 8

/** 命中测试用的 DOM 标记：行 / 项目根落点 */
const NODE_ROW_SELECTOR = "[data-node-key]"
const ROOT_DROP_SELECTOR = "[data-root-drop]"
const NODE_ATTR = "data-node-key"

/** el-tree 的落点类型：只接受 inner（放进目录） */
const DROP_TYPE_INNER = "inner"

export function toUiNodes(nodes: LocatorTreeNode[]): UiTreeNode[] {
  return nodes.map((node) =>
    node.type === "directory"
      ? {
          key: `d-${node.id}`,
          type: "directory" as const,
          id: node.id,
          name: node.name,
          children: toUiNodes(node.children || []),
        }
      : {
          key: `f-${node.id}`,
          type: "file" as const,
          id: node.id,
          name: node.name,
          kind: node.kind,
        },
  )
}

function moveItemOf(node: UiTreeNode): LocatorMoveItem {
  return { kind: node.type === "directory" ? "directory" : "page", id: node.id }
}

/**
 * el-tree 拖放回调传回的是库自己的 Node（data 为宽泛的 Record）。
 * 这里只声明用得到的形状，取回后收窄为 UiTreeNode，避免把库的内部类型引进来。
 */
interface ElDragNode {
  data?: unknown
}

function asUiNode(raw: ElDragNode | null | undefined): UiTreeNode | null {
  return (raw?.data as UiTreeNode | undefined) ?? null
}

export function useLocatorTreeMove(options: {
  treeData: () => LocatorTreeNode[]
  moveItems: (items: LocatorMoveItem[], parentDirectoryId: number | null) => Promise<boolean>
}) {
  const uiTree = computed(() => toUiNodes(options.treeData()))

  /** key → 节点，供勾选集合与命中测试反查 */
  const nodeIndex = computed(() => {
    const index = new Map<string, UiTreeNode>()
    const walk = (nodes: UiTreeNode[]) => {
      for (const node of nodes) {
        index.set(node.key, node)
        if (node.children?.length) walk(node.children)
      }
    }
    walk(uiTree.value)
    return index
  })

  // ── 批量勾选 ──

  const selectMode = ref(false)
  const checkedKeys = ref<string[]>([])

  const checkedItems = computed<LocatorMoveItem[]>(() =>
    checkedKeys.value
      .map((key) => nodeIndex.value.get(key))
      .filter((node): node is UiTreeNode => !!node)
      .map(moveItemOf),
  )
  const checkedCount = computed(() => checkedItems.value.length)

  function toggleSelectMode() {
    selectMode.value = !selectMode.value
    if (!selectMode.value) checkedKeys.value = []
  }

  function onCheck(_node: unknown, info: { checkedKeys?: unknown[] }) {
    checkedKeys.value = (info?.checkedKeys || []).map(String)
  }

  function clearSelection() {
    checkedKeys.value = []
  }

  /** 拖动提交的节点集合：勾选态拖动已勾选节点 → 整批，否则只动被拖的那一个 */
  function itemsForDrag(node: UiTreeNode | null | undefined): LocatorMoveItem[] {
    if (!node) return []
    if (selectMode.value && checkedKeys.value.includes(node.key)) return checkedItems.value
    return [moveItemOf(node)]
  }

  async function submit(items: LocatorMoveItem[], parentDirectoryId: number | null) {
    if (!items.length) return
    const ok = await options.moveItems(items, parentDirectoryId)
    if (ok) clearSelection()
  }

  // ── 桌面原生拖放 ──

  let draggingNode: UiTreeNode | null = null
  /** 本次拖动是否已由「项目根」落点接手（node-drag-end 随后触发，不应再报落点无效） */
  let rootDropHandled = false

  function allowDrag(node: ElDragNode | null) {
    return !!asUiNode(node)
  }

  function allowDrop(_dragging: ElDragNode | null, drop: ElDragNode | null, type: string) {
    return type === DROP_TYPE_INNER && asUiNode(drop)?.type === "directory"
  }

  function onNodeDragStart(node: ElDragNode | null) {
    draggingNode = asUiNode(node)
    rootDropHandled = false
  }

  function onNodeDragEnd(_dragging: ElDragNode | null, drop: ElDragNode | null, type: string) {
    draggingNode = null
    if (rootDropHandled) {
      rootDropHandled = false
      return
    }
    // allow-drop 已挡下文件落点，node-drop 不会触发；这里补一句可操作提示
    if (asUiNode(drop)?.type === "file" && type === DROP_TYPE_INNER) {
      ElMessage.warning("只能放到目录或项目根")
    }
  }

  async function onNodeDrop(dragging: ElDragNode | null, drop: ElDragNode | null, type: string) {
    const target = asUiNode(drop)
    const source = asUiNode(dragging) ?? draggingNode
    draggingNode = null
    if (!source || !target || type !== DROP_TYPE_INNER || target.type !== "directory") return
    await submit(itemsForDrag(source), target.id)
  }

  async function onRootDrop() {
    const source = draggingNode
    draggingNode = null
    if (!source) return
    rootDropHandled = true
    await submit(itemsForDrag(source), null)
  }

  // ── 触摸长按拖拽 ──

  const touchActive = ref(false)
  const touchDragging = ref(false)
  const touchSource = ref<UiTreeNode | null>(null)
  const touchTargetId = ref<number | null>(null)
  const touchOnRoot = ref(false)

  let touchTimer: ReturnType<typeof setTimeout> | null = null
  let touchStartPoint: { x: number; y: number } | null = null
  let touchPendingKey: string | null = null

  function clearTouchTimer() {
    if (touchTimer != null) {
      clearTimeout(touchTimer)
      touchTimer = null
    }
  }

  function enterTouchDrag() {
    const node = touchPendingKey ? nodeIndex.value.get(touchPendingKey) : undefined
    if (!node) return
    touchDragging.value = true
    touchSource.value = node
    touchTargetId.value = null
    touchOnRoot.value = false
  }

  function onTouchStart(event: TouchEvent) {
    touchActive.value = true
    if (event.touches.length !== 1) return
    const row = (event.target as HTMLElement | null)?.closest(NODE_ROW_SELECTOR)
    const key = row?.getAttribute(NODE_ATTR)
    if (!key) return
    const touch = event.touches[0]
    touchPendingKey = key
    touchStartPoint = { x: touch.clientX, y: touch.clientY }
    clearTouchTimer()
    touchTimer = setTimeout(enterTouchDrag, TOUCH_LONG_PRESS_MS)
  }

  function updateTouchTarget(x: number, y: number) {
    const hit = document.elementFromPoint(x, y) as HTMLElement | null
    if (hit?.closest(ROOT_DROP_SELECTOR)) {
      touchOnRoot.value = true
      touchTargetId.value = null
      return
    }
    const row = hit?.closest(NODE_ROW_SELECTOR) ?? null
    const node = row ? nodeIndex.value.get(row.getAttribute(NODE_ATTR) || "") : undefined
    touchOnRoot.value = false
    touchTargetId.value = node?.type === "directory" ? node.id : null
  }

  function onTouchMove(event: TouchEvent) {
    const touch = event.touches[0]
    if (!touch) return
    if (!touchDragging.value) {
      // 未进入拖动态时，位移超过阈值按滚动处理并取消长按
      if (!touchStartPoint) return
      const moved =
        Math.abs(touch.clientX - touchStartPoint.x) + Math.abs(touch.clientY - touchStartPoint.y)
      if (moved > TOUCH_SCROLL_TOLERANCE_PX) {
        clearTouchTimer()
        touchPendingKey = null
        touchStartPoint = null
      }
      return
    }
    event.preventDefault()
    updateTouchTarget(touch.clientX, touch.clientY)
  }

  async function onTouchEnd() {
    clearTouchTimer()
    touchActive.value = false
    touchStartPoint = null
    touchPendingKey = null
    if (!touchDragging.value) return
    const source = touchSource.value
    const targetId = touchTargetId.value
    const onRoot = touchOnRoot.value
    touchDragging.value = false
    touchSource.value = null
    touchTargetId.value = null
    touchOnRoot.value = false
    if (!source) return
    if (!onRoot && targetId == null) {
      ElMessage.warning("只能放到目录或项目根")
      return
    }
    await submit(itemsForDrag(source), onRoot ? null : targetId)
  }

  function onTouchCancel() {
    clearTouchTimer()
    touchActive.value = false
    touchDragging.value = false
    touchSource.value = null
    touchTargetId.value = null
    touchOnRoot.value = false
    touchStartPoint = null
    touchPendingKey = null
  }

  onBeforeUnmount(clearTouchTimer)

  return {
    uiTree,
    selectMode,
    checkedKeys,
    checkedCount,
    checkedItems,
    toggleSelectMode,
    onCheck,
    clearSelection,
    moveCheckedTo: (directoryId: number | null) => submit(checkedItems.value, directoryId),
    allowDrag,
    allowDrop,
    onNodeDragStart,
    onNodeDragEnd,
    onNodeDrop,
    onRootDrop,
    touchActive,
    touchDragging,
    touchSourceKey: computed(() => touchSource.value?.key ?? null),
    touchTargetId,
    touchOnRoot,
    onTouchStart,
    onTouchMove,
    onTouchEnd,
    onTouchCancel,
  }
}
