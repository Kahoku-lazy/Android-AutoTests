<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  show: boolean
  x: number
  y: number
  linkId: number
  /** 默认名（源端口/元素名），未自定义时展示 */
  label: string
  /** 当前自定义名（空字符串 = 未命名） */
  customName: string
}>()

const emit = defineEmits<{
  close: []
  rename: [id: number, name: string]
  delete: [id: number]
}>()

const renaming = ref(false)
const name = ref('')
const menuRef = ref<HTMLDivElement | null>(null)

watch(
  () => props.show,
  (v) => {
    if (v) {
      renaming.value = false
      name.value = props.customName
      setTimeout(() => document.addEventListener('click', onOutside), 0)
    } else {
      document.removeEventListener('click', onOutside)
    }
  }
)

function onOutside(e: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) {
    emit('close')
  }
}

function startRename() {
  renaming.value = true
  name.value = props.customName
}

function confirmRename() {
  renaming.value = false
  emit('rename', props.linkId, name.value.trim())
}

function doDelete() {
  if (!confirm(`删除连线「${props.customName || props.label}」？`)) return
  emit('delete', props.linkId)
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="show"
      ref="menuRef"
      class="edge-menu"
      :style="{ left: x + 'px', top: y + 'px' }"
      @click.stop
    >
      <template v-if="!renaming">
        <div class="edge-menu__title" :title="customName || label">{{ customName || label }}</div>
        <button type="button" class="edge-menu__item" @click="startRename">
          <span>✎</span> 重命名连线
        </button>
        <button type="button" class="edge-menu__item danger" @click="doDelete">
          <span>🗑</span> 删除连线
        </button>
      </template>

      <template v-else>
        <div class="edge-menu__header">
          <button type="button" class="edge-menu__back" @click="renaming = false">←</button>
          <span>重命名连线</span>
        </div>
        <input
          v-model="name"
          class="edge-menu__input"
          :placeholder="`留空恢复默认（${label}）`"
          autofocus
          @keydown.enter="confirmRename"
          @keydown.escape="renaming = false"
        />
        <div class="edge-menu__hint">留空则恢复为源端口（元素）默认名</div>
      </template>
    </div>
  </Teleport>
</template>

<style scoped>
/* Teleport 到 body：用全局 token + 字面量，不能依赖 .workflow-workbench 作用域变量 */
.edge-menu {
  position: fixed;
  z-index: 60;
  width: 248px;
  padding: 6px;
  background: var(--app-bg-card);
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-md);
  box-shadow: var(--app-shadow-lg);
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-family: var(--app-font);
}
.edge-menu__title {
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
  padding: 6px 8px 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.edge-menu__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: background 0.12s var(--app-ease);
}
.edge-menu__item:hover { background: rgba(137, 207, 240, 0.16); }
.edge-menu__item.danger { color: var(--app-status-danger-text); }
.edge-menu__item.danger:hover { background: var(--app-status-danger-bg); }
.edge-menu__header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px 8px;
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
}
.edge-menu__back {
  border: 2px solid var(--ink);
  background: var(--app-bg-card);
  color: var(--ink);
  border-radius: 8px;
  width: 28px;
  height: 28px;
  cursor: pointer;
  font-weight: 700;
  line-height: 1;
}
.edge-menu__back:hover { background: rgba(137, 207, 240, 0.16); }
.edge-menu__input {
  margin: 0 4px 6px;
  padding: 8px 10px;
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-card);
  color: var(--ink);
  font-size: var(--app-size-sm);
  outline: none;
  font-family: inherit;
}
.edge-menu__input:focus { border-color: var(--c-workflow); }
.edge-menu__hint {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  padding: 0 8px 6px;
  font-weight: 600;
}
</style>
