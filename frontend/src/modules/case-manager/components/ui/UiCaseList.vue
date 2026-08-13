<script setup>
import { ref } from "vue";
import { ElMessage } from "element-plus";
import CaseList from "../CaseList.vue";
import StepViewer from "../StepViewer.vue";
import { listDefinitions, deleteDefinition, getDefinition, listExports } from "../../api/uiAutomation";

const props = defineProps({ treeData: Array, activeDirectoryId: null, activeDirName: String, activeCaseId: null });
const emit = defineEmits(["refresh-tree", "clear-case", "select-case", "go-all"]);

const api = { listDefs: listDefinitions, deleteDef: deleteDefinition, getDef: getDefinition };

const columns = [
  { title: "ID", dataIndex: "id", minWidth: 220 },
  { title: "标题", dataIndex: "title", minWidth: 200 },
  { title: "包名", dataIndex: "package_name", minWidth: 160 },
  { title: "优先级", dataIndex: "priority", minWidth: 86, align: "center" },
  { title: "启用", dataIndex: "enabled", minWidth: 86, align: "center" },
  { title: "操作", dataIndex: "actions", minWidth: 180, align: "center" },
];

const listRef = ref(null);
const yamlLoading = ref(false);

function handleSelect(id) {
  listRef.value?.loadCaseDetail(id);
}

async function handleExportYaml() {
  yamlLoading.value = true;
  try {
    const { data } = await listExports();
    if (data.status && data.files?.length) {
      const latest = data.files[0];
      window.open(`/api/cases/exports/${latest.filename}`, "_blank");
    } else {
      ElMessage.warning("暂无导出文件，请先生成 YAML");
    }
  } catch (_) {
    ElMessage.error("获取导出列表失败");
  }
  yamlLoading.value = false;
}

function editPath(id) { return `/cases/${id}/edit`; }
</script>

<template>
  <CaseList ref="listRef" case-type="ui" :list-api="api" :columns="columns" create-path="/cases/new" :edit-path="editPath"
    :tree-data="props.treeData" :active-directory-id="props.activeDirectoryId" :active-dir-name="props.activeDirName"
    :active-case-id="props.activeCaseId"
    @refresh-tree="emit('refresh-tree')"
    @clear-case="emit('clear-case')"
    @select-case="(id) => emit('select-case', id)"
    @go-all="emit('go-all')">
    <template #table-extra>
      <button class="btn-yaml" :disabled="yamlLoading" @click="handleExportYaml">📄 导出YAML</button>
    </template>
    <template #detail="{ case: c }">
      <StepViewer v-if="c" :steps="c.steps_data || []" />
    </template>
    <template #cell-id="{ record }">
      <button class="case-link case-link-btn" @click="handleSelect(record.id)">{{ record.id }}</button>
    </template>
  </CaseList>
</template>

<style scoped>
.btn-yaml{padding:5px 12px;font-size:var(--app-size-xs);font-weight:700;color:var(--ink);background:var(--app-bg-card);border:2px solid var(--ink);border-radius:var(--app-radius-sm);cursor:pointer}
.case-link{font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:600;cursor:pointer;text-decoration:underline}.case-link-btn{background:none;border:none;padding:0;color:inherit}
</style>
