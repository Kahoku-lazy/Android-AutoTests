<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { getDefinition, saveDefinition } from "./api/uiAutomation.js";
import StepEditor from "./components/StepEditor.vue";
import WatcherPanel from "./components/WatcherPanel.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import { useEditLock } from "./composables/useEditLock.js";
import { useDebugDevice } from "./composables/useDebugDevice.js";
import { useDirtyGuard } from "./composables/useDirtyGuard.js";
import { useDirectoryCascader } from "./composables/useDirectoryCascader.js";

const route = useRoute();
const router = useRouter();

const isNew = computed(() => route.name === "case-new");
const caseId = computed(() => (isNew.value ? "" : route.params.id));

const loading = ref(false);
const saving = ref(false);
const form = ref({
  id: "", title: "", category: "", package_name: "", description: "",
  enabled: true, steps_data: [], directory_id: null,
  priority: "P1", design_method: "", precondition: "", expected_result: "", metrics: "",
  visibility: "public", permitted_users: [], permission: "edit", permitted_editors: [],
  watchers: [],
});

// ── Composables ──
const lock = useEditLock();
const { devices, debugDevice, debugConnected, debugConnecting, availableDevices,
        loadDevices, connectDebugDevice, disconnectDebugDevice } = useDebugDevice();
const { dirOptions, loadDirOptions } = useDirectoryCascader();

// ── Form helpers ──
const permittedUsersStr = computed({
  get: () => (form.value.permitted_users || []).join(", "),
  set: (val) => form.value.permitted_users = val.split(",").map(s => s.trim()).filter(Boolean),
});
const permittedEditorsStr = computed({
  get: () => (form.value.permitted_editors || []).join(", "),
  set: (val) => form.value.permitted_editors = val.split(",").map(s => s.trim()).filter(Boolean),
});

// ── Dirty tracking ──
const initialForm = ref(null);
const isDirty = computed(() => {
  if (!initialForm.value) return false;
  return JSON.stringify(form.value) !== JSON.stringify(initialForm.value);
});
const guard = useDirtyGuard(form, isDirty);

// ── ID generation ──
function generateId() {
  const now = new Date();
  const date = now.toISOString().slice(0, 10).replace(/-/g, "");
  const time = now.toTimeString().slice(0, 8).replace(/:/g, "");
  const rand = String(Math.floor(Math.random() * 10000)).padStart(4, "0");
  form.value.id = `TC-${date}-${time}-${rand}`;
}

// ── Save ──
async function save() {
  if (!form.value.title.trim()) { ElMessage.warning("请输入用例标题"); return false; }
  if (!form.value.package_name.trim()) { ElMessage.warning("请输入 APP 包名"); return false; }
  saving.value = true;
  try {
    const { data } = await saveDefinition(form.value);
    if (data.ok) {
      ElMessage.success("保存成功");
      if (data.id) form.value.id = data.id;
      if (data.updated_at) form.value.updated_at = data.updated_at;
      initialForm.value = JSON.parse(JSON.stringify(form.value));
      if (isNew.value && data.id) await router.replace(`/cases/${data.id}/edit`);
      return true;
    } else { ElMessage.error(data.error || "保存失败"); return false; }
  } catch (e) {
    const status = e.response?.status;
    const errMsg = e.response?.data?.error || "";
    if (status === 409 && errMsg.includes("已被他人修改")) {
      ElMessageBox.alert(errMsg, "保存冲突", { confirmButtonText: "知道了", type: "warning" });
    } else {
      ElMessage.error("保存失败: " + (errMsg || e.message || "网络错误"));
    }
    return false;
  } finally { saving.value = false; }
}

// ── Lifecycle ──
onMounted(async () => {
  guard.setup();
  loadDevices();
  await loadDirOptions();
  if (!isNew.value) {
    loading.value = true;
    try {
      const { data } = await getDefinition(caseId.value);
      if (data.ok) {
        const d = data.definition;
        form.value = {
          id: d.id, title: d.title || "", category: d.category || "",
          package_name: d.package_name || "", description: d.description || "",
          enabled: d.enabled !== false,
          steps_data: d.steps_data ? [...d.steps_data] : [],
          directory_id: d.directory_id || null,
          priority: d.priority || "P1", design_method: d.design_method || "",
          precondition: d.precondition || "", expected_result: d.expected_result || "",
          metrics: d.metrics || "", updated_at: d.updated_at || "",
          visibility: d.visibility || "public", permitted_users: d.permitted_users || [],
          permission: d.permission || "edit", permitted_editors: d.permitted_editors || [],
          watchers: d.watchers || [],
        };
        lock.caseCreatedBy.value = d.created_by || "";
        await lock.acquireLock(caseId.value, d);
      }
    } catch { /* ignore */ }
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
  guard.teardown();
  disconnectDebugDevice();
  lock.releaseLock(caseId.value);
});
</script>

<template>
  <div v-loading="loading" class="doc-page case-editor-page">
    <PageHeader :title="isNew ? '新建用例 New Case' : '编辑用例 Edit Case'" subtitle="定义用例基本信息、编排执行步骤，支持从元素库快速选取 XPath" />

    <div v-if="lock.isReadOnly.value" class="edit-lock-banner">
      <span>🔒 用例正被 <strong>{{ lock.editingBy.value }}</strong> 编辑中，当前为只读模式</span>
      <el-button v-if="lock.currentUser && lock.currentUser === lock.caseCreatedBy.value" size="small" type="primary" danger @click="lock.forceEdit(caseId)">强制编辑</el-button>
    </div>

    <div class="doc-body">
      <section class="doc-section form-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">基本信息 <span class="doc-tag">Basic</span></h3>
          <div class="actions">
            <el-button type="primary" @click="guard.exitPage('/cases')" danger><Icon name="icon-close" :size="14" style="margin-right:4px" />退出</el-button>
            <el-button type="primary" :loading="saving" :disabled="lock.isReadOnly.value" @click="save"><Icon name="icon-check" :size="14" style="margin-right:4px" />保存</el-button>
          </div>
        </div>
        <div class="doc-section__label">用例元数据与启动配置</div>
        <el-form :model="form" label-width="80px" size="default">
          <el-row :gutter="24">
            <el-col :span="14"><el-form-item label="用例 ID"><el-input v-model="form.id" :disabled="!isNew" placeholder="留空则自动生成"><template #append v-if="isNew"><el-button @click="generateId"><Icon name="icon-refresh" :size="14" /> 重新生成</el-button></template></el-input></el-form-item></el-col>
            <el-col :span="10"><el-form-item label="启用"><el-switch v-model="form.enabled" active-text="启用" inactive-text="禁用" /></el-form-item></el-col>
          </el-row>
          <el-row :gutter="24">
            <el-col :span="12"><el-form-item label="标题" required><el-input v-model="form.title" placeholder="用例标题" /></el-form-item></el-col>
            <el-col :span="12"><el-form-item label="目录">
              <el-cascader v-model="form.directory_id" :options="dirOptions" :props="{ checkStrictly: true, emitPath: false, value: 'value', label: 'label' }" placeholder="选择目录（可选）" clearable style="width:100%" />
            </el-form-item></el-col>
          </el-row>
          <el-row :gutter="16"><el-col :span="12"><el-form-item label="分类标签"><el-input v-model="form.category" placeholder="如：登录、支付、首页" /></el-form-item></el-col></el-row>
          <el-form-item label="包名" required><el-input v-model="form.package_name" placeholder="com.example.app（必填）" /></el-form-item>
          <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" placeholder="用例说明、前置条件、预期结果" /></el-form-item>
          <el-row :gutter="16"><el-col :span="12"><el-form-item label="优先级"><el-select v-model="form.priority" style="width:100%"><el-option label="P0 — 必测" value="P0" /><el-option label="P1 — 应测" value="P1" /><el-option label="P2 — 可测" value="P2" /></el-select></el-form-item></el-col></el-row>

          <template v-if="lock.currentUser && lock.caseCreatedBy.value === lock.currentUser">
            <el-divider content-position="left">权限与可见性</el-divider>
            <el-row :gutter="16">
              <el-col :span="12"><el-form-item label="编辑权限"><el-select v-model="form.permission" style="width:100%" :disabled="lock.isReadOnly.value"><el-option label="所有人可编辑" value="edit" /><el-option label="所有人只读" value="readonly" /><el-option label="指定用户可编辑" value="restricted" /></el-select></el-form-item></el-col>
              <el-col v-if="form.permission === 'restricted'" :span="12"><el-form-item label="允许编辑的用户"><el-input v-model="permittedEditorsStr" :disabled="lock.isReadOnly.value" placeholder="用户名，逗号分隔" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12"><el-form-item label="可见范围"><el-select v-model="form.visibility" style="width:100%" :disabled="lock.isReadOnly.value"><el-option label="所有人可见" value="public" /><el-option label="仅创建者" value="hidden" /><el-option label="指定用户" value="restricted" /></el-select></el-form-item></el-col>
              <el-col v-if="form.visibility === 'restricted'" :span="12"><el-form-item label="允许查看的用户"><el-input v-model="permittedUsersStr" :disabled="lock.isReadOnly.value" placeholder="用户名，逗号分隔" /></el-form-item></el-col>
            </el-row>
          </template>

          <template v-if="form.design_method || form.precondition || form.expected_result || form.metrics">
            <el-divider content-position="left">PRD 导入字段</el-divider>
            <el-form-item label="设计方法"><el-input v-model="form.design_method" readonly placeholder="五法之一" /></el-form-item>
            <el-form-item label="前置条件"><el-input v-model="form.precondition" type="textarea" :rows="2" placeholder="测试前置条件" /></el-form-item>
            <el-form-item label="预期结果"><el-input v-model="form.expected_result" type="textarea" :rows="2" placeholder="预期结果" /></el-form-item>
            <el-form-item label="量化指标"><el-input v-model="form.metrics" placeholder="可量化的测试指标" /></el-form-item>
          </template>
        </el-form>
      </section>

      <section class="doc-section steps-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">步骤编排 <span class="doc-tag">Steps</span></h3>
          <div class="steps-header-actions">
            <el-select v-model="debugDevice" size="small" placeholder="选择调试设备" style="width:220px" @focus="loadDevices" :disabled="debugConnected">
              <el-option v-for="d in availableDevices" :key="d.serial" :label="`${d.model || d.serial} [${d.serial}]`" :value="d.serial"><span>{{ d.model || d.serial }}</span><span class="device-option-serial">{{ d.serial }}</span></el-option>
            </el-select>
            <el-button v-if="!debugConnected" type="primary" size="small" :disabled="!debugDevice" :loading="debugConnecting" @click="connectDebugDevice">连接设备</el-button>
            <el-button v-else type="primary" size="small" plain @click="disconnectDebugDevice" danger>断开</el-button>
            <el-button type="primary" size="small" @click="guard.goToElementLocator(save)"><Icon name="icon-search" :size="14" style="margin-right:4px" />去元素定位</el-button>
          </div>
        </div>
        <div class="doc-section__label">全局弹窗监视器 — 在步骤执行过程中自动检测并关闭意外弹出的弹窗</div>
        <WatcherPanel v-model="form.watchers" />
      </section>

      <section class="doc-section">
        <div class="doc-section__label">点击、滑动、等待、校验等操作步骤，选择设备后可单步或批量调试执行</div>
        <StepEditor v-model="form.steps_data" :debug-device="debugDevice" :package-name="form.package_name" :readonly="lock.isReadOnly.value" />
      </section>
    </div>
  </div>
</template>

<style scoped>
.edit-lock-banner { display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; background: rgba(247,205,103,0.18); border-bottom: 1.5px solid rgba(247,170,60,0.3); color: #8a6d14; font-size: var(--app-size-sm); font-weight: 600; flex-shrink: 0; }
.edit-lock-banner strong { color: #6b4c00; }
.case-editor-page { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.case-editor-page .doc-body { flex: 1; min-height: 0; overflow-x: hidden; overflow-y: auto; }
.form-section { padding: 18px 24px; }
.steps-section { padding: 18px 24px 24px; }
.steps-header-actions { display: flex; gap: 10px; align-items: center; }
.actions { display: flex; gap: 10px; }
:deep(.el-input__append) { background: rgba(162,210,255,0.12) !important; }
.device-option-serial { float: right; color: #999; font-size: var(--app-size-sm); }
</style>
