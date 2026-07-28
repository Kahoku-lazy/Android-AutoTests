<script setup>
import CaseList from "../CaseList.vue";
import { listWebDefinitions, deleteWebDefinition, getWebDefinition } from "../../api/webAutomation.js";

defineProps({ treeData: Array, activeDirectoryId: null, activeDirName: String, activeCaseId: null });
defineEmits(["refresh-tree"]);

const api = { listDefs: listWebDefinitions, deleteDef: deleteWebDefinition, getDef: getWebDefinition };

const columns = [
  { title: "ID", dataIndex: "id", minWidth: 220 },
  { title: "标题", dataIndex: "title", minWidth: 200 },
  { title: "URL", dataIndex: "url", minWidth: 200 },
  { title: "优先级", dataIndex: "priority", minWidth: 86, align: "center" },
  { title: "启用", dataIndex: "enabled", minWidth: 86, align: "center" },
  { title: "操作", dataIndex: "actions", minWidth: 180, align: "center" },
];

function editPath(id) { return `/cases/web/${id}/edit`; }
</script>

<template>
  <CaseList case-type="web" :list-api="api" :columns="columns" create-path="/cases/web/new" :edit-path="editPath"
    :tree-data="treeData" :active-directory-id="activeDirectoryId" :active-dir-name="activeDirName"
    :active-case-id="activeCaseId"
    @refresh-tree="$emit('refresh-tree')" />
</template>
