<script setup>
import CaseList from "../CaseList.vue";
import { listStorageDefinitions, deleteStorageDefinition, getStorageDefinition } from "../../api/storage.js";

defineProps({ treeData: Array, activeDirectoryId: null, activeDirName: String });
defineEmits(["refresh-tree"]);

const api = { listDefs: listStorageDefinitions, deleteDef: deleteStorageDefinition, getDef: getStorageDefinition };

const columns = [
  { title: "ID", dataIndex: "id", minWidth: 220 },
  { title: "标题", dataIndex: "title", minWidth: 220 },
  { title: "目录", dataIndex: "directory_name", minWidth: 160 },
  { title: "分类", dataIndex: "category", minWidth: 120 },
  { title: "优先级", dataIndex: "priority", minWidth: 86, align: "center" },
  { title: "启用", dataIndex: "enabled", minWidth: 86, align: "center" },
  { title: "操作", dataIndex: "actions", minWidth: 180, align: "center" },
];

function editPath(id) { return `/cases/storage/${id}/edit`; }
</script>

<template>
  <CaseList case-type="storage" :list-api="api" :columns="columns" create-path="/cases/storage/new" :edit-path="editPath"
    :tree-data="treeData" :active-directory-id="activeDirectoryId" :active-dir-name="activeDirName"
    @refresh-tree="$emit('refresh-tree')" />
</template>
