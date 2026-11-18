<script setup lang="ts">
/** Knowledge Search — 知识库：左栏勾选模块（可多选），右栏提问返回检索原文。 */
import { onMounted, ref } from "vue"
import { ElMessage } from "element-plus"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import { useAuthUser } from "@/shared/composables/useAuthUser"
import ModulePanel from "./components/ModulePanel.vue"
import QueryPanel from "./components/QueryPanel.vue"
import { useKnowledgeModules } from "./composables/useKnowledgeModules"
import { KS_INDEX_DONE, KS_INDEX_FAILED, KS_PAGE_ICON, KS_PAGE_TITLE } from "./constants"
import type { KnowledgeModuleRow, ModulePayload } from "./types"

const { isSuperuser } = useAuthUser()
const {
  modules,
  loading,
  error,
  selected,
  load,
  toggleSelect,
  save,
  remove,
  toggleEnabled,
  rebuildIndex,
} = useKnowledgeModules()

const panelRef = ref<InstanceType<typeof ModulePanel> | null>(null)

onMounted(() => void load())

async function onSave(payload: ModulePayload, id?: number) {
  const result = await save(payload, id)
  if (result.ok) {
    panelRef.value?.closeDialog()
    ElMessage.success("模块已保存")
  } else {
    ElMessage.error(result.message)
  }
}

async function onRemove(id: number) {
  const result = await remove(id)
  if (result.ok) ElMessage.success("模块已删除")
  else ElMessage.error(result.message)
}

async function onToggleEnabled(row: KnowledgeModuleRow) {
  const result = await toggleEnabled(row)
  if (!result.ok) ElMessage.error(result.message)
}

async function onIndex(id: number) {
  const result = await rebuildIndex(id)
  if (result.ok) {
    ElMessage.success(`${KS_INDEX_DONE}：重建 ${result.outcome?.reindexed ?? 0} 个文件`)
  } else {
    ElMessage.error(`${KS_INDEX_FAILED}：${result.message}`)
  }
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell knowledge-search-workbench">
    <WorkbenchHeader
      :title="KS_PAGE_TITLE"
      :icon="KS_PAGE_ICON"
      icon-gradient="linear-gradient(135deg,var(--c-case),var(--app-status-purple))"
    />

    <div class="doc-body">
      <div class="ks-split" data-testid="knowledge-search-page">
        <ModulePanel
          ref="panelRef"
          :modules="modules"
          :loading="loading"
          :error="error"
          :selected="selected"
          :can-manage="isSuperuser"
          @toggle-select="toggleSelect"
          @refresh="load"
          @save="onSave"
          @remove="onRemove"
          @toggle-enabled="onToggleEnabled"
          @index="onIndex"
        />
        <QueryPanel :selected-names="selected" />
      </div>
    </div>
  </div>
</template>

<style src="./index.style.css" scoped></style>
