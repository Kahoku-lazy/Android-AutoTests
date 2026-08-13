<script setup>
import CaseList from "../CaseList.vue";
import { listStorageDefinitions, deleteStorageDefinition, getStorageDefinition } from "../../api/storage";

defineProps({ treeData: Array, activeDirectoryId: null, activeDirName: String, activeCaseId: null });
defineEmits(["refresh-tree", "clear-case", "select-case", "go-all"]);

const api = { listDefs: listStorageDefinitions, deleteDef: deleteStorageDefinition, getDef: getStorageDefinition };

const columns = [
  { title: "ID", dataIndex: "id", minWidth: 200 },
  { title: "标题", dataIndex: "title", minWidth: 180 },
  { title: "目录", dataIndex: "directory_name", minWidth: 140 },
  { title: "分类", dataIndex: "category", minWidth: 100 },
  { title: "优先级", dataIndex: "priority", minWidth: 86, align: "center" },
  { title: "步骤摘要", dataIndex: "steps", minWidth: 160 },
  { title: "预期结果", dataIndex: "expected_result", minWidth: 160 },
  { title: "启用", dataIndex: "enabled", minWidth: 86, align: "center" },
  { title: "操作", dataIndex: "actions", minWidth: 180, align: "center" },
];

function editPath(id) { return `/cases/storage/${id}/edit`; }

function previewText(val, max = 80) {
  const s = String(val || "").replace(/\s+/g, " ").trim();
  if (!s) return "—";
  return s.length > max ? s.slice(0, max) + "…" : s;
}
</script>

<template>
  <CaseList case-type="storage" :list-api="api" :columns="columns" create-path="/cases/storage/new" :edit-path="editPath"
    :tree-data="treeData" :active-directory-id="activeDirectoryId" :active-dir-name="activeDirName"
    :active-case-id="activeCaseId"
    @refresh-tree="$emit('refresh-tree')"
    @clear-case="$emit('clear-case')"
    @select-case="$emit('select-case', $event)"
    @go-all="$emit('go-all')">
    <template #cell-steps="{ value }">
      <span :title="String(value || '')">{{ previewText(value) }}</span>
    </template>
    <template #cell-expected_result="{ value }">
      <span :title="String(value || '')">{{ previewText(value) }}</span>
    </template>
    <template #detail="{ case: c }">
      <div class="storage-detail">
        <div class="storage-detail__row"><strong>前置条件</strong><pre>{{ c.precondition || '—' }}</pre></div>
        <div class="storage-detail__row"><strong>步骤</strong><pre>{{ c.steps || '—' }}</pre></div>
        <div class="storage-detail__row"><strong>预期结果</strong><pre>{{ c.expected_result || '—' }}</pre></div>
      </div>
    </template>
  </CaseList>
</template>

<style scoped>
.storage-detail{display:flex;flex-direction:column;gap:10px;margin-top:8px}
.storage-detail__row strong{display:block;font-size:var(--app-size-xs);margin-bottom:4px}
.storage-detail__row pre{
  margin:0;white-space:pre-wrap;word-break:break-word;
  font-family:var(--app-font-mono);font-size:var(--app-size-xs);
  background:var(--app-bg-muted,#f7f7f7);padding:8px;border-radius:6px;border:1px solid var(--ink);
}
</style>
