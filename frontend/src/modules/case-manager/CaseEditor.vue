<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useRoute, useRouter, onBeforeRouteLeave } from "vue-router";
import { animate } from "animejs";
import { ElMessage, ElMessageBox, ElCascader } from "element-plus";
import client from "@/shared/api-client.js";
import StepEditor from "./components/StepEditor.vue";
import PageHeader from "@/shared/components/PageHeader.vue";
import { Button as AnimalButton, Icon } from "animal-island-vue";
import { fetchDirectories } from "./api.js";

const route = useRoute();
const router = useRouter();

const isNew = computed(() => route.name === "case-new");
const caseId = computed(() => (isNew.value ? "" : route.params.id));

const loading = ref(false);
const saving = ref(false);
const form = ref({
  id: "",
  title: "",
  category: "",
  package_name: "",
  description: "",
  enabled: true,
  steps_data: [],
  directory_id: null,
  // IoT PRD fields
  priority: "P1",
  design_method: "",
  precondition: "",
  expected_result: "",
  metrics: "",
});

// ── Directory cascader options ──
const dirOptions = ref([]);

function buildCascaderOptions(tree) {
  return tree.map((node) => ({
    value: node.id,
    label: node.name,
    children:
      node.children && node.children.length > 0
        ? buildCascaderOptions(node.children)
        : undefined,
  }));
}

async function loadDirOptions() {
  try {
    const { data } = await fetchDirectories();
    if (data.ok) {
      dirOptions.value = buildCascaderOptions(data.tree);
    }
  } catch (_) {}
}

// ── Dirty tracking (unsaved changes detection) ──
const initialForm = ref(null);
const isDirty = computed(() => {
  if (!initialForm.value) return false;
  const curr = JSON.stringify(form.value);
  const orig = JSON.stringify(initialForm.value);
  return curr !== orig;
});

// ── Device selector for step debugging ──
const devices = ref([]);
const debugDevice = ref("");
async function loadDevices() {
  try {
    const { data } = await client.get("/devices");
    if (data.ok) {
      devices.value = (data.devices || []).filter(
        (d) => d.status === "ONLINE" || d.status === "BUSY",
      );
      if (!debugDevice.value && devices.value.length)
        debugDevice.value = devices.value[0].serial;
    }
  } catch (_) {}
}

onMounted(async () => {
  // B10: 浏览器刷新/关标签页时提示保存
  window.addEventListener("beforeunload", onBeforeUnload);
  loadDevices();
  await loadDirOptions();
  if (!isNew.value) {
    loading.value = true;
    try {
      const { data } = await client.get(`/cases/definitions/${caseId.value}`);
      if (data.ok) {
        const d = data.definition;
        form.value = {
          id: d.id,
          title: d.title || "",
          category: d.category || "",
          package_name: d.package_name || "",
          description: d.description || "",
          enabled: d.enabled !== false,
          steps_data: d.steps_data ? [...d.steps_data] : [],
          directory_id: d.directory_id || null,
          priority: d.priority || "P1",
          design_method: d.design_method || "",
          precondition: d.precondition || "",
          expected_result: d.expected_result || "",
          metrics: d.metrics || "",
        };
      }
    } catch (_) {}
    loading.value = false;
  } else {
    generateId();
    // Pre-select directory from query param
    if (route.query.directory_id) {
      form.value.directory_id = parseInt(route.query.directory_id) || null;
    }
  }
  // Capture initial state for dirty tracking
  initialForm.value = JSON.parse(JSON.stringify(form.value));
});

function generateId() {
  const now = new Date();
  const date = now.toISOString().slice(0, 10).replace(/-/g, "");
  const time = now.toTimeString().slice(0, 8).replace(/:/g, "");
  const rand = String(Math.floor(Math.random() * 10000)).padStart(4, "0");
  form.value.id = `TC-${date}-${time}-${rand}`;
}

async function save() {
  if (!form.value.title.trim()) {
    ElMessage.warning("请输入用例标题");
    return false;
  }
  if (!form.value.package_name.trim()) {
    ElMessage.warning(
      "请输入 APP 包名（步骤中的启动/关闭/重启应用需要此信息）",
    );
    return false;
  }
  saving.value = true;
  try {
    const { data } = await client.post("/cases/definitions", form.value);
    if (data.ok) {
      ElMessage.success("保存成功");
      // Reset dirty tracker BEFORE router.replace — 否则 onBeforeRouteLeave 看到 isDirty=true
      initialForm.value = JSON.parse(JSON.stringify(form.value));
      if (isNew.value && data.id) {
        form.value.id = data.id;
        await router.replace(`/cases/${data.id}/edit`);
      }
      return true;
    } else {
      ElMessage.error(data.error || "保存失败");
      return false;
    }
  } catch (e) {
    ElMessage.error("保存失败: " + (e.message || "网络错误"));
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
        {
          confirmButtonText: "不保存，直接退出",
          cancelButtonText: "取消",
          type: "warning",
        },
      );
    } catch (_) {
      return; // user cancelled
    }
  }
  skipGuard.value = true; // B6修复: 防止onBeforeRouteLeave二次弹窗
  router.push("/cases");
}

async function goToElementLocator() {
  // 有未保存修改 → 先问用户是否保存后跳转
  if (isDirty.value) {
    try {
      await ElMessageBox.confirm(
        "当前用例有未保存的修改，是否保存后跳转到元素定位页面？",
        "保存并跳转",
        {
          confirmButtonText: "保存并跳转",
          cancelButtonText: "取消",
          type: "warning",
        },
      );
    } catch (_) {
      return; // 用户取消 → 留在编辑页
    }
  }
  const ok = await save();
  if (!ok) return;
  router.push("/elements");
}

const skipGuard = ref(false); // B6修复: 防止exitPage+onBeforeRouteLeave双重弹窗

// B10: 浏览器刷新/关标签页时提示
function onBeforeUnload(e) {
  if (isDirty.value) {
    e.preventDefault();
    e.returnValue = ""; // Chrome需要
  }
}

onUnmounted(() => {
  window.removeEventListener("beforeunload", onBeforeUnload);
});

// Browser back / router navigation guard
onBeforeRouteLeave((_to, _from, next) => {
  if (!isDirty.value || skipGuard.value) return next();
  ElMessageBox.confirm(
    "当前用例有未保存的修改，离开后数据将会丢失。是否继续？",
    "未保存的修改",
    {
      confirmButtonText: "不保存，直接离开",
      cancelButtonText: "取消",
      type: "warning",
    },
  )
    .then(() => next())
    .catch(() => next(false));
});
</script>

<template>
  <div v-loading="loading" class="doc-page case-editor-page">
    <PageHeader
      :title="isNew ? '新建用例 New Case' : '编辑用例 Edit Case'"
      subtitle="定义用例基本信息、编排执行步骤，支持从元素库快速选取 XPath"
      color="app-yellow"
    />

    <div class="doc-body">
      <!-- 基本信息 -->
      <section class="doc-section form-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            基本信息
            <span class="doc-tag">Basic</span>
          </h3>
          <div class="actions">
            <el-button type="danger" @click="exitPage">
              <Icon
                name="icon-close"
                :size="14"
                style="margin-right: 4px"
              />退出
            </el-button>
            <el-button type="primary" :loading="saving" @click="save">
              <Icon
                name="icon-check"
                :size="14"
                style="margin-right: 4px"
              />保存
            </el-button>
          </div>
        </div>
        <div class="doc-section__label">用例元数据与启动配置</div>

        <el-form :model="form" label-width="80px" size="default">
          <el-row :gutter="24">
            <el-col :span="14">
              <el-form-item label="用例 ID">
                <el-input
                  v-model="form.id"
                  :disabled="!isNew"
                  placeholder="留空则自动生成 TC-日期-时间-随机码"
                >
                  <template #append v-if="isNew">
                    <el-button @click="generateId">
                      <Icon name="icon-refresh" :size="14" /> 重新生成
                    </el-button>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item label="启用">
                <el-switch
                  v-model="form.enabled"
                  active-text="启用"
                  inactive-text="禁用"
                />
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
                <el-cascader
                  v-model="form.directory_id"
                  :options="dirOptions"
                  :props="{
                    checkStrictly: true,
                    emitPath: false,
                    value: 'value',
                    label: 'label',
                  }"
                  placeholder="选择目录（可选）"
                  clearable
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="分类标签">
                <el-input
                  v-model="form.category"
                  placeholder="如：登录、支付、首页"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="包名" required>
            <el-input
              v-model="form.package_name"
              placeholder="com.example.app（必填，启动/关闭/重启应用时使用）"
            />
          </el-form-item>

          <el-form-item label="描述">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="2"
              placeholder="用例说明、前置条件、预期结果"
            />
          </el-form-item>

          <!-- 优先级（始终可见） -->
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

          <!-- IoT PRD 字段（从 PRD 文档生成时自动填充） -->
          <template
            v-if="
              form.design_method ||
              form.precondition ||
              form.expected_result ||
              form.metrics
            "
          >
            <el-divider content-position="left">PRD 导入字段</el-divider>

            <el-form-item label="设计方法">
              <el-input
                v-model="form.design_method"
                readonly
                placeholder="五法之一"
              />
            </el-form-item>

            <el-form-item label="前置条件">
              <el-input
                v-model="form.precondition"
                type="textarea"
                :rows="2"
                placeholder="测试前置条件"
              />
            </el-form-item>

            <el-form-item label="预期结果">
              <el-input
                v-model="form.expected_result"
                type="textarea"
                :rows="2"
                placeholder="预期结果"
              />
            </el-form-item>

            <el-form-item label="量化指标">
              <el-input v-model="form.metrics" placeholder="可量化的测试指标" />
            </el-form-item>
          </template>
        </el-form>
      </section>

      <!-- 步骤编排 -->
      <section class="doc-section steps-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            步骤编排
            <span class="doc-tag">Steps</span>
          </h3>
          <div class="steps-header-actions">
            <el-select
              v-model="debugDevice"
              size="small"
              placeholder="选择调试设备"
              style="width: 260px"
              @focus="loadDevices"
            >
              <el-option
                v-for="d in devices"
                :key="d.serial"
                :label="`${d.model || d.serial} [${d.serial}]`"
                :value="d.serial"
              >
                <span>{{ d.model || d.serial }}</span>
                <span style="float: right; color: #9f927d; font-size: 12px">{{
                  d.serial
                }}</span>
              </el-option>
            </el-select>
            <AnimalButton
              type="primary"
              size="small"
              @click="goToElementLocator"
            >
              <Icon
                name="icon-search"
                :size="14"
                style="margin-right: 4px"
              />去元素定位
            </AnimalButton>
          </div>
        </div>
        <div class="doc-section__label">
          点击、滑动、等待、校验等操作步骤，选择设备后可单步或批量调试执行
        </div>
        <StepEditor
          v-model="form.steps_data"
          :debug-device="debugDevice"
          :package-name="form.package_name"
        />
      </section>
    </div>
  </div>
</template>

<style scoped>
.case-editor-page {
  min-height: 100%;
}
.form-section {
  padding: 18px 24px;
}
.steps-section {
  padding: 18px 24px 24px;
}
.steps-header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.actions {
  display: flex;
  gap: 10px;
}

:deep(.el-input__append) {
  background: var(--animal-bg-color-secondary, #f0e8d8) !important;
}
</style>
