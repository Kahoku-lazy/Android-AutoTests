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

const isPopup = computed(() => props.data.nodeType === 'PopupNode')
const isStart = computed(() => props.data.nodeType === 'StartNode')
const isEnd = computed(() => props.data.nodeType === 'EndNode')
const isApi = computed(() => props.data.nodeType === 'ApiNode')
const startKind = computed<StartKind>(() => props.data.startKind || 'app')

const accent = computed(() => {
  if (isStart.value) return 'var(--c-workflow)'
  if (isEnd.value) return '#8a8a96'
  if (isPopup.value) return '#e85f5f'
  if (isApi.value) return '#f5a623'
  return '#6f9fd8'
})

const icon = computed(() => {
  if (isApi.value) return '📡'
  if (isStart.value) return '▶'
  if (isEnd.value) return '⏹'
  if (isPopup.value) return '⚠️'
  return '📱'
})

function methodColor(m?: string): string {
  const map: Record<string, string> = { GET: '#6fba2c', POST: '#889df0', PUT: '#f7cd67', DELETE: '#e85f5f', PATCH: '#b39ef3' }
  return map[m || 'GET'] || '#8b7355'
}

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
      api: isApi,
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

    <!-- Start: app / page / url / api -->
    <div v-if="isStart" class="pf-kind nodrag" @mousedown.stop>
      <button type="button" class="kind-btn" :class="{ active: startKind === 'app' }"
        @click.stop="onStartKind('app')">启动 App</button>
      <button type="button" class="kind-btn" :class="{ active: startKind === 'page' }"
        @click.stop="onStartKind('page')">页面</button>
      <button type="button" class="kind-btn" :class="{ active: startKind === 'url' }"
        @click.stop="onStartKind('url')">URL</button>
      <button type="button" class="kind-btn" :class="{ active: startKind === 'api' }"
        @click.stop="onStartKind('api')">API</button>
    </div>

    <div v-if="isStart && startKind === 'app'" class="pf-pkg nodrag" @mousedown.stop>
      <label>包名</label>
      <input class="pkg-input" :value="data.packageName" placeholder="com.example.app" @change="onPackageChange" />
    </div>
    <div v-if="isStart && startKind === 'url'" class="pf-pkg nodrag" @mousedown.stop>
      <label>URL</label>
      <input class="pkg-input" :value="data.startUrl" placeholder="https://example.com" @change="(e) => { store.setStartUrl(props.id, (e.target as HTMLInputElement).value); refreshFlow() }" />
    </div>
    <div v-if="isStart && startKind === 'api'" class="pf-pkg nodrag" @mousedown.stop>
      <label>API 地址</label>
      <input class="pkg-input" :value="data.startApi" placeholder="http://localhost/api/endpoint" @change="(e) => { store.setStartApi(props.id, (e.target as HTMLInputElement).value); refreshFlow() }" />
    </div>

    <!-- API Node: method badge + URL -->
    <div v-if="data.isApiNode" class="pf-api nodrag" @mousedown.stop>
      <span class="api-method" :style="{background: methodColor(data.apiMethod)}">{{ data.apiMethod }}</span>
      <span class="api-url">{{ data.apiUrl }}</span>
    </div>

    <div class="pf-sub">
      <template v-if="isStart && startKind === 'app'">
        无入口 · 从「启动」连到页面入口
      </template>
      <template v-else-if="isStart && (startKind === 'page' || startKind === 'url' || startKind === 'api')">
        <template v-if="data.linkedPageName">
          关联: {{ data.linkedPageName }} · 已选 {{ data.outputs.filter(o => o.el).length }} 个元素
        </template>
        <template v-else>
          无入口 · 右键关联页面后添加元素
        </template>
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
  background: var(--app-bg-card);
  border: 2px solid var(--ink);
  border-left: 4px solid var(--accent);
  border-radius: var(--app-radius-md);
  padding: 11px 13px 13px;
  font-family: var(--app-font);
  color: var(--ink);
  box-shadow: var(--app-shadow-sm);
}
.pf-node.selected {
  border-color: var(--c-workflow);
  box-shadow: 0 0 0 3px rgba(137, 207, 240, 0.28), var(--app-shadow-md);
}
.pf-node.popup {
  border-style: dashed;
}
.pf-node.start {
  min-width: 240px;
}
.pf-node.end {
  min-width: 180px;
  opacity: 0.96;
}
.pf-node.api {
  min-width: 240px;
  box-shadow: 0 0 8px rgba(245, 166, 35, 0.16);
}
.pf-api {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: rgba(245, 166, 35, 0.08);
  border-radius: 8px;
  margin-bottom: 4px;
}
.api-method {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: var(--app-size-xs);
  font-weight: 800;
  color: #fff;
  flex-shrink: 0;
}
.api-url {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--app-font-mono);
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
  border-radius: 8px;
  background: var(--app-bg-subtle);
  font-size: var(--app-size-sm);
}
.pf-title {
  flex: 1;
  min-width: 0;
  background: transparent;
  border: 2px solid transparent;
  border-radius: 8px;
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: 800;
  padding: 2px 6px;
  outline: none;
  font-family: inherit;
}
.pf-title:focus {
  border-color: var(--c-workflow);
  background: var(--ac-accent-soft);
}
.pf-kind {
  display: flex;
  gap: 4px;
  margin: 6px 0 4px;
  padding: 3px;
  background: var(--app-bg-subtle);
  border-radius: 8px;
  border: 1px solid var(--ac-border-soft);
}
.kind-btn {
  flex: 1;
  border: none;
  border-radius: 6px;
  padding: 5px 8px;
  font-size: var(--app-size-xs);
  font-weight: 700;
  font-family: inherit;
  background: transparent;
  color: var(--app-text-secondary);
  cursor: pointer;
  transition: background 0.12s var(--app-ease), color 0.12s var(--app-ease);
}
.kind-btn.active {
  background: var(--app-bg-card);
  color: var(--ink);
  box-shadow: var(--app-shadow-sm);
}
.kind-btn:focus-visible {
  outline: 2px solid var(--c-workflow);
  outline-offset: 1px;
}
.pf-pkg {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  padding: 0 2px;
}
.pf-pkg label {
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--app-text-secondary);
  flex-shrink: 0;
}
.pkg-input {
  flex: 1;
  min-width: 0;
  padding: 5px 9px;
  border: 1.5px solid var(--ink);
  border-radius: 8px;
  background: var(--app-bg-card);
  color: var(--ink);
  font-size: var(--app-size-xs);
  font-family: var(--app-font-mono);
  outline: none;
  transition: border-color 0.12s var(--app-ease);
}
.pkg-input:focus {
  border-color: var(--c-workflow);
}
.pf-sub {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  margin-bottom: 8px;
  padding-left: 4px;
  line-height: 1.5;
  font-weight: 600;
}
.pf-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  padding: 3px 0;
  margin: 2px 0;
  font-size: var(--app-size-xs);
}
.pf-row.in { justify-content: flex-start; }
.pf-row.out { justify-content: flex-end; }
.pf-port-name { color: var(--ink); font-weight: 600; }
.pf-port-type {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  border: 1px solid var(--ink);
  border-radius: 6px;
  padding: 0 5px;
  cursor: help;
  user-select: none;
  background: var(--app-bg-card);
}
.pf-in-count {
  font-size: var(--app-size-xs);
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
  background: var(--app-bg-card);
  border: 1px solid var(--ink);
  border-radius: 8px;
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
  cursor: pointer;
  padding: 0 5px;
  line-height: 18px;
}
.pf-actions button:hover {
  border-color: var(--c-workflow);
  color: var(--ink);
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
  box-shadow: 0 0 0 1px rgba(162, 210, 255, 0.3);
}
.pf-handle.target { margin-right: 2px; order: -1; }
.pf-handle.source { margin-left: 2px; }
.pf-handle:hover {
  box-shadow: 0 0 0 4px rgba(162, 210, 255, 0.3);
}

.pf-empty-end {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  text-align: center;
  padding: 8px 0 4px;
  font-weight: 600;
}

.pf-add {
  width: 100%;
  margin-top: 8px;
  padding: 7px;
  border: 2px dashed var(--ink);
  border-radius: 8px;
  background: var(--ac-accent-soft);
  color: var(--ac-accent-deep);
  font-size: var(--app-size-sm);
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.12s var(--app-ease);
}
.pf-add:hover {
  border-color: var(--c-workflow);
}
.pf-add:focus-visible {
  outline: 2px solid var(--c-workflow);
  outline-offset: 1px;
}
</style>
