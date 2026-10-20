<script setup lang="ts">
import { ref, watch } from "vue"
import { ElMessageBox } from "element-plus"
import { NODE_MENU_SIZE } from "@/modules/workflow/helpers/overlayPosition"
import { useContainedOverlay } from "@/modules/workflow/composables/useContainedOverlay"

const props = defineProps<{
  show: boolean
  x: number
  y: number
  nodeId: string
  nodeLabel: string
}>()

const emit = defineEmits<{
  close: []
  deleteNode: []
}>()

/** 浮层根元素 + 已收敛到屏内的位置（光标锚点越界时向屏内平移） */
const { el: menuRef, position, place } = useContainedOverlay(NODE_MENU_SIZE)

function reposition() {
  if (!props.show) return
  void place({ x: props.x, y: props.y })
}

watch(() => [props.show, props.x, props.y] as const, reposition, { immediate: true })

watch(
  () => props.show,
  (v) => {
    if (v) {
      setTimeout(() => document.addEventListener("click", onOutside), 0)
    } else {
      document.removeEventListener("click", onOutside)
    }
  },
)

function onOutside(e: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) {
    emit("close")
  }
}

async function doDelete() {
  try {
    await ElMessageBox.confirm(
      `确定删除节点「${props.nodeLabel}」？相关连线也会删除。`,
      "删除确认",
      {
        confirmButtonText: "删除",
        cancelButtonText: "取消",
        type: "warning",
      },
    )
  } catch {
    // 用户取消删除：ElMessageBox 以 reject 表示取消，不触发删除（非静默吞错）
    return
  }
  emit("deleteNode")
  emit("close")
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="show"
      ref="menuRef"
      class="node-menu"
      :style="{ left: position.x + 'px', top: position.y + 'px' }"
      @click.stop
    >
      <div class="menu-title">{{ nodeLabel }}</div>
      <button class="menu-item danger" @click="doDelete"><span>🗑</span> 删除节点</button>
    </div>
  </Teleport>
</template>

<style scoped>
.node-menu {
  position: fixed;
  z-index: var(--z-popup);
  width: 288px;
  /* 视口兜底：窗口比浮层还矮时按视口收敛（脚本未执行的首帧也不会超出屏幕） */
  max-height: min(420px, calc(100vh - 16px));
  max-height: min(420px, calc(100dvh - 16px));
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--app-bg-card);
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-md);
  box-shadow: var(--app-shadow-lg);
  padding: var(--app-space-sm);
  font-family: var(--app-font);
  --wf-nodemenu-hover-bg: var(--color-cyan-74-a18) /* -> --color-cyan-74-a18 */; /* 菜单项悬停底（工作流蓝 16%） */
}
.menu-title {
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
  padding: 6px var(--app-space-sm) 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  width: 100%;
  padding: 9px 12px;
  border: none;
  border-radius: var(--app-radius-md);
  background: transparent;
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: background var(--app-duration-fast) var(--app-ease);
}
.menu-item:hover {
  background: var(--wf-nodemenu-hover-bg);
}
.menu-item.danger {
  color: var(--app-status-danger-text);
}
.menu-item.danger:hover {
  background: var(--app-status-danger-bg);
  color: var(--app-status-danger-text);
}
</style>
