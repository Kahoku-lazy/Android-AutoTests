<script setup lang="ts">
import { ref } from "vue"
import AppCard from "@/shared/components/AppCard.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import ConfirmButton from "@/shared/components/patterns/ConfirmButton.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { KS_DELETE_MESSAGE, KS_MANAGE_HINT } from "../constants"
import type { KnowledgeModuleRow, ModulePayload } from "../types"
import ModuleFormDialog from "./ModuleFormDialog.vue"
import RetrievalSettingsCard from "./RetrievalSettingsCard.vue"

defineProps<{
  modules: KnowledgeModuleRow[]
  loading: boolean
  error: string
  selected: string[]
  canManage: boolean
}>()

const emit = defineEmits<{
  "toggle-select": [name: string]
  "refresh": []
  "save": [payload: ModulePayload, id?: number]
  "remove": [id: number]
  "toggle-enabled": [row: KnowledgeModuleRow]
  "index": [id: number]
}>()

const dialogOpen = ref(false)
const editing = ref<KnowledgeModuleRow | null>(null)

function openCreate() {
  editing.value = null
  dialogOpen.value = true
}

function openEdit(row: KnowledgeModuleRow) {
  editing.value = row
  dialogOpen.value = true
}

function onSave(payload: ModulePayload, id?: number) {
  emit("save", payload, id)
}

function closeDialog() {
  dialogOpen.value = false
}

defineExpose({ closeDialog })
</script>

<template>
  <div class="ks-module-column">
    <RetrievalSettingsCard v-if="canManage" />
    <AppCard tone="var(--c-case)" :pin="false" :tilt="0.3" class="ks-module-panel">
      <template #header>
        <div class="ks-module-panel__head">
          <span class="ks-module-panel__title">知识模块</span>
          <DoodleBtn v-if="canManage" tone="teal" @click="openCreate">新增</DoodleBtn>
        </div>
      </template>

      <SkeletonCard v-if="loading" variant="list" :lines="4" />
      <ErrorState v-else-if="error" :message="error" @retry="emit('refresh')" />
      <EmptyState
        v-else-if="modules.length === 0"
        icon="📚"
        text="暂无模块"
        :hint="canManage ? '点「新增」登记一个资料目录' : KS_MANAGE_HINT"
      />
      <ul v-else class="ks-module-panel__list">
        <li v-for="row in modules" :key="row.id" class="ks-module">
          <div class="ks-module__row">
            <el-checkbox
              :model-value="selected.includes(row.name)"
              :disabled="!row.enabled"
              @update:model-value="emit('toggle-select', row.name)"
            >
              <span class="ks-module__name">{{ row.name }}</span>
            </el-checkbox>
            <span class="ks-module__state" :class="{ 'is-off': !row.enabled }">
              {{ row.enabled ? "启用" : "禁用" }}
            </span>
          </div>
          <p class="ks-module__desc">{{ row.description }}</p>
          <p class="ks-module__dir" :title="row.data_dir">{{ row.data_dir }}</p>
          <div v-if="canManage" class="ks-module__actions">
            <DoodleBtn @click="openEdit(row)">编辑</DoodleBtn>
            <DoodleBtn @click="emit('toggle-enabled', row)">
              {{ row.enabled ? "停用" : "启用" }}
            </DoodleBtn>
            <DoodleBtn tone="teal" @click="emit('index', row.id)">预建索引</DoodleBtn>
            <ConfirmButton doodle :message="KS_DELETE_MESSAGE" @confirm="emit('remove', row.id)">
              删除
            </ConfirmButton>
          </div>
        </li>
      </ul>
      <p v-if="!canManage" class="ks-module-panel__hint">{{ KS_MANAGE_HINT }}</p>
    </AppCard>

    <ModuleFormDialog v-model="dialogOpen" :editing="editing" @save="onSave" />
  </div>
</template>

<style scoped>
.ks-module-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-sm);
}

.ks-module-panel__title {
  font-size: var(--app-size-md);
  font-weight: var(--app-font-weight-heavy);
  color: var(--app-text-primary);
}

.ks-module-panel__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}

.ks-module {
  border: 1px solid color-mix(in srgb, var(--ink) 10%, transparent);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  padding: var(--app-space-md);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
}

.ks-module__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-sm);
}

.ks-module__name {
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text-primary);
}

.ks-module__state {
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-semibold);
  color: var(--app-text-secondary);
  border: 1px solid color-mix(in srgb, var(--ink) 24%, transparent);
  border-radius: var(--app-radius-sm);
  padding: 0 var(--app-space-xs);
}

.ks-module__state.is-off {
  color: var(--app-status-danger-text);
  border-color: var(--app-status-danger);
}

.ks-module__desc {
  margin: 0;
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
}

.ks-module__dir {
  margin: 0;
  font-size: var(--app-size-xs);
  font-family: var(--app-font-mono, monospace);
  color: var(--app-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ks-module__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-sm);
  margin-top: var(--app-space-xs);
}

.ks-module-column {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
  min-width: 0;
}

.ks-module-panel__hint {
  margin: var(--app-space-md) 0 0;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
</style>
