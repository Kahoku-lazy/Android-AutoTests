<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRouter, useRoute, onBeforeRouteLeave } from "vue-router";
import { ElMessage } from "element-plus";
import PageHeader from "@/shared/components/PageHeader.vue";
import AppCard from "@/shared/components/AppCard.vue";
import {
  getStorageDefinition,
  saveStorageDefinition,
} from "../../api/storage.js";
import {
  acquireEditLock,
  releaseEditLock,
} from "../../api/uiAutomation.js";
import { fetchDirectories } from "../../api/directories.js";

const router = useRouter();
const route = useRoute();
const caseId = computed(() => route.params.id);
const isNew = computed(() => !caseId.value);
const saving = ref(false);
const loading = ref(false);

// Default columns
const DEFAULT_COLS = [
  { key: "id", label: "测试用例编号", width: 200, editable: false },
  { key: "title", label: "用例标题", width: 200, editable: true },
  { key: "priority", label: "优先级", width: 80, editable: true },
  { key: "precondition", label: "前置条件", width: 200, editable: true },
  { key: "steps", label: "用例步骤", width: 300, editable: true },
  { key: "expected_result", label: "预期结果", width: 300, editable: true },
];

// ── Table data (rows) ──
const columns = ref([...DEFAULT_COLS.map(c => ({ ...c }))]);
const rows = ref([]);
const selectedRow = ref(-1);

// Metadata
const directoryId = ref(null);
const directories = ref([]);
const editLockHeld = ref(false);
const lockOwner = ref("");
let lockHeartbeat = null;
const currentUser = ref(sessionStorage.getItem("current-username") || "");

// Row ID counter
let rowCounter = 1;

async function loadDirectories() {
  try {
    const { data } = await fetchDirectories("storage");
    if (data.ok) directories.value = data.tree || [];
  } catch (_) {}
}

function blankRow() {
  const r = { id: rowCounter++ };
  columns.value.forEach(c => { if (c.editable) r[c.key] = ""; });
  return r;
}

async function loadCase() {
  if (isNew.value) {
    if (route.query.directory_id) directoryId.value = Number(route.query.directory_id);
    rows.value.push(blankRow());
    return;
  }
  loading.value = true;
  try {
    const { data } = await getStorageDefinition(caseId.value);
    if (data.ok) {
      const d = data.definition;
      directoryId.value = d.directory_id;
      // Rebuild rows from saved data
      const savedCols = d.custom_columns || [];
      if (savedCols.length) {
        const merged = [...DEFAULT_COLS.map(c => ({ ...c }))];
        savedCols.forEach(col => merged.push({ key: col.key, label: col.key, width: 200, editable: true }));
        columns.value = merged;
      }
      rows.value = d.rows || [];
      if (!rows.value.length && d.title) {
        // Fallback: single-row from old format
        rows.value.push({
          id: 1, title: d.title, priority: d.priority, precondition: d.precondition,
          steps: d.steps, expected_result: d.expected_result,
        });
        rowCounter = 2;
      } else {
        rowCounter = rows.value.length + 1;
      }
      if (d.editing_by) lockOwner.value = d.editing_by;
    }
  } catch (_) { ElMessage.error("加载用例失败"); }
  loading.value = false;
}

// ── Row operations ──
function addRow() {
  rows.value.push(blankRow());
  selectedRow.value = rows.value.length - 1;
}

function removeRow(index) {
  if (rows.value.length <= 1) { ElMessage.warning("至少保留一行"); return; }
  rows.value.splice(index, 1);
  if (selectedRow.value >= rows.value.length) selectedRow.value = rows.value.length - 1;
}

function addColumn() {
  const name = prompt("输入新列名称：");
  if (!name || !name.trim()) return;
  const key = "custom_" + name.trim().replace(/\s+/g, "_").toLowerCase();
  if (columns.value.find(c => c.key === key)) { ElMessage.warning("列名已存在"); return; }
  columns.value.push({ key, label: name.trim(), width: 200, editable: true });
  rows.value.forEach(r => { r[key] = ""; });
}

function removeColumn(colIdx) {
  const col = columns.value[colIdx];
  if (DEFAULT_COLS.find(dc => dc.key === col.key)) { ElMessage.warning("默认列不能删除"); return; }
  columns.value.splice(colIdx, 1);
  rows.value.forEach(r => { delete r[col.key]; });
}

// ── Edit lock ──
async function acquireLock() {
  if (isNew.value || lockOwner.value) return;
  try {
    const { data } = await acquireEditLock(caseId.value);
    if (data.ok) {
      editLockHeld.value = true;
      lockHeartbeat = setInterval(async () => { try { await acquireEditLock(caseId.value); } catch (_) {} }, 600000);
    }
  } catch (e) {
    if (e.response?.status === 423) lockOwner.value = e.response.data.editing_by || "其他用户";
  }
}
async function releaseLock() {
  if (!editLockHeld.value) return;
  clearInterval(lockHeartbeat);
  try { await releaseEditLock(caseId.value); } catch (_) {}
  editLockHeld.value = false;
}

onMounted(async () => { await loadDirectories(); await loadCase(); await acquireLock(); });
onUnmounted(() => releaseLock());
const originalJson = ref("");
onMounted(() => { originalJson.value = JSON.stringify({ rows: rows.value, columns: columns.value }); });
onBeforeRouteLeave((_to, _from, next) => {
  const current = JSON.stringify({ rows: rows.value, columns: columns.value });
  if (current !== originalJson.value) {
    if (!window.confirm("有未保存的修改，确定离开吗？")) return next(false);
  }
  releaseLock();
  next();
});

const isLockedByOther = computed(() => !!(lockOwner.value && lockOwner.value !== currentUser.value));

// ── Save ──
async function doSave() {
  saving.value = true;
  try {
    // Build custom_columns from added columns (exclude default ones)
    const customCols = [];
    columns.value.forEach(c => {
      if (!DEFAULT_COLS.find(dc => dc.key === c.key)) {
        customCols.push({ key: c.key, label: c.label });
      }
    });
    // Use first row for title + metadata fields
    const firstRow = rows.value[0] || {};
    const payload = {
      title: firstRow.title || `存储用例-${new Date().toISOString().slice(0,10)}`,
      priority: firstRow.priority || "P1",
      precondition: firstRow.precondition || "",
      steps: firstRow.steps || "",
      expected_result: firstRow.expected_result || "",
      custom_columns: customCols,
      directory_id: directoryId.value,
      rows: rows.value,
    };
    if (!isNew.value) payload.id = caseId.value;
    const { data } = await saveStorageDefinition(payload);
    if (data.ok) {
      ElMessage.success("保存成功");
      originalJson.value = JSON.stringify({ rows: rows.value, columns: columns.value });
      if (isNew.value) router.replace(`/cases/storage/${data.id}/edit`);
    } else {
      ElMessage.error(data.error || "保存失败");
    }
  } catch (e) {
    ElMessage.error("保存失败: " + (e?.response?.data?.error || e?.message));
  }
  saving.value = false;
}
</script>

<template>
  <div class="doc-page wb-shell">
    <PageHeader :title="isNew ? '新建功能测试用例' : '编辑功能测试用例'" icon="🗄️">
      <template #actions>
        <button class="btn-text" @click="router.back()">取消</button>
        <button class="btn-primary" :disabled="saving || isLockedByOther" @click="doSave">
          {{ saving ? "保存中..." : "保存" }}
        </button>
      </template>
    </PageHeader>

    <div v-if="loading" class="case-loading">加载中...</div>
    <div v-else-if="isLockedByOther" class="lock-banner">⚠️ {{ lockOwner }} 正在编辑此用例，当前为只读模式。</div>

    <div v-else class="table-editor">
      <div class="table-toolbar">
        <div class="table-toolbar__left">
          <span class="toolbar-label">目录：</span>
          <select v-model="directoryId" class="form-select">
            <option :value="null">根级（未分类）</option>
            <option v-for="d in directories.filter(n => n.node_type === 'directory')" :key="d.id" :value="d.id">{{ d.name }}</option>
          </select>
        </div>
        <div class="table-toolbar__right">
          <button class="btn-minor" @click="addColumn">+ 新增列</button>
          <button class="btn-minor" @click="addRow">+ 新增行</button>
          <button class="btn-minor btn-danger-outline" @click="removeRow(selectedRow)" :disabled="selectedRow < 0">删除选中行</button>
        </div>
      </div>

      <AppCard class="table-card">
        <div class="table-scroll">
          <table class="editable-table">
            <thead>
              <tr>
                <th class="col-num">#</th>
                <th v-for="(col, ci) in columns" :key="col.key" :style="{ minWidth: col.width + 'px' }">
                  {{ col.label }}
                  <button v-if="!DEFAULT_COLS.find(dc => dc.key === col.key)"
                    class="btn-col-remove" @click="removeColumn(ci)" title="删除此列">✕</button>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in rows" :key="ri"
                :class="{ 'row-selected': selectedRow === ri }"
                @click="selectedRow = ri">
                <td class="col-num">{{ ri + 1 }}</td>
                <td v-for="col in columns" :key="col.key">
                  <input v-if="col.editable" v-model="row[col.key]" class="cell-input"
                    :placeholder="col.label" />
                  <span v-else class="cell-text">{{ row[col.key] }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </AppCard>
    </div>
  </div>
</template>

<style scoped>
.table-editor { display: flex; flex-direction: column; gap: 12px; }
.table-toolbar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.table-toolbar__left, .table-toolbar__right { display: flex; align-items: center; gap: 8px; }
.toolbar-label { font-size: 13px; color: #555; }
.form-select { padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
.table-card { padding: 0; overflow: hidden; }
.table-scroll { overflow-x: auto; }
.editable-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.editable-table th { background: #f5f5f5; padding: 8px 10px; text-align: left; font-weight: 600; white-space: nowrap; border-bottom: 2px solid #e0e0e0; position: relative; }
.editable-table td { padding: 4px 6px; border-bottom: 1px solid #f0f0f0; }
.col-num { width: 40px; text-align: center; color: #999; font-size: 12px; }
.row-selected { background: #f0f7ff; }
.row-selected td { border-color: #c8e0ff; }
.cell-input { width: 100%; padding: 4px 6px; border: 1px solid transparent; border-radius: 4px; font-size: 13px; background: transparent; }
.cell-input:focus { border-color: var(--animal-primary-color, #89CFF0); background: #fff; outline: none; }
.cell-input:hover { border-color: #ddd; }
.cell-text { padding: 4px 6px; display: block; }
.btn-col-remove { position: absolute; right: 2px; top: 50%; transform: translateY(-50%); border: none; background: #fee; color: #e85f5f; border-radius: 3px; cursor: pointer; font-size: 10px; padding: 1px 4px; }
.btn-primary, .btn-minor, .btn-text { padding: 6px 16px; border-radius: 8px; border: 1px solid #e0e0e0; background: #fff; cursor: pointer; font-size: 13px; }
.btn-primary { background: var(--animal-primary-color, #89CFF0); color: #fff; border-color: var(--animal-primary-color, #89CFF0); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger-outline { color: #e85f5f; border-color: #fcc; }
.lock-banner { padding: 12px 16px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.case-loading { text-align: center; padding: 40px; color: #999; }
</style>
