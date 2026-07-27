<script setup>
import { ref } from "vue";
import CaseList from "../CaseList.vue";
import StepViewer from "../StepViewer.vue";
import { listDefinitions, deleteDefinition, getDefinition, listExports } from "../../api/uiAutomation.js";

const props = defineProps({ treeData: Array, activeDirectoryId: null, activeDirName: String });
const emit = defineEmits(["refresh-tree"]);

const api = { listDefs: listDefinitions, deleteDef: deleteDefinition, getDef: getDefinition };

const columns = [
  { title: "ID", dataIndex: "id", minWidth: 220 },
  { title: "标题", dataIndex: "title", minWidth: 200 },
  { title: "包名", dataIndex: "package_name", minWidth: 160 },
  { title: "优先级", dataIndex: "priority", minWidth: 86, align: "center" },
  { title: "启用", dataIndex: "enabled", minWidth: 86, align: "center" },
  { title: "操作", dataIndex: "actions", minWidth: 180, align: "center" },
];

const selectedDefinition = ref(null);
const yamlLoading = ref(false);

async function handleSelect(id) {
  try {
    const { data } = await getDefinition(id);
    if (data.ok) selectedDefinition.value = data.definition;
  } catch (_) {}
}

async function handleExportYaml() {
  yamlLoading.value = true;
  try {
    const { data } = await listExports();
    if (data.ok && data.files?.length) {
      const latest = data.files[0];
      window.open(`/api/cases/export/yaml/${latest.filename}`, "_blank");
    }
  } catch (_) {}
  yamlLoading.value = false;
}

function editPath(id) { return `/cases/${id}/edit`; }
</script>

<template>
  <CaseList ref="listRef" case-type="ui" :list-api="api" :columns="columns" create-path="/cases/new" :edit-path="editPath"
    :tree-data="props.treeData" :active-directory-id="props.activeDirectoryId" :active-dir-name="props.activeDirName"
    @refresh-tree="emit('refresh-tree')">
    <template #table-extra>
      <button class="btn-yaml" :disabled="yamlLoading" @click="handleExportYaml">📄 导出YAML</button>
    </template>
    <template #detail="{ case: c }">
      <StepViewer v-if="selectedDefinition" :case-definition="selectedDefinition" />
    </template>
    <template #cell-id="{ record }">
      <span class="case-link" @click="handleSelect(record.id)">{{ record.id }}</span>
    </template>
  </CaseList>
</template>

<style scoped>
.btn-yaml{padding:5px 12px;font-size:var(--app-size-xs);font-weight:700;color:var(--ink);background:#fff;border:2px solid var(--ink);border-radius:4px 8px 4px 8px;cursor:pointer}
.case-link{font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:600;cursor:pointer;text-decoration:underline}
</style>
