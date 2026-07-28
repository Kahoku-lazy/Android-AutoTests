<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useRoute, useRouter, onBeforeRouteLeave } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import StepEditor from "../StepEditor.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import { getWebDefinition, saveWebDefinition } from "../../api/webAutomation.js";
import { fetchDirectories, acquireEditLock, releaseEditLock } from "../../api.js";

const route = useRoute();
const router = useRouter();

const isNew = computed(() => route.name === "web-case-new");
const caseId = computed(() => (isNew.value ? "" : route.params.id));

const loading = ref(false);
const saving = ref(false);

const form = ref({
  id: "",
  title: "",
  url: "",
  priority: "P1",
  precondition: "",
  description: "",
  enabled: true,
  steps_data: [],
  directory_id: null,
  visibility: "public",
  permitted_users: [],
  permission: "edit",
  permitted_editors: [],
});

// ── Directory cascader ──
const dirOptions = ref([]);

function buildCascaderOptions(tree) {
  return tree.map((node) => ({
    value: node.id, label: node.name,
    children: node.children?.length ? buildCascaderOptions(node.children) : undefined,
  }));
}

async function loadDirOptions() {
  try {
    const { data } = await fetchDirectories("web_automation");
    if (data.ok) dirOptions.value = buildCascaderOptions(data.tree);
  } catch (e) { console.error(e); }
}

// ── Current user ──
function resolveCurrentUser() {
  const active = sessionStorage.getItem("auth_active") || "";
  if (active) return active;
  try {
    const pool = JSON.parse(localStorage.getItem("auth_accounts") || "{}");
    return Object.keys(pool)[0] || "";
  } catch { return ""; }
}

const currentUser = resolveCurrentUser();

// ── Edit lock ──
const isReadOnly = ref(false);
const editingBy = ref("");
const caseCreatedBy = ref("");
const hasEditLock = ref(false);

// ── Dirty tracking ──
const initialForm = ref(null);
const isDirty = computed(() => {
  if (!initialForm.value) return false;
  return JSON.stringify(form.value) !== JSON.stringify(initialForm.value);
});

// ── Visibility helpers ──
const permittedUsersStr = computed({
  get: () => (form.value.permitted_users || []).join(", "),
  set: (val) => { form.value.permitted_users = val.split(",").map(s => s.trim()).filter(Boolean); },
});
const permittedEditorsStr = computed({
  get: () => (form.value.permitted_editors || []).join(", "),
  set: (val) => { form.value.permitted_editors = val.split(",").map(s => s.trim()).filter(Boolean); },
});

// ── ID generation ──
function generateId() {
  const now = new Date();
  const date = now.toISOString().slice(0, 10).replace(/-/g, "");
  const time = now.toTimeString().slice(0, 8).replace(/:/g, "");
  const rand = String(Math.floor(Math.random() * 10000)).padStart(4, "0");
  form.value.id = `WEB-${date}-${time}-${rand}`;
}

// ── Load ──
onMounted(async () => {
  window.addEventListener("beforeunload", onBeforeUnload);
  await loadDirOptions();
  if (!isNew.value) {
    loading.value = true;
    try {
      const { data } = await getWebDefinition(caseId.value);
      if (data.ok) {
        const d = data.definition;
        form.value = {
          id: d.id,
          title: d.title || "",
          url: d.url || "",
          priority: d.priority || "P1",
          precondition: d.precondition || "",
          description: d.description || "",
          enabled: d.enabled !== false,
          steps_data: parseSteps(d.steps_json),
          directory_id: d.directory_id || null,
          visibility: d.visibility || "public",
          permitted_users: d.permitted_users || [],
          permission: d.permission || "edit",
          permitted_editors: d.permitted_editors || [],
        };
        caseCreatedBy.value = d.created_by || "";
        if (d.editing_by && d.editing_by !== currentUser) {
          isReadOnly.value = true;
          editingBy.value = d.editing_by;
        } else if (currentUser) {
          try {
            const lockResp = await acquireEditLock(caseId.value);
            if (lockResp.data.ok) hasEditLock.value = true;
          } catch (e) {
            if (e.response?.status === 423) {
              isReadOnly.value = true;
              editingBy.value = e.response.data?.editing_by || "";
            }
          }
        }
      }
    } catch (e) { console.error(e); }
    loading.value = false;
  } else {
    generateId();
    if (route.query.directory_id) {
      form.value.directory_id = parseInt(route.query.directory_id) || null;
    }
  }
  initialForm.value = JSON.parse(JSON.stringify(form.value));
});

function parseSteps(stepsJson) {
  if (!stepsJson) return [];
  if (Array.isArray(stepsJson)) return stepsJson;
  try { return JSON.parse(stepsJson); } catch { return []; }
}

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

const skipGuard = ref(false);

function onBeforeUnload(e) {
  if (isDirty.value) { e.preventDefault(); e.returnValue = ""; }
}

// ── Force edit ──
async function forceEdit() {
  try {
    await releaseEditLock(caseId.value, true);
    const lockResp = await acquireEditLock(caseId.value);
    if (lockResp.data.ok) {
      isReadOnly.value = false; editingBy.value = ""; hasEditLock.value = true;
      ElMessage.success("已强制获取编辑权限");
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.error || "强制编辑失败");
  }
}

// ── Save ──
async function save() {
  if (!form.value.title.trim()) { ElMessage.warning("请输入用例标题"); return false; }
  if (!form.value.url.trim()) { ElMessage.warning("请输入目标起始 URL"); return false; }
  saving.value = true;
  try {
    const payload = {
      ...form.value,
      steps_json: JSON.stringify(form.value.steps_data),
    };
    const { data } = await saveWebDefinition(payload);
    if (data.ok) {
      ElMessage.success("保存成功");
      if (data.id) form.value.id = data.id;
      if (data.updated_at) form.value.updated_at = data.updated_at;
      initialForm.value = JSON.parse(JSON.stringify(form.value));
      if (isNew.value && data.id) {
        await router.replace(`/cases/web/${data.id}/edit`);
      }
      return true;
    } else {
      ElMessage.error(data.error || "保存失败");
      return false;
    }
  } catch (e) {
    ElMessage.error("保存失败: " + (e?.response?.data?.error || e?.message || "网络错误"));
    return false;
  } finally {
    saving.value = false;
  }
}

async function exitPage() {
  if (isDirty.value) {
    try {
      await ElMessageBox.confirm("当前用例有未保存的修改，退出后数据将会丢失。是否继续退出？", "未保存的修改", {
        confirmButtonText: "不保存，直接退出", cancelButtonText: "取消", type: "warning",
      });
    } catch { return; }
  }
  skipGuard.value = true;
  router.push("/cases");
}
</script>

<template>
  <div v-loading="loading" class="doc-page case-editor-page">
    <PageHeader
      :title="isNew ? '新建 Web 自动化用例' : '编辑 Web 自动化用例'"
      subtitle="编排浏览器自动化步骤：页面跳转、元素点击、表单填充、文本验证、截图"
    />

    <!-- Read-only banner -->
    <div v-if="isReadOnly" class="edit-lock-banner">
      <span>🔒 用例正被 <strong>{{ editingBy }}</strong> 编辑中，当前为只读模式</span>
      <el-button v-if="currentUser && currentUser === caseCreatedBy" size="small" type="primary" danger @click="forceEdit">强制编辑</el-button>
    </div>

    <div class="doc-body">
      <!-- 基本信息 -->
      <section class="doc-section form-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">基本信息 <span class="doc-tag">Basic</span></h3>
          <div class="actions">
            <el-button @click="exitPage" disabled="false">退出</el-button>
            <el-button type="primary" :loading="saving" :disabled="isReadOnly" @click="save">保存</el-button>
          </div>
        </div>
        <div class="doc-section__label">用例元数据与起始 URL 配置</div>

        <el-form :model="form" label-width="80px" size="default">
          <el-row :gutter="24">
            <el-col :span="14">
              <el-form-item label="用例 ID">
                <el-input v-model="form.id" :disabled="!isNew" placeholder="留空则自动生成">
                  <template #append v-if="isNew">
                    <el-button @click="generateId">重新生成</el-button>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item label="启用">
                <el-switch v-model="form.enabled" active-text="启用" inactive-text="禁用" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="标题" required>
                <el-input v-model="form.title" placeholder="用例标题" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="目录">
                <el-cascader v-model="form.directory_id" :options="dirOptions"
                  :props="{ checkStrictly: true, emitPath: false, value: 'value', label: 'label' }"
                  placeholder="选择目录（可选）" clearable style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="起始 URL" required>
            <el-input v-model="form.url" placeholder="https://example.com（浏览器从这个 URL 开始执行）" />
          </el-form-item>

          <el-form-item label="描述">
            <el-input v-model="form.description" type="textarea" :rows="2" placeholder="用例说明、前置条件、预期结果" />
          </el-form-item>

          <el-form-item label="前置条件">
            <el-input v-model="form.precondition" type="textarea" :rows="2" placeholder="浏览器版本要求、需要登录状态等" />
          </el-form-item>

          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="优先级">
                <el-select v-model="form.priority" style="width: 100%">
                  <el-option label="P0 — 必测" value="P0" />
                  <el-option label="P1 — 应测" value="P1" />
                  <el-option label="P2 — 可测" value="P2" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 权限与可见性 -->
          <template v-if="currentUser && caseCreatedBy === currentUser">
            <el-divider content-position="left">权限与可见性</el-divider>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="编辑权限">
                  <el-select v-model="form.permission" style="width: 100%" :disabled="isReadOnly">
                    <el-option label="所有人可编辑" value="edit" />
                    <el-option label="所有人只读" value="readonly" />
                    <el-option label="指定用户可编辑" value="restricted" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col v-if="form.permission === 'restricted'" :span="12">
                <el-form-item label="允许编辑的用户">
                  <el-input v-model="permittedEditorsStr" :disabled="isReadOnly" placeholder="用户名，逗号分隔" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="可见范围">
                  <el-select v-model="form.visibility" style="width: 100%" :disabled="isReadOnly">
                    <el-option label="所有人可见" value="public" />
                    <el-option label="仅创建者" value="hidden" />
                    <el-option label="指定用户" value="restricted" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col v-if="form.visibility === 'restricted'" :span="12">
                <el-form-item label="允许查看的用户">
                  <el-input v-model="permittedUsersStr" :disabled="isReadOnly" placeholder="用户名，逗号分隔" />
                </el-form-item>
              </el-col>
            </el-row>
          </template>
        </el-form>
      </section>

      <!-- 步骤编排 -->
      <section class="doc-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">步骤编排 <span class="doc-tag">Steps</span></h3>
        </div>
        <div class="doc-section__label">
          页面跳转、点击元素、填充表单、等待加载、验证文本、截图等浏览器自动化步骤
        </div>
        <StepEditor v-model="form.steps_data" :package-name="form.url" :readonly="isReadOnly" />
      </section>
    </div>
  </div>
</template>

<style scoped>
.case-editor-page {
  display: flex; flex-direction: column; height: 100%; overflow: hidden;
}
.case-editor-page .doc-body {
  flex: 1; min-height: 0; overflow-x: hidden; overflow-y: auto;
}
.form-section { padding: 18px 24px; }
.edit-lock-banner {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 20px; margin: 0;
  background: rgba(247, 205, 103, 0.18);
  border-bottom: 1.5px solid rgba(247, 170, 60, 0.3);
  color: #8a6d14; font-size: var(--app-size-sm); font-weight: 600; flex-shrink: 0;
}
.edit-lock-banner strong { color: #6b4c00; }
.actions { display: flex; gap: 10px; }
:deep(.el-input__append) { background: rgba(162,210,255,0.12) !important; }
</style>
