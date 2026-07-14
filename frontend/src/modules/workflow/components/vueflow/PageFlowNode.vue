<script setup lang="ts">
import { computed, inject, nextTick, watch } from 'vue'
import { Handle, Position, useVueFlow } from '@vue-flow/core'
import type { NodeProps } from '@vue-flow/core'
import type { PageFlowNodeData } from '@/modules/workflow/composables/useVueFlowAdapter'
import { portHandleColor } from '@/modules/workflow/composables/useVueFlowAdapter'
import { useWorkflowStore } from '@/modules/workflow/stores/workflowStore'
import { ELEMENT_ICONS, MULTI_IN_PORT_TYPES } from '@/modules/workflow/types/workflow'
import type { StartKind } from '@/modules/workflow/types/workflow'

const props = defineProps<NodeProps<PageFlowNodeData>>()
const store = useWorkflowStore()
const { updateNodeInternals } = useVueFlow()

const openPicker = inject<(nodeId: string) => void>('vfOpenPicker', () => {})
const refreshFlow = inject<() => void>('vfRefresh', () => {})
const addToCase = inject<(nodeId: string, slot: number, step: 'click' | 'wait') => void>(
  'vfAddToCase',
  () => {}
)

const isPopup = computed(() => props.data.nodeType === 'PopupNode')
const isStart = computed(() => props.data.nodeType === 'StartNode')
const isEnd = computed(() => props.data.nodeType === 'EndNode')
const startKind = computed<StartKind>(() => props.data.startKind || 'app')

const accent = computed(() => {
  if (isStart.value) return '#6fba2c'
  if (isEnd.value) return '#8a8a96'
  if (isPopup.value) return '#e85f5f'
  return '#19c8b9'
})

const icon = computed(() => {
  if (isStart.value) return '▶'
  if (isEnd.value) return '⏹'
  if (isPopup.value) return '⚠️'
  return '📱'
})

function onRename(e: Event) {
  const v = (e.target as HTMLInputElement).value.trim()
  if (v) store.renameNode(props.id, v)
}

function onAddElement() {
  openPicker(props.id)
}

async function refreshHandles() {
  await nextTick()
  updateNodeInternals([props.id])
}

function onAddToCase(slot: number, step: 'click' | 'wait') {
  addToCase(props.id, slot, step)
}

function onRemovePort(slot: number) {
  store.removePort(props.id, slot)
  refreshFlow()
}

function onTogglePortType(slot: number) {
  if (isStart.value && startKind.value === 'app') return
  store.togglePortType(props.id, slot)
  store.setStatus(
    '已切换端口类型（navigation↔popup_fixed）。连「入口」必须是 navigation；连弹窗「触发」用 popup_fixed'
  )
  refreshFlow()
}

function onStartKind(kind: StartKind) {
  store.setStartKind(props.id, kind)
  refreshFlow()
}

function onPackageChange(e: Event) {
  store.setStartPackage(props.id, (e.target as HTMLInputElement).value)
  refreshFlow()
}

watch(
  () => [props.data.inputs.length, props.data.outputs.length, props.data.startKind],
  () => { refreshHandles() }
)
</script>

<template>
  <div
    class="pf-node"
    :class="{
      selected,
      popup: isPopup,
      start: isStart,
      end: isEnd,
    }"
    :style="{ '--accent': accent }"
  >
    <div class="pf-header">
      <span class="pf-icon">{{ icon }}</span>
      <input
        class="pf-title nodrag"
        :value="data.label"
        @change="onRename"
        @mousedown.stop
      />
    </div>

    <!-- Start: app vs page -->
    <div v-if="isStart" class="pf-kind nodrag" @mousedown.stop>
      <button
        type="button"
        class="kind-btn"
        :class="{ active: startKind === 'app' }"
        @click.stop="onStartKind('app')"
      >
        启动 App
      </button>
      <button
        type="button"
        class="kind-btn"
        :class="{ active: startKind === 'page' }"
        @click.stop="onStartKind('page')"
      >
        页面
      </button>
    </div>

    <div v-if="isStart && startKind === 'app'" class="pf-pkg nodrag" @mousedown.stop>
      <label>包名</label>
      <input
        class="pkg-input"
        :value="data.packageName"
        placeholder="com.example.app"
        @change="onPackageChange"
      />
    </div>

    <div class="pf-sub">
      <template v-if="isStart && startKind === 'app'">
        无入口 · 从「启动」连到页面入口
      </template>
      <template v-else-if="isStart && startKind === 'page'">
        无入口 · 流程从本页开始
        <span v-if="data.linkedPageName"> · 关联 {{ data.linkedPageName }}</span>
      </template>
      <template v-else-if="isEnd">
        无输出 · 接收 navigation / popup_close
      </template>
      <template v-else-if="isPopup && !data.canCreateOutput">需要先连接触发</template>
      <template v-else-if="data.linkedPageName">
        关联: {{ data.linkedPageName }} · 已选 {{ data.outputs.filter(o => o.el).length }} 个元素
      </template>
      <template v-else>
        {{ data.outputs.filter(o => o.el).length }} 个元素 · 右键关联页面后添加
      </template>
    </div>

    <div
      v-for="port in data.inputs"
      :key="'in-' + port.slot_index"
      class="pf-row in"
    >
      <Handle
        :id="'in-' + port.slot_index"
        type="target"
        :position="Position.Left"
        :connectable="MULTI_IN_PORT_TYPES.has(port.type) ? true : 1"
        class="pf-handle target"
        :style="{ background: portHandleColor(port.type) }"
      />
      <span class="pf-port-name">{{ port.name }}</span>
      <span class="pf-port-type">{{ port.type }}</span>
      <span v-if="(port.links?.length || 0) > 0" class="pf-in-count">
        ×{{ port.links.length }}
      </span>
    </div>

    <div
      v-for="port in data.outputs"
      :key="'out-' + port.slot_index"
      class="pf-row out"
    >
      <span class="pf-port-name">
        {{ ELEMENT_ICONS[port.el?.type || ''] || (isStart && !port.el ? '▶' : '◆') }} {{ port.name }}
      </span>
      <span
        class="pf-port-type nodrag"
        :title="isStart && startKind === 'app' ? '启动输出固定为 navigation' : '双击切换 navigation ↔ popup_fixed'"
        @dblclick.stop="onTogglePortType(port.slot_index)"
      >
        {{ port.type }}
      </span>
      <div v-if="port.el" class="pf-actions nodrag">
        <button type="button" title="添加到用例·点击" @click.stop="onAddToCase(port.slot_index, 'click')">👆</button>
        <button type="button" title="添加到用例·等待" @click.stop="onAddToCase(port.slot_index, 'wait')">⏳</button>
        <button type="button" title="移除" @click.stop="onRemovePort(port.slot_index)">×</button>
      </div>
      <Handle
        :id="'out-' + port.slot_index"
        type="source"
        :position="Position.Right"
        :connectable="true"
        class="pf-handle source"
        :style="{ background: portHandleColor(port.type) }"
      />
    </div>

    <div v-if="isEnd && data.inputs.length === 0" class="pf-empty-end">
      （终节点）
    </div>

    <button
      v-if="data.canCreateOutput"
      type="button"
      class="pf-add nodrag"
      @click.stop="onAddElement"
      @mousedown.stop
    >
      + 添加元素
    </button>
  </div>
</template>

<style scoped>
.pf-node {
  min-width: 228px;
  background: var(--ac-paper, #fffbf5);
  border: 2px solid var(--ac-border, rgba(139, 115, 85, 0.16));
  border-left: 5px solid var(--accent);
  border-radius: 16px;
  padding: 10px 12px 12px;
  font-family: var(--ac-font, inherit);
  color: var(--ac-ink, #4a3a28);
  box-shadow: 0 4px 14px rgba(139, 115, 85, 0.12);
}
.pf-node.selected {
  border-color: var(--ac-teal, #19c8b9);
  box-shadow: 0 0 0 3px rgba(25, 200, 185, 0.22), 0 6px 18px rgba(139, 115, 85, 0.12);
}
.pf-node.popup {
  border-style: dashed;
}
.pf-node.start {
  min-width: 240px;
  border-radius: 16px 16px 16px 28px;
}
.pf-node.end {
  min-width: 180px;
  border-radius: 16px 28px 16px 16px;
  opacity: 0.96;
}
.pf-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}
.pf-icon {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: rgba(247, 205, 103, 0.35);
  font-size: 13px;
}
.pf-node.start .pf-icon {
  background: rgba(111, 186, 44, 0.28);
  color: #3d7a12;
}
.pf-node.end .pf-icon {
  background: rgba(138, 138, 150, 0.28);
}
.pf-title {
  flex: 1;
  min-width: 0;
  background: transparent;
  border: 2px solid transparent;
  border-radius: 8px;
  color: var(--ac-ink, #4a3a28);
  font-size: 13px;
  font-weight: 800;
  padding: 2px 6px;
  outline: none;
  font-family: inherit;
}
.pf-title:focus {
  border-color: var(--ac-teal, #19c8b9);
  background: var(--ac-cream, #fdf8f0);
}
.pf-kind {
  display: flex;
  gap: 4px;
  margin: 6px 0 4px;
  padding: 3px;
  background: var(--ac-cream-deep, #f3eadc);
  border-radius: 999px;
  border: 1px solid var(--ac-border-soft, rgba(139, 115, 85, 0.1));
}
.kind-btn {
  flex: 1;
  border: none;
  border-radius: 999px;
  padding: 5px 8px;
  font-size: 11px;
  font-weight: 800;
  font-family: inherit;
  background: transparent;
  color: var(--ac-ink-faint, #988b7a);
  cursor: pointer;
}
.kind-btn.active {
  background: #fff;
  color: #3d7a12;
  box-shadow: 0 1px 4px rgba(74, 58, 40, 0.12);
}
.pf-pkg {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  padding: 0 2px;
}
.pf-pkg label {
  font-size: 10px;
  font-weight: 800;
  color: var(--ac-ink-faint, #988b7a);
  flex-shrink: 0;
}
.pkg-input {
  flex: 1;
  min-width: 0;
  padding: 4px 8px;
  border: 1px solid var(--ac-border, rgba(139, 115, 85, 0.16));
  border-radius: 8px;
  background: var(--ac-cream, #fdf8f0);
  color: var(--ac-ink, #4a3a28);
  font-size: 10px;
  font-family: ui-monospace, monospace;
  outline: none;
}
.pkg-input:focus {
  border-color: #6fba2c;
}
.pf-sub {
  font-size: 10px;
  color: var(--ac-ink-faint, #988b7a);
  margin-bottom: 8px;
  padding-left: 4px;
  line-height: 1.4;
  font-weight: 600;
}
.pf-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  padding: 3px 0;
  margin: 2px 0;
  font-size: 11px;
}
.pf-row.in { justify-content: flex-start; }
.pf-row.out { justify-content: flex-end; }
.pf-port-name { color: var(--ac-ink-muted, #5c4a35); font-weight: 600; }
.pf-port-type {
  font-size: 9px;
  color: var(--ac-ink-faint, #988b7a);
  border: 1px solid var(--ac-border, rgba(139,115,85,0.16));
  border-radius: 6px;
  padding: 0 5px;
  cursor: help;
  user-select: none;
  background: var(--ac-cream, #fdf8f0);
}
.pf-in-count {
  font-size: 10px;
  font-weight: 800;
  color: #4a6ad4;
  background: rgba(136, 157, 240, 0.2);
  border-radius: 8px;
  padding: 0 6px;
  line-height: 16px;
}
.pf-actions {
  display: flex;
  gap: 3px;
  flex-shrink: 0;
}
.pf-actions button {
  background: var(--ac-cream, #fdf8f0);
  border: 1px solid var(--ac-border, rgba(139,115,85,0.16));
  border-radius: 8px;
  color: var(--ac-ink-muted, #5c4a35);
  font-size: 11px;
  cursor: pointer;
  padding: 0 5px;
  line-height: 18px;
}
.pf-actions button:hover {
  border-color: var(--ac-teal, #19c8b9);
  color: #0d7a70;
}

.pf-handle {
  width: 12px !important;
  height: 12px !important;
  border: 2px solid #fff !important;
  border-radius: 50% !important;
  position: relative !important;
  top: auto !important;
  left: auto !important;
  right: auto !important;
  transform: none !important;
  flex-shrink: 0;
  box-shadow: 0 0 0 1px rgba(139, 115, 85, 0.2);
}
.pf-handle.target { margin-right: 2px; order: -1; }
.pf-handle.source { margin-left: 2px; }
.pf-handle:hover {
  box-shadow: 0 0 0 4px rgba(25, 200, 185, 0.28);
}

.pf-empty-end {
  font-size: 11px;
  color: var(--ac-ink-faint);
  text-align: center;
  padding: 8px 0 4px;
  font-weight: 700;
}

.pf-add {
  width: 100%;
  margin-top: 8px;
  padding: 7px;
  border: 2px dashed var(--ac-border, rgba(139,115,85,0.2));
  border-radius: 12px;
  background: rgba(25, 200, 185, 0.06);
  color: var(--ac-ink-muted, #5c4a35);
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
}
.pf-add:hover {
  border-color: var(--ac-teal, #19c8b9);
  color: #0d7a70;
  background: rgba(25, 200, 185, 0.12);
}
</style>
