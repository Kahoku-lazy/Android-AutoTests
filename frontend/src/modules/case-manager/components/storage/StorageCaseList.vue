<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElTag } from "element-plus";
import ConfirmButton from "@/shared/components/patterns/ConfirmButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import AppTable from "@/shared/components/AppTable.vue";
import { listStorageDefinitions, deleteStorageDefinition } from "../../api/storage.js";

const props = defineProps({
  treeData: { type: Array, default: () => [] },
  activeDirectoryId: { default: null },
  activeDirName: { type: String, default: "" },
});
const emit = defineEmits(["refresh-tree"]);

const router = useRouter();
const definitions = ref([]);
const loading = ref(false);
const viewMode = ref(localStorage.getItem("case-manager-view-mode") || "card");

function setViewMode(mode) { viewMode.value = mode; localStorage.setItem("case-manager-view-mode", mode); }

let refreshTimer = null;
onMounted(() => { loadDefs(); refreshTimer = setInterval(loadDefs, 30000); });
onUnmounted(() => clearInterval(refreshTimer));

async function loadDefs() {
  loading.value = true;
  try {
    const { data } = await listStorageDefinitions(props.activeDirectoryId);
    if (data.ok) definitions.value = data.definitions;
  } catch (_) {}
  loading.value = false;
}

const breadcrumbPath = computed(() => {
  if (!props.activeDirectoryId) return [];
  const parts = [];
  function find(node, id) {
    if (node.id === id) return [node];
    if (node.children) for (const c of node.children) { const f = find(c, id); if (f) return [node, ...f]; }
    return null;
  }
  for (const root of props.treeData) { const f = find(root, props.activeDirectoryId); if (f) { parts.push(...f); break; } }
  if (parts.length === 0 && props.activeDirName) parts.push({ id: props.activeDirectoryId, name: props.activeDirName, parent_id: 1 });
  return parts;
});

const columns = [
  { title: "ID", dataIndex: "id", minWidth: 220 },
  { title: "标题", dataIndex: "title", minWidth: 220 },
  { title: "目录", dataIndex: "directory_name", minWidth: 160 },
  { title: "分类", dataIndex: "category", minWidth: 120 },
  { title: "优先级", dataIndex: "priority", minWidth: 86, align: "center" },
  { title: "启用", dataIndex: "enabled", minWidth: 86, align: "center" },
  { title: "操作", dataIndex: "actions", minWidth: 180, align: "center" },
];

function createCase() {
  router.push({ path: "/cases/storage/new", query: props.activeDirectoryId ? { directory_id: props.activeDirectoryId } : {} });
}
function editCase(row) { router.push(`/cases/storage/${row.id}/edit`); }
async function doRemove(row) {
  try {
    await deleteStorageDefinition(row.id);
    ElMessage.success("已删除");
    loadDefs(); emit("refresh-tree");
  } catch (e) {
    ElMessage.error("删除失败: " + (e?.response?.data?.error || e?.message || "网络错误"));
  }
}

function goToAll() { emit("refresh-tree"); loadDefs(); }

defineExpose({ loadDefs, definitions });
</script>

<template>
  <div class="case-toolbar">
    <div class="case-toolbar__left">
      <nav class="case-breadcrumb">
        <button class="crumb crumb--root" :class="{ 'crumb--active': activeDirectoryId === null }" @click="goToAll">
          <span class="crumb__icon">🗄️</span><span class="crumb__label">全部存储用例</span>
        </button>
        <template v-for="node in breadcrumbPath" :key="node.id">
          <span class="crumb-sep">›</span>
          <span class="crumb crumb--active crumb--dir">
            <span class="crumb__icon">{{ node.parent_id === null ? "📁" : "📂" }}</span>
            <span class="crumb__label">{{ node.name }}</span>
          </span>
        </template>
      </nav>
      <span class="case-count-badge">{{ definitions.length }} 个用例</span>
    </div>
    <div class="case-toolbar__right">
      <div class="view-toggle">
        <button :class="{ active: viewMode === 'card' }" @click="setViewMode('card')">▦</button>
        <button :class="{ active: viewMode === 'list' }" @click="setViewMode('list')">☰</button>
      </div>
      <button class="btn-primary" @click="createCase">+ 新建存储用例</button>
    </div>
  </div>

  <div v-if="loading" class="case-loading">加载中...</div>
  <div v-else-if="viewMode === 'card'" class="card-grid">
    <AppCard v-for="item in definitions" :key="item.id" class="storage-card">
      <div class="storage-card__header">
        <code class="storage-card__id">{{ item.id }}</code>
        <el-tag :type="item.enabled ? 'success' : 'info'" size="small">{{ item.enabled ? '启用' : '禁用' }}</el-tag>
        <span class="storage-card__priority">{{ item.priority }}</span>
      </div>
      <h3 class="storage-card__title">{{ item.title }}</h3>
      <p v-if="item.description" class="storage-card__desc">{{ item.description }}</p>
      <div class="storage-card__meta">
        <span v-if="item.category">分类：{{ item.category }}</span>
        <span v-if="item.directory_name">目录：{{ item.directory_name }}</span>
        <span>{{ item.operations?.length || 0 }} 个操作</span>
      </div>
      <div class="storage-card__actions">
        <button class="btn-text" @click="editCase(item)">编辑</button>
        <ConfirmButton size="small" type="danger" plain @confirm="doRemove(item)">删除</ConfirmButton>
      </div>
    </AppCard>
  </div>
  <AppCard v-else>
    <AppTable :columns="columns" :data-source="definitions" row-key="id" :striped="true" :loading="loading" empty-text="暂无存储业务用例">
      <template #cell-id="{ value }"><code>{{ value }}</code></template>
      <template #cell-title="{ record }"><span class="case-link">{{ record.title }}</span></template>
      <template #cell-enabled="{ value }">
        <el-tag :type="value ? 'success' : 'info'" size="small">{{ value ? '启用' : '禁用' }}</el-tag>
      </template>
      <template #cell-actions="{ record }">
        <button class="btn-text" @click="editCase(record)">编辑</button>
        <ConfirmButton size="small" type="danger" plain @confirm="doRemove(record)">删除</ConfirmButton>
      </template>
    </AppTable>
  </AppCard>
</template>

<style scoped>
.case-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 0 0 16px 0; flex-wrap: wrap; gap: 8px; }
.case-toolbar__left { display: flex; align-items: center; gap: 12px; }
.case-toolbar__right { display: flex; align-items: center; gap: 8px; }
.case-breadcrumb { display: flex; align-items: center; gap: 4px; }
.crumb { background: none; border: none; cursor: pointer; padding: 4px 8px; border-radius: 6px; font-size: 13px; }
.crumb--active { font-weight: 600; color: var(--animal-primary-color, #6fba2c); }
.crumb-sep { color: #999; font-size: 14px; }
.case-count-badge { font-size: 12px; color: #999; background: #f0f0f0; padding: 2px 10px; border-radius: 12px; }
.view-toggle { display: flex; border: 1px solid #e0e0e0; border-radius: 6px; overflow: hidden; }
.view-toggle button { border: none; background: #fff; padding: 4px 10px; cursor: pointer; font-size: 14px; }
.view-toggle button.active { background: var(--animal-primary-color, #6fba2c); color: #fff; }
.btn-primary, .btn-text { padding: 6px 16px; border-radius: 8px; border: 1px solid #e0e0e0; background: #fff; cursor: pointer; font-size: 13px; }
.btn-primary { background: var(--animal-primary-color, #6fba2c); color: #fff; border-color: var(--animal-primary-color, #6fba2c); }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.storage-card__header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.storage-card__id { font-size: 11px; color: #999; }
.storage-card__title { margin: 0 0 8px 0; font-size: 16px; }
.storage-card__desc { font-size: 13px; color: #666; margin-bottom: 8px; }
.storage-card__meta { display: flex; gap: 12px; font-size: 12px; color: #999; margin-bottom: 8px; }
.storage-card__actions { display: flex; gap: 8px; }
</style>
