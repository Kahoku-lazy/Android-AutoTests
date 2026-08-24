<script setup>
/**
 * StorageCaseEditor — 业务功能用例编辑（文本步骤 + 预期结果）
 */
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useRoute, useRouter, onBeforeRouteLeave } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import PageHeader from "@/shared/components/PageHeader.vue";
import { getStorageDefinition, saveStorageDefinition } from "../../api/storage";
import { getActive } from "@/shared/auth/token-storage";
import { fetchDirectories, acquireEditLock, releaseEditLock } from "../../api";

const route = useRoute();
const router = useRouter();

const isNew = computed(() => route.name === "storage-case-new");
const caseId = computed(() => (isNew.value ? "" : route.params.id));

const loading = ref(false);
const saving = ref(false);
const skipGuard = ref(false);

const form = ref({
  id: "",
  title: "",
  category: "",
  priority: "P1",
  precondition: "",
  steps: "",
  expected_result: "",
  description: "",
  enabled: true,
  directory_id: null,
  design_method: "",
  metrics: "",
  visibility: "public",
  permitted_users: [],
  permission: "edit",
  permitted_editors: [],
  updated_at: "",
});

const dirOptions = ref([]);
const currentUser = getActive();
const isReadOnly = ref(false);
const editingBy = ref("");
const hasEditLock = ref(false);
const initialForm = ref(null);

const isDirty = computed(() => {
  if (!initialForm.value) return false;
  return JSON.stringify(form.value) !== JSON.stringify(initialForm.value);
});

function buildCascaderOptions(tree) {
  return tree.map((node) => ({
    value: node.id,
    label: node.name,
    children: node.children?.length ? buildCascaderOptions(node.children) : undefined,
  }));
}

async function loadDirOptions() {
  try {
    const { data } = await fetchDirectories("storage");
    if (data.status) dirOptions.value = buildCascaderOptions(data.tree);
  } catch (e) {
    console.error(e);
  }
}

function generateId() {
  const now = new Date();
  const date = now.toISOString().slice(0, 10).replace(/-/g, "");
  const time = now.toTimeString().slice(0, 8).replace(/:/g, "");
  const rand = String(Math.floor(Math.random() * 10000)).padStart(4, "0");
  form.value.id = `ST-${date}-${time}-${rand}`;
}

async function acquireLock(d) {
  if (!currentUser) return;
  if (d.locked && d.created_by !== currentUser) {
    isReadOnly.value = true;
    editingBy.value = "创建者（已锁定用例）";
    return;
  }
  if (d.editing_by && d.editing_by !== currentUser) {
    isReadOnly.value = true;
    editingBy.value = d.editing_by;
    return;
  }
  try {
    const lockResp = await acquireEditLock(caseId.value);
    if (lockResp.data.status) hasEditLock.value = true;
  } catch (e) {
    if (e.response?.status === 423) {
      isReadOnly.value = true;
      editingBy.value = e.response.data?.editing_by || "";
    }
  }
}

onMounted(async () => {
  window.addEventListener("beforeunload", onBeforeUnload);
  await loadDirOptions();
  if (!isNew.value) {
    loading.value = true;
    try {
      const { data } = await getStorageDefinition(caseId.value);
      if (data.status) {
        const d = data.definition;
        form.value = {
          id: d.id,
          title: d.title || "",
          category: d.category || "",
          priority: d.priority || "P1",
          precondition: d.precondition || "",
          steps: d.steps || "",
          expected_result: d.expected_result || "",
          description: d.description || "",
          enabled: d.enabled !== false,
          directory_id: d.directory_id || null,
          design_method: d.design_method || "",
          metrics: d.metrics || "",
          visibility: d.visibility || "public",
          permitted_users: d.permitted_users || [],
          permission: d.permission || "edit",
          permitted_editors: d.permitted_editors || [],
          updated_at: d.updated_at || "",
        };
        await acquireLock(d);
      } else {
        ElMessage.error(data.message || "加载用例失败");
      }
    } catch (e) {
      ElMessage.error("加载用例失败: " + (e.response?.data?.message || e.message || "网络错误"));
    }
    loading.value = false;
  } else {
    generateId();
    if (route.query.directory_id) {
      form.value.directory_id = parseInt(route.query.directory_id) || null;
    }
  }
  initialForm.value = JSON.parse(JSON.stringify(form.value));
});

onUnmounted(() => {
  window.removeEventListener("beforeunload", onBeforeUnload);
  if (hasEditLock.value && caseId.value) {
    releaseEditLock(caseId.value).catch(() => {});
  }
});

onBeforeRouteLeave((_to, _from, next) => {
  if (!isDirty.value || skipGuard.value) return next();
  ElMessageBox.confirm("当前用例有未保存的修改，离开后数据将会丢失。是否继续？", "未保存的修改", {
    confirmButtonText: "不保存，直接离开",
    cancelButtonText: "取消",
    type: "warning",
  }).then(() => next()).catch(() => next(false));
});

function onBeforeUnload(e) {
  if (isDirty.value) {
    e.preventDefault();
    e.returnValue = "";
  }
}

async function save() {
  if (!form.value.title.trim()) {
    ElMessage.warning("请输入用例标题");
    return false;
  }
  saving.value = true;
  try {
    const { data } = await saveStorageDefinition(form.value);
    if (data.status) {
      ElMessage.success("保存成功");
      if (data.id) form.value.id = data.id;
      if (data.updated_at) form.value.updated_at = data.updated_at;
      initialForm.value = JSON.parse(JSON.stringify(form.value));
      if (isNew.value && data.id) {
        await router.replace(`/cases/storage/${data.id}/edit`);
      }
      return true;
    }
    ElMessage.error(data.message || "保存失败");
    return false;
  } catch (e) {
    const status = e.response?.status;
    const errMsg = e.response?.data?.message || "";
    if (status === 409 && errMsg.includes("已被他人修改")) {
      ElMessageBox.alert(errMsg, "保存冲突", { confirmButtonText: "知道了", type: "warning" });
    } else {
      ElMessage.error("保存失败: " + (errMsg || e.message || "网络错误"));
    }
    return false;
  } finally {
    saving.value = false;
  }
}

async function exitPage() {
  if (isDirty.value) {
    try {
      await ElMessageBox.confirm(
        "当前用例有未保存的修改，退出后数据将会丢失。是否继续退出？",
        "未保存的修改",
        { confirmButtonText: "不保存，直接退出", cancelButtonText: "取消", type: "warning" },
      );
    } catch {
      return;
    }
  }
  skipGuard.value = true;
  router.push("/cases/storage");
}
</script>

<template>
  <div v-loading="loading" class="doc-page case-editor-page">
    <PageHeader
      :title="isNew ? '新建业务功能用例' : '编辑业务功能用例'"
      subtitle="维护前置条件、步骤与预期结果"
    />

    <div v-if="isReadOnly" class="lock-banner">
      当前只读：{{ editingBy || "他人正在编辑" }}
    </div>

    <el-form label-width="100px" class="storage-form" :disabled="isReadOnly">
      <el-form-item label="用例 ID">
        <el-input v-model="form.id" disabled />
      </el-form-item>
      <el-form-item label="标题" required>
        <el-input v-model="form.title" placeholder="用例标题" />
      </el-form-item>
      <el-form-item label="目录">
        <el-cascader
          v-model="form.directory_id"
          :options="dirOptions"
          :props="{ checkStrictly: true, emitPath: false }"
          clearable
          placeholder="选择目录"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="分类">
        <el-input v-model="form.category" placeholder="分类" />
      </el-form-item>
      <el-form-item label="优先级">
        <el-select v-model="form.priority" style="width: 160px">
          <el-option label="P0 — 必测" value="P0" />
          <el-option label="P1 — 应测" value="P1" />
          <el-option label="P2 — 可测" value="P2" />
        </el-select>
      </el-form-item>
      <el-form-item label="启用">
        <el-switch v-model="form.enabled" />
      </el-form-item>
      <el-form-item label="前置条件">
        <el-input v-model="form.precondition" type="textarea" :rows="2" placeholder="前置条件" />
      </el-form-item>
      <el-form-item label="步骤">
        <el-input v-model="form.steps" type="textarea" :rows="8" placeholder="每行一步" />
      </el-form-item>
      <el-form-item label="预期结果">
        <el-input v-model="form.expected_result" type="textarea" :rows="4" placeholder="预期结果" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="2" />
      </el-form-item>
    </el-form>

    <div class="editor-actions">
      <el-button @click="exitPage">返回列表</el-button>
      <el-button type="primary" :loading="saving" :disabled="isReadOnly" @click="save">保存</el-button>
    </div>
  </div>
</template>

<style scoped>
.storage-form { max-width: 880px; margin: 12px 0 24px; }
.lock-banner {
  margin: 8px 0 12px;
  padding: 8px 12px;
  border: 2px solid var(--ink);
  border-radius: 6px;
  background: #fff7e6;
  font-size: var(--app-size-sm);
  font-weight: 700;
}
.editor-actions { display: flex; gap: 10px; }
</style>
