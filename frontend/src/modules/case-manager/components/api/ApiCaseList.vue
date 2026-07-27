<script setup>
import CaseList from "../CaseList.vue";
import { listApiDefinitions, deleteApiDefinition, getApiDefinition } from "../../api/apiTesting.js";

defineProps({ treeData: Array, activeDirectoryId: null, activeDirName: String });
defineEmits(["refresh-tree"]);

const api = { listDefs: listApiDefinitions, deleteDef: deleteApiDefinition, getDef: getApiDefinition };

const columns = [
  { title: "ID", dataIndex: "id", minWidth: 220 },
  { title: "标题", dataIndex: "title", minWidth: 200 },
  { title: "方法", dataIndex: "http_method", minWidth: 86, align: "center" },
  { title: "URL", dataIndex: "url", minWidth: 220 },
  { title: "状态码", dataIndex: "expected_status", minWidth: 86, align: "center" },
  { title: "启用", dataIndex: "enabled", minWidth: 86, align: "center" },
  { title: "操作", dataIndex: "actions", minWidth: 180, align: "center" },
];

function editPath(id) { return `/cases/api/${id}/edit`; }
</script>

<template>
  <CaseList case-type="api" :list-api="api" :columns="columns" create-path="/cases/api/new" :edit-path="editPath"
    :tree-data="treeData" :active-directory-id="activeDirectoryId" :active-dir-name="activeDirName"
    @refresh-tree="$emit('refresh-tree')">
    <template #cell-http_method="{ value }">
      <span :style="{ color: { GET: '#6fba2c', POST: '#889df0', PUT: '#f7cd67', DELETE: '#e85f5f', PATCH: '#a78bfa' }[value] || 'inherit', fontWeight: 700 }">{{ value }}</span>
    </template>
  </CaseList>
</template>
