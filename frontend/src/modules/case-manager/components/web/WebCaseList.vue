<script setup>
import { ref } from "vue";
import CaseList from "../CaseList.vue";
import StepViewer from "../StepViewer.vue";
import { listWebDefinitions, deleteWebDefinition, getWebDefinition } from "../../api/webAutomation.js";

const props = defineProps({ treeData: Array, activeDirectoryId: null, activeDirName: String, activeCaseId: null });
const emit = defineEmits(["refresh-tree"]);

const api = { listDefs: listWebDefinitions, deleteDef: deleteWebDefinition, getDef: getWebDefinition };

const columns = [
  { title: "ID", dataIndex: "id", minWidth: 220 },
  { title: "标题", dataIndex: "title", minWidth: 200 },
  { title: "起始 URL", dataIndex: "url", minWidth: 200 },
  { title: "步骤数", dataIndex: "stepCount", minWidth: 72, align: "center" },
  { title: "优先级", dataIndex: "priority", minWidth: 86, align: "center" },
  { title: "启用", dataIndex: "enabled", minWidth: 86, align: "center" },
  { title: "操作", dataIndex: "actions", minWidth: 180, align: "center" },
];

const listRef = ref(null);

function handleSelect(id) {
  listRef.value?.loadCaseDetail(id);
}

function stepCount(record) {
  const raw = record?.steps_data || record?.steps_json;
  if (!raw) return 0;
  if (Array.isArray(raw)) return raw.length;
  try { return JSON.parse(raw).length; } catch { return 0; }
}

function editPath(id) { return `/cases/web/${id}/edit`; }
</script>

<template>
  <CaseList ref="listRef" case-type="web" :list-api="api" :columns="columns" create-path="/cases/web/new" :edit-path="editPath"
    :tree-data="props.treeData" :active-directory-id="props.activeDirectoryId" :active-dir-name="props.activeDirName"
    :active-case-id="props.activeCaseId"
    @refresh-tree="emit('refresh-tree')">
    <template #detail="{ case: c }">
      <StepViewer v-if="c?.steps_data?.length" :steps="c.steps_data" />
      <div v-else class="no-steps">暂无步骤 — 点击「编辑」添加 Web 自动化步骤</div>
    </template>
    <template #cell-id="{ record }">
      <span class="case-link" @click="handleSelect(record.id)">{{ record.id }}</span>
    </template>
    <template #cell-stepCount="{ record }">
      <span class="step-count-badge">{{ stepCount(record) }}</span>
    </template>
  </CaseList>
</template>

<style scoped>
.case-link{font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:600;cursor:pointer;text-decoration:underline}
.step-count-badge{display:inline-block;min-width:24px;padding:1px 8px;border-radius:10px;background:rgba(111,186,44,0.15);color:#4a8a1a;font-weight:700;font-size:var(--app-size-xs)}
.no-steps{text-align:center;padding:24px;color:#999;font-size:var(--app-size-sm)}
</style>
