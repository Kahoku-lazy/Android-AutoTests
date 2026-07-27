<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElTag } from "element-plus";
import ConfirmButton from "@/shared/components/patterns/ConfirmButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import AppTable from "@/shared/components/AppTable.vue";
import CaseCard from "./CaseCard.vue";

/**
 * 通用 CaseList — 替代 4 个 ~85% 重复的 TypeCaseList
 *
 * Props:
 *   caseType          — "ui" | "api" | "storage" | "web"
 *   listApi           — { listDefs, deleteDef, getDef }
 *   columns            — AppTable 列定义
 *   createPath         — 新建路由 path
 *   editPath(id)       — 编辑路由 path 工厂
 *   treeData / activeDirectoryId / activeDirName — 与原来一致
 *   hideCard           — 是否隐藏卡片视图（默认 false）
 *
 * Slots:
 *   #table-extra       — 表格上方额外内容（如 YAML 导出按钮）
 *   #cell-{dataIndex}  — 自定义列渲染（透传给 AppTable）
 *   #card-body         — 自定义卡片内容（默认用 CaseCard）
 *   #detail            — 自定义详情面板（默认显示通用字段）
 */
const props = defineProps({
  caseType: { type: String, default: "ui" },
  listApi: { type: Object, required: true },
  columns: { type: Array, required: true },
  createPath: { type: String, required: true },
  editPath: { type: Function, required: true },
  treeData: { type: Array, default: () => [] },
  activeDirectoryId: { default: null },
  activeDirName: { type: String, default: "" },
  hideCard: { type: Boolean, default: false },
});

const emit = defineEmits(["refresh-tree"]);

const router = useRouter();
const definitions = ref([]);
const loading = ref(false);
const error = ref(null);
const viewMode = ref(localStorage.getItem("case-manager-view-mode") || "card");
function setViewMode(mode) { viewMode.value = mode; localStorage.setItem("case-manager-view-mode", mode); }

const selectedCase = ref(null);
const selectedCaseLoading = ref(false);

async function loadCaseDetail(caseId) {
  selectedCaseLoading.value = true;
  try {
    const { data } = await props.listApi.getDef(caseId);
    if (data.ok) selectedCase.value = data.definition;
  } catch (e) { console.error(e); }
  selectedCaseLoading.value = false;
}

let refreshTimer = null;
watch(() => props.activeDirectoryId, () => loadDefs());
onMounted(() => { loadDefs(); refreshTimer = setInterval(loadDefs, 30000); });
onUnmounted(() => clearInterval(refreshTimer));

async function loadDefs() {
  loading.value = true;
  error.value = null;
  try {
    const { data } = await props.listApi.listDefs(props.activeDirectoryId);
    if (data.ok) definitions.value = data.definitions;
  } catch (e) {
    error.value = '加载用例列表失败';
    console.error(e);
  }
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

function createCase() {
  router.push({ path: props.createPath, query: props.activeDirectoryId ? { directory_id: props.activeDirectoryId } : {} });
}
function editCase(row) { router.push(props.editPath(row.id)); }

async function doRemove(row) {
  try {
    await props.listApi.deleteDef(row.id);
    ElMessage.success("已删除");
    loadDefs();
    emit("refresh-tree");
  } catch (e) {
    ElMessage.error("删除失败: " + (e?.response?.data?.error || e?.message || "网络错误"));
  }
}
function goToAll() { emit("refresh-tree"); }

defineExpose({ loadDefs, definitions });
</script>

<template>
  <div class="case-list-root">
    <!-- 工具栏 -->
    <div class="case-toolbar">
      <div class="case-toolbar__left">
        <div class="case-breadcrumb">
          <span class="crumb" @click="goToAll">📂 全部用例</span>
          <template v-for="(p, i) in breadcrumbPath" :key="p.id">
            <span class="crumb-sep">›</span>
            <span class="crumb" :class="{ 'crumb--active': i === breadcrumbPath.length - 1 }">{{ p.name || p.label }}</span>
          </template>
        </div>
        <span class="case-count-badge">{{ definitions.length }} 用例</span>
      </div>
      <div class="case-toolbar__right">
        <div class="view-toggle">
          <button :class="{ active: viewMode === 'table' }" @click="setViewMode('table')">📋 表格</button>
          <button :class="{ active: viewMode === 'card' }" @click="setViewMode('cards')">📷 卡片</button>
        </div>
        <button class="btn-primary" @click="createCase">＋ 新建</button>
        <slot name="table-extra" />
      </div>
    </div>

    <!-- 错误态 -->
    <div v-if="error" class="case-error">
      <p>{{ error }}</p>
      <button class="btn-primary" @click="loadDefs">重试</button>
    </div>

    <!-- 详情面板 -->
    <div v-if="selectedCase" class="case-detail">
      <div class="case-detail__toolbar">
        <button class="btn-text" @click="selectedCase = null">← 返回列表</button>
        <button class="btn-primary" @click="editCase(selectedCase)">编辑</button>
      </div>
      <div class="case-detail__header">
        <span class="case-detail__id">{{ selectedCase.id }}</span>
        <span class="case-detail__title">{{ selectedCase.title }}</span>
      </div>
      <div class="case-detail__meta">
        <span v-if="selectedCase.category">分类: {{ selectedCase.category }}</span>
        <span v-if="selectedCase.priority">优先级: {{ selectedCase.priority }}</span>
        <span v-if="selectedCase.directory_name">目录: {{ selectedCase.directory_name }}</span>
      </div>
      <div class="case-detail__desc">{{ selectedCase.description || '暂无描述' }}</div>
      <slot name="detail" :case="selectedCase" />
    </div>

    <!-- 表格视图 -->
    <AppCard v-if="viewMode === 'table'" class="table-card">
      <AppTable :columns="columns" :data-source="definitions" row-key="id" :loading="loading" empty-text="暂无用例" @row-click="loadCaseDetail">
        <template v-for="col in columns" :key="col.dataIndex" #[`cell-${col.dataIndex}`]="{ record, value }">
          <slot :name="`cell-${col.dataIndex}`" :record="record" :value="value">
            <template v-if="col.dataIndex === 'id'"><span class="case-link">{{ value }}</span></template>
            <template v-else-if="col.dataIndex === 'enabled'"><el-tag :type="value ? 'success' : 'info'" size="small">{{ value ? '启用' : '禁用' }}</el-tag></template>
            <template v-else-if="col.dataIndex === 'actions'">
              <button class="btn-text" @click.stop="editCase(record)">编辑</button>
              <ConfirmButton size="small" type="danger" plain message="确认删除?" @confirm="doRemove(record)">删除</ConfirmButton>
            </template>
          </slot>
        </template>
      </AppTable>
    </AppCard>

    <!-- 卡片视图 -->
    <div v-if="viewMode === 'cards' && !hideCard" class="card-grid">
      <CaseCard v-for="item in definitions" :key="item.id" :item="item" :case-type="caseType"
        @edit="editCase" @delete="doRemove" @select="loadCaseDetail" @refresh="loadDefs" />
    </div>

    <!-- 加载态 -->
    <div v-if="loading && !definitions.length" class="case-loading">加载中...</div>
  </div>
</template>

<style scoped>
.case-toolbar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.case-toolbar__left{display:flex;align-items:center;gap:8px;flex:1;min-width:0}
.case-toolbar__right{display:flex;align-items:center;gap:8px;flex-shrink:0}
.case-breadcrumb{display:flex;align-items:center;gap:4px;font-size:var(--app-size-xs);font-weight:700;color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.crumb{cursor:pointer;opacity:0.5;transition:opacity 0.12s}.crumb:hover{opacity:0.8}.crumb--active{opacity:1}
.crumb-sep{opacity:0.3}
.case-count-badge{font-size:var(--app-size-xs);font-weight:700;padding:2px 7px;border-radius:4px 8px 4px 8px;background:var(--c-case);color:#fff;border:1.5px solid var(--ink)}
.view-toggle{display:flex;gap:0;border:2px solid var(--c-case);border-radius:4px 8px 4px 8px;overflow:hidden}
.view-toggle button{padding:4px 10px;font-size:var(--app-size-xs);font-weight:700;background:#fff;color:var(--ink);border:none;border-right:1px solid var(--c-case);cursor:pointer;transition:all 0.12s}
.view-toggle button:last-child{border-right:none}
.view-toggle button.active{background:var(--c-case);color:#fff}
.btn-primary{padding:5px 12px;font-size:var(--app-size-xs);font-weight:700;color:#fff;background:var(--c-case);border:2px solid var(--ink);border-radius:4px 8px 4px 8px;cursor:pointer}
.btn-text{padding:4px 8px;font-size:var(--app-size-xs);font-weight:700;background:none;border:none;color:var(--ink);cursor:pointer;opacity:0.5}
.case-error{text-align:center;padding:20px;color:var(--app-status-danger-text)}
.case-detail{background:#fff;border:2.5px solid var(--ink);border-radius:6px 10px 6px 10px;padding:16px;margin-bottom:10px}
.case-detail__toolbar{display:flex;justify-content:space-between;margin-bottom:10px}
.case-detail__header{display:flex;gap:12px;align-items:baseline;margin-bottom:8px}
.case-detail__id{font-family:var(--app-font-mono);font-size:var(--app-size-xs);opacity:0.5}
.case-detail__title{font-size:var(--app-size-md);font-weight:700}
.case-detail__meta{display:flex;gap:16px;font-size:var(--app-size-xs);color:var(--app-text-secondary);margin-bottom:8px}
.case-detail__desc{font-size:var(--app-size-sm);color:var(--ink);line-height:1.5}
.case-link{font-family:var(--app-font-mono);font-size:var(--app-size-xs);font-weight:600;cursor:pointer}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.case-loading{text-align:center;padding:40px;color:var(--app-text-secondary);font-size:var(--app-size-sm)}
</style>
