<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { bus } from "@/shared/event-bus.js";
import client from "@/shared/api-client.js";
import { ElMessageBox, ElMessage } from "element-plus";
import {
  IconPlus,
  IconRefresh,
  IconTrash,
  IconGripVertical,
} from "@/shared/icons/index.js";

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  debugDevice: { type: String, default: "" },
  packageName: { type: String, default: "" },
});
const emit = defineEmits(["update:modelValue"]);

import { STEP_TYPES, STEP_FIELDS, FIELD_LABELS, DIRECTION_OPTIONS, FIELD_HINTS, APP_LIFECYCLE_TYPES } from '@/shared/constants/steps.js'
// ── Element manager data for XPath picker ──
const pages = ref([]);
const allElements = ref([]); // flat list with page info
const elementSearchQuery = ref("");

const filteredElements = computed(() => {
  if (!elementSearchQuery.value) return allElements.value;
  const q = elementSearchQuery.value.toLowerCase();
  return allElements.value.filter((el) => {
    return (
      (el.alias || "").toLowerCase().includes(q) ||
      (el.text_val || "").toLowerCase().includes(q) ||
      (el.resource_id || "").toLowerCase().includes(q) ||
      (el.content_desc || "").toLowerCase().includes(q) ||
      (getXPath(el) || "").toLowerCase().includes(q)
    );
  });
});

const filteredPages = computed(() => {
  const pageIds = new Set(filteredElements.value.map((e) => e._pageId));
  return pages.value.filter((p) => pageIds.has(p.id));
});

onMounted(() => loadElementLibrary());

async function loadElementLibrary() {
  try {
    const { data: pageData } = await client.get("/elements/pages");
    if (!pageData.ok) return;
    pages.value = pageData.pages || [];
    // Load elements for all pages
    const results = [];
    for (const p of pages.value) {
      try {
        const { data: elData } = await client.get(
          `/elements/pages/${p.id}/items`,
        );
        if (elData.ok) {
          for (const e of elData.elements || []) {
            results.push({
              ...e,
              _pageLabel: p.label || `Page#${p.id}`,
              _pageId: p.id,
            });
          }
        }
      } catch (_) {}
    }
    allElements.value = results;
  } catch (_) {}
}

function getXPath(el) {
  try {
    return JSON.parse(el.xpath_candidates)[0]?.xpath || "";
  } catch {
    return "";
  }
}

function elementOptionLabel(el) {
  // 只显示元素名称，不显示 XPath
  return el.alias || el.text_val || el.resource_id || "未命名";
}

// Find element by id, fill step fields
function onElementPicked(step, field, elementId) {
  const el = allElements.value.find((e) => e.id === elementId);
  if (!el) return;
  step[field] = getXPath(el);
  // Auto-fill description for click/wait steps
  if (!step.description) {
    step.description = el.alias || el.text_val || el.resource_id || "";
  }
  // Store element reference and ID for dynamic name resolution
  step[`_el_${field}`] = el;
  step[`_el_id_${field}`] = el.id;
}

// Resolve current element name from element library (follows element manager changes)
function resolveElementName(step, field = "xpath") {
  const id = step[`_el_id_${field}`];
  if (id) {
    const el = allElements.value.find((e) => e.id === id);
    if (el) return el.alias || el.text_val || el.resource_id || "未命名元素";
  }
  const cached = step[`_el_${field}`];
  if (cached)
    return (
      cached.alias || cached.text_val || cached.resource_id || "未命名元素"
    );
  return step.description || "元素";
}

// ── State ──
const expanded = ref({});
const steps = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});


function defaultStep(type = "click") {
  const xpath = APP_LIFECYCLE_TYPES.includes(type)
    ? props.packageName || ""
    : "";
  return {
    type,
    xpath,
    xpath2: "",
    timeout: 10,
    expected_text: "",
    index: 0,
    description: "",
    direction: "up",
    distance: 500,
  };
}

function visibleFields(step) {
  const info = STEP_FIELDS[step.type] || { required: [], optional: [] };
  return [...info.required, ...(info.optional || [])];
}

function isFieldRequired(step, field) {
  return (STEP_FIELDS[step.type]?.required || []).includes(field);
}

function isContainer(type) {
  return ["if_element_appear", "if_element_disappear", "loop_n", "loop_elements"].includes(type);
}

function addStep() {
  if (steps.value.length >= 100) {
    ElMessage.warning("单用例最多 100 个步骤");
    return;
  }
  const newSteps = [...steps.value, defaultStep()];
  steps.value = newSteps;
  expanded.value[newSteps.length - 1] = true;
}

function addChildStep(parentStep) {
  if (!parentStep.children) parentStep.children = [];
  if (parentStep.children.length >= 50) {
    ElMessage.warning("单个容器最多 50 个子步骤");
    return;
  }
  parentStep.children.push(defaultStep("click"));
  steps.value = [...steps.value]; // trigger reactivity
}

function removeChildStep(parentStep, childIdx) {
  parentStep.children = parentStep.children.filter((_, i) => i !== childIdx);
  steps.value = [...steps.value]; // trigger reactivity
}

function removeStep(idx) {
  steps.value = steps.value.filter((_, i) => i !== idx);
}

function duplicateStep(idx) {
  const original = steps.value[idx];
  const copy = JSON.parse(JSON.stringify(original));
  const newSteps = [...steps.value];
  newSteps.splice(idx + 1, 0, copy);
  steps.value = newSteps;
  expanded.value[idx + 1] = true;
}

// ── Delete confirmation ──
const skipDeleteConfirm = ref(false);
const deleteDialog = ref({ visible: false, idx: null, skip: false });

function requestRemoveStep(idx) {
  if (skipDeleteConfirm.value) {
    removeStep(idx);
    return;
  }
  deleteDialog.value = { visible: true, idx, skip: false };
}

function confirmRemove() {
  removeStep(deleteDialog.value.idx);
  skipDeleteConfirm.value = deleteDialog.value.skip;
  deleteDialog.value.visible = false;
}

// ── Drag & drop reorder ──
const dragIndex = ref(null);
const dropTargetIdx = ref(null);

function onDragStart(idx, e) {
  dragIndex.value = idx;
  dropTargetIdx.value = null;
  e.dataTransfer.effectAllowed = "move";
}

function onDragOver(idx, e) {
  e.preventDefault();
  if (idx !== dragIndex.value) dropTargetIdx.value = idx;
}

function onDragLeave() {
  dropTargetIdx.value = null;
}

function onDragEnd() {
  dragIndex.value = null;
  dropTargetIdx.value = null;
}

function onDrop(e, idx) {
  e.preventDefault();
  e.stopPropagation();
  if (dragIndex.value === null || dragIndex.value === idx) {
    dragIndex.value = null;
    dropTargetIdx.value = null;
    return;
  }
  const arr = [...steps.value];
  const [moved] = arr.splice(dragIndex.value, 1);
  arr.splice(idx, 0, moved);
  steps.value = arr;
  expanded.value = {};
  dragIndex.value = null;
  dropTargetIdx.value = null;
}

function onTypeChange(idx, newType) {
  const newSteps = [...steps.value];
  const fields = STEP_FIELDS[newType] || { required: [], optional: [] };
  const allFields = new Set([...fields.required, ...(fields.optional || [])]);
  const newStep = { ...defaultStep(newType) };
  const old = newSteps[idx];
  for (const key of Object.keys(old)) {
    if (key === "type" || key.startsWith("_el_")) continue;
    if (allFields.has(key)) newStep[key] = old[key] || newStep[key];
  }
  // When switching to app lifecycle step, default xpath to case package name
  if (APP_LIFECYCLE_TYPES.includes(newType) && props.packageName) {
    newStep.xpath = newStep.xpath || props.packageName;
  }
  newSteps[idx] = newStep;
  steps.value = newSteps;
}

// ── Event bus: receive element from locator ──
const onAddStepFromLocator = (payload) => {
  if (steps.value.length >= 100) {
    ElMessage.warning("单用例最多 100 个步骤，请先删除多余步骤后再添加");
    return;
  }
  const step = defaultStep("click");
  step.xpath = payload.xpath || "";
  step.description =
    payload.description ||
    `${payload.type}: ${(payload.xpath || "").slice(0, 60)}`;
  steps.value = [...steps.value, step];
};
bus.on("add-step-to-case", onAddStepFromLocator);
// B9修复: 组件卸载时清理事件监听
onUnmounted(() => {
  bus.off("add-step-to-case", onAddStepFromLocator);
});

// ── Step summary with clear action description ──
function stepSummary(step) {
  const def = STEP_TYPES.find((t) => t.value === step.type);
  const icon = def?.icon || "";
  const elName = resolveElementName(step, "xpath");

  switch (step.type) {
    case "click":
      return `${icon} 点击「${elName}」`;
    case "long_click":
      return `${icon} 长按「${elName}」${step.timeout || 0.8}s`;
    case "swipe":
      return `${icon} 向${DIRECTION_OPTIONS.find((d) => d.value === step.direction)?.label || step.direction}滑动 ${step.distance || 500}px`;
    case "wait":
      return `${icon} 等待「${elName}」出现（${step.timeout || 10}s）`;
    case "wait_disappear":
      return `${icon} 等待「${elName}」消失`;
    case "sleep":
      return `${icon} 暂停 ${step.timeout || 0}s`;
    case "verify_text":
      return `${icon} 检查「${elName}」文字是否="${step.expected_text || "?"}"`;
    case "poll_text":
      return `${icon} 等待「${elName}」出现，文字="${step.expected_text || "?"}"`;
    case "start_app":
      return `${icon} 打开应用 ${step.xpath || ""}`;
    case "kill_app":
      return `${icon} 关闭应用 ${step.xpath || ""}`;
    case "perf_element_time":
      return `${icon} 等待「${elName}」出现耗时（超时${step.timeout || 10}s）`;
    case "wait_toast":
      return `${icon} 等待Toast「${step.expected_text || "?"}」`;
    case "if_element_appear":
      return `${icon} 如果「${elName}」出现 (${(step.children || []).length} 子步骤)`;
    case "if_element_disappear":
      return `${icon} 如果「${elName}」消失 (${(step.children || []).length} 子步骤)`;
    case "loop_n":
      return `${icon} 循环 ${step.index || 1} 次 (${(step.children || []).length} 子步骤)`;
    case "loop_elements":
      return `${icon} 遍历 ${(step.xpath || '').split('|').filter(Boolean).length || 0} 个元素 (${(step.children || []).length} 子步骤)`;
    default:
      return `${icon} ${def?.label || step.type}`;
  }
}

function fieldLabel(step, field) {
  if (
    field === "xpath" &&
    ["start_app", "kill_app"].includes(step.type)
  )
    return "包名";
  if (field === "timeout" && step.type === "long_click") return "长按秒数";
  if (field === "timeout" && step.type === "sleep") return "等待秒数";
  return FIELD_LABELS[field] || field;
}

function fieldHint(step, field) {
  if (field === "direction") return "滑动方向";
  if (field === "distance") return "滑动的像素距离";
  return "";
}

// Whether to use element picker vs free-text input for a field
function useElementPicker(step) {
  return !["start_app", "kill_app", "swipe"].includes(step.type);
}

// ── Run single step on device ──
const runningStep = ref(null);
const runningBatch = ref(false);
const runningFromIdx = ref(null);
const stepResults = ref({}); // { [idx]: { ok, message } }

async function runStep(idx, step) {
  if (!props.debugDevice) {
    ElMessage.warning("请先在顶部选择调试设备");
    return;
  }
  runningStep.value = idx;
  stepResults.value[idx] = null;
  try {
    const { data } = await client.post("/runner/run-step", {
      device_serial: props.debugDevice,
      type: step.type,
      xpath: step.xpath || "",
      xpath2: step.xpath2 || "",
      timeout: step.timeout || 10,
      expected_text: step.expected_text || "",
      index: step.index ?? 0,
      direction: step.direction || "",
      distance: step.distance || 500,
      description: step.description || "",
    });
    stepResults.value[idx] = data.ok
      ? { ok: true, message: data.message || "执行成功" }
      : { ok: false, message: data.error || "执行失败" };
  } catch (e) {
    stepResults.value[idx] = {
      ok: false,
      message: e.response?.data?.error || e.message || "请求失败",
    };
  }
  runningStep.value = null;
}

async function runStepsRange(fromIdx) {
  runningBatch.value = true;
  runningFromIdx.value = fromIdx;
  const stepsToRun = steps.value.slice(fromIdx);
  for (let i = 0; i < stepsToRun.length; i++) {
    const realIdx = fromIdx + i;
    runningStep.value = realIdx;
    stepResults.value[realIdx] = null;
    try {
      const s = stepsToRun[i];
      const { data } = await client.post("/runner/run-step", {
        device_serial: props.debugDevice,
        type: s.type,
        xpath: s.xpath || "",
        xpath2: s.xpath2 || "",
        timeout: s.timeout || 10,
        expected_text: s.expected_text || "",
        index: s.index ?? 0,
        direction: s.direction || "",
        distance: s.distance || 500,
        description: s.description || "",
      });
      stepResults.value[realIdx] = data.ok
        ? { ok: true, message: data.message || "执行成功" }
        : { ok: false, message: data.error || "执行失败" };
      if (!data.ok) {
        try {
          await ElMessageBox.confirm("上一步执行失败，是否继续？", "步骤失败", {
            confirmButtonText: "继续",
            cancelButtonText: "停止",
            type: "warning",
          });
        } catch (_) {
          break;
        }
      }
    } catch (e) {
      stepResults.value[realIdx] = {
        ok: false,
        message: e.message || "请求失败",
      };
      break;
    }
  }
  runningStep.value = null;
  runningBatch.value = false;
  runningFromIdx.value = null;
}

function runAllSteps() {
  stepResults.value = {};
  runStepsRange(0);
}
function runFromCurrent(idx) {
  runStepsRange(idx);
}
</script>

<template>
  <div class="step-editor">
    <div class="step-header">
      <span class="step-header__title">步骤列表 ({{ steps.length }})</span>
      <div class="step-header__actions">
        <template v-if="steps.length">
          <el-button
            size="small"
            type="primary"
            plain
            :loading="runningBatch && runningFromIdx === 0"
            @click="runAllSteps"
            :disabled="runningBatch"
            >▶▶ 从头执行</el-button>
          <el-button
            size="small"
            @click="loadElementLibrary"
            text
            title="刷新元素库"
            ><IconRefresh :size="14"
          /></el-button>
        </template>
        <el-button size="small" type="primary" @click="addStep">
          <IconPlus :size="14" style="margin-right: 4px" />添加步骤
        </el-button>
      </div>
    </div>

    <div v-if="!steps.length" class="empty-hint">
      暂无步骤，点击「添加步骤」开始编排
    </div>

    <div
      v-for="(step, idx) in steps"
      :key="idx"
      class="step-item"
      :class="{
        expanded: expanded[idx],
        dragging: dragIndex === idx,
        'drop-target': dropTargetIdx === idx && dragIndex !== idx,
      }"
      draggable="true"
      @dragstart="onDragStart(idx, $event)"
      @dragover="onDragOver(idx, $event)"
      @dragleave="onDragLeave"
      @dragend="onDragEnd"
      @drop="onDrop($event, idx)"
    >
      <!-- Step summary bar -->
      <div class="step-bar" @click="expanded[idx] = !expanded[idx]">
        <span class="drag-handle" title="拖动排序">
          <IconGripVertical :size="16" />
        </span>
        <span class="step-idx">
          <template v-if="stepResults[idx]">
            {{ stepResults[idx].ok ? "✅" : "❌" }}</template
          >
          <template v-else>{{ idx + 1 }}</template>
        </span>
        <span class="step-summary">
          {{ stepSummary(step) }}
          <span
            v-if="stepResults[idx]"
            :class="['step-result-msg', stepResults[idx].ok ? 'ok' : 'fail']"
            >{{ stepResults[idx].message }}</span
          >
        </span>
        <span class="step-actions" @click.stop>
          <el-button
            size="small"
            type="primary"
            plain
            :loading="runningStep === idx"
            @click="runStep(idx, step)"
            title="单步执行"
            >▶</el-button>
          <el-button
            size="small"
            type="primary"
            plain
            :loading="runningFromIdx === idx"
            @click="runFromCurrent(idx)"
            title="从这步开始执行到结束"
            :disabled="runningBatch && runningFromIdx !== idx"
            >▶▶ ▸</el-button>
          <el-button
            size="small"
            plain
            @click="duplicateStep(idx)"
            title="复制步骤"
            >📋</el-button>
          <el-button type="primary"
            size="small"
            
            plain
            @click="requestRemoveStep(idx)"
           danger>
            <IconTrash :size="14" style="margin-right: 4px" />删除
          </el-button>
        </span>
      </div>

      <!-- Expanded form -->
      <div v-show="expanded[idx]" class="step-form">
        <div class="step-desc">
          {{ STEP_TYPES.find((t) => t.value === step.type)?.desc }}
        </div>
        <el-form label-width="80px" size="small">
          <el-form-item label="类型">
            <el-select
              v-model="step.type"
              @change="(t) => onTypeChange(idx, t)"
              style="width: 240px"
            >
              <el-option-group
                v-for="grp in [...new Set(STEP_TYPES.map((s) => s.group))]"
                :key="grp"
                :label="grp"
              >
                <el-option
                  v-for="st in STEP_TYPES.filter((s) => s.group === grp)"
                  :key="st.value"
                  :label="st.icon + ' ' + st.label"
                  :value="st.value"
                />
              </el-option-group>
            </el-select>
          </el-form-item>

          <template v-for="field in visibleFields(step)" :key="field">
            <!-- Direction → select -->
            <el-form-item
              v-if="field === 'direction'"
              :label="FIELD_LABELS.direction"
              :required="isFieldRequired(step, field)"
            >
              <el-select v-model="step.direction" style="width: 140px">
                <el-option
                  v-for="d in DIRECTION_OPTIONS"
                  :key="d.value"
                  :label="d.label"
                  :value="d.value"
                />
              </el-select>
              <span class="field-hint">{{ fieldHint(step, field) }}</span>
            </el-form-item>

            <!-- Distance → number -->
            <el-form-item
              v-else-if="field === 'distance'"
              :label="FIELD_LABELS.distance"
              :required="isFieldRequired(step, field)"
            >
              <el-input-number
                v-model="step.distance"
                :min="50"
                :max="3000"
                :step="50"
              />
              <span class="field-hint">{{ fieldHint(step, field) }}</span>
            </el-form-item>

            <!-- XPath fields → element picker -->
            <el-form-item
              v-else-if="
                (field === 'xpath' || field === 'xpath2') &&
                useElementPicker(step)
              "
              :label="fieldLabel(step, field)"
              :required="isFieldRequired(step, field)"
            >
              <el-select
                :model-value="step[field] ? step['_el_' + field]?.id || '' : ''"
                placeholder="搜索元素名称/ID..."
                filterable
                :filter-method="(q) => (elementSearchQuery = q)"
                clearable
                style="width: 100%"
                @change="(val) => onElementPicked(step, field, val)"
              >
                <el-option-group
                  v-for="pg in filteredPages"
                  :key="pg.id"
                  :label="
                    (pg.label || 'Page#' + pg.id) +
                    ' (' +
                    filteredElements.filter((e) => e._pageId === pg.id).length +
                    ')'
                  "
                >
                  <el-option
                    v-for="el in filteredElements.filter(
                      (e) => e._pageId === pg.id,
                    )"
                    :key="el.id"
                    :label="elementOptionLabel(el)"
                    :value="el.id"
                  >
                    <div class="el-opt">
                      <span class="el-opt-name">{{
                        el.alias || el.text_val || el.resource_id || "未命名"
                      }}</span>
                      <span class="el-opt-page">{{
                        pg.label || "Page#" + pg.id
                      }}</span>
                    </div>
                  </el-option>
                </el-option-group>
              </el-select>
              <div v-if="step[field]" class="current-xpath">
                <code>{{ step[field] }}</code>
              </div>
            </el-form-item>

            <!-- app lifecycle xpath → free text -->
            <el-form-item
              v-else-if="
                (field === 'xpath' || field === 'xpath2') &&
                !useElementPicker(step)
              "
              :label="fieldLabel(step, field)"
              :required="isFieldRequired(step, field)"
            >
              <el-input v-model="step[field]" placeholder="com.example.app" />
            </el-form-item>

            <!-- Text fields -->
            <el-form-item
              v-else-if="field === 'expected_text' || field === 'description'"
              :label="FIELD_LABELS[field]"
              :required="isFieldRequired(step, field)"
            >
              <el-input
                v-model="step[field]"
                :placeholder="FIELD_HINTS[field] || ''"
              />
            </el-form-item>

            <!-- Number fields -->
            <el-form-item
              v-else-if="field === 'timeout' || field === 'index'"
              :label="fieldLabel(step, field)"
              :required="isFieldRequired(step, field)"
            >
              <el-input-number
                v-model="step[field]"
                :min="0"
                :step="1"
                :precision="field === 'timeout' ? 1 : 0"
              />
              <span class="field-hint" v-if="fieldHint(step, field)">{{
                fieldHint(step, field)
              }}</span>
            </el-form-item>
          </template>

          <el-form-item
            label="描述"
            v-if="!visibleFields(step).includes('description')"
          >
            <el-input v-model="step.description" placeholder="步骤描述" />
          </el-form-item>
        </el-form>

        <!-- Child steps for container types -->
        <div v-if="isContainer(step.type)" class="child-steps">
          <div class="child-steps__header">
            <span>📎 子步骤 ({{ (step.children || []).length }})</span>
            <el-button size="small" type="primary" plain @click="addChildStep(step)">
              <IconPlus :size="12" style="margin-right: 2px" />添加子步骤
            </el-button>
          </div>
          <div v-if="(step.children || []).length" class="child-steps__list">
            <div
              v-for="(child, ci) in step.children"
              :key="ci"
              class="child-step-item"
            >
              <span class="child-step-idx">{{ idx + 1 }}.{{ ci + 1 }}</span>
              <span class="child-step-type">{{ STEP_TYPES.find(t => t.value === child.type)?.label || child.type }}</span>
              <span class="child-step-desc">{{ child.description || child.xpath || '(未设置)' }}</span>
              <el-button size="small" @click="removeChildStep(step, ci)" type="danger" plain class="child-step-del">
                <IconTrash :size="12" />
              </el-button>
            </div>
          </div>
          <div v-else class="child-steps__empty">暂无子步骤，点击上方按钮添加</div>
        </div>
      </div>
    </div>

    <div v-if="steps.length > 0" class="add-bottom">
      <el-button size="small" type="primary" @click="addStep">
        <IconPlus :size="14" style="margin-right: 4px" />添加步骤
      </el-button>
    </div>

    <!-- Delete confirmation -->
    <el-dialog
      v-model:open="deleteDialog.visible"
      title="删除步骤"
      width="360px"
      @close="deleteDialog.visible = false"
    >
      <p>确定要删除第 {{ deleteDialog.idx + 1 }} 个步骤吗？</p>
      <el-checkbox v-model="deleteDialog.skip">本次编辑不再询问</el-checkbox>
      <template #footer>
        <el-button @click="deleteDialog.visible = false">取消</el-button>
        <el-button type="primary" danger @click="confirmRemove"
          >确定删除</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.step-editor {
  margin-top: 4px;
}
.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.step-header__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
}
.step-header__actions {
  display: flex;
  gap: 8px;
}

.empty-hint {
  text-align: center;
  color: #999;
  font-size: 14px;
  padding: 32px;
  border: 1px dashed rgba(162,210,255,0.38);
  border-radius: 12px;
  background: rgba(255,255,255,0.36);
}

.step-item {
  position: relative;
  margin-bottom: 10px;
  border-radius: 12px;
  border: 1px solid var(--ink);
  background: rgba(255,255,255,0.48);
  box-shadow: var(--app-shadow-sm);
  transition: all 0.2s;
  overflow: hidden;
}
.step-item:hover {
  border-color: rgba(162,210,255,0.62);
  box-shadow: var(--app-shadow-md);
}
.step-item.expanded {
  border-color: var(--accent-blue);
  box-shadow: 0 2px 10px rgba(64, 158, 255, 0.1);
}
.step-item.dragging {
  opacity: 0.4;
  transform: scale(0.97);
  box-shadow: 0 0 0 2px var(--app-green-deep);
}
.step-item.drop-target {
  border-color: var(--app-green-deep) !important;
  box-shadow:
    0 0 0 2px var(--app-green-deep),
    0 4px 16px rgba(162,210,255,0.28) !important;
}
.step-item.drop-target .step-bar {
  background: rgba(162,210,255,0.16);
}
.step-item.drop-target::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--app-green-deep);
  border-radius: 0 4px 4px 0;
  z-index: 2;
}

.step-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
  background: rgba(255,255,255,0.36);
}
.drag-handle {
  color: #999;
  cursor: grab;
  display: flex;
  align-items: center;
  padding: 2px;
  border-radius: 4px;
  transition: all 0.15s;
}
.drag-handle:hover {
  color: var(--app-green-deep);
  background: rgba(162,210,255,0.16);
}
.drag-handle:active {
  cursor: grabbing;
}
.step-item.dragging .drag-handle {
  color: var(--app-green-deep);
}
.step-idx {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--app-green-deep);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.step-summary {
  flex: 1;
  font-size: 14px;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.step-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.step-actions :deep(.el-button) {
  padding: 5px 8px;
}
.step-result-msg {
  font-size: 11px;
  margin-left: 8px;
  font-weight: 600;
}
.step-result-msg.ok {
  color: var(--app-green, var(--c-workflow));
}
.step-result-msg.fail {
  color: #e85f5f;
}

.step-desc {
  font-size: 13px;
  color: #999;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: rgba(162,210,255,0.10);
  border-radius: 8px;
}
.step-form {
  padding: 14px 18px 18px 48px;
  border-top: 1px solid rgba(162,210,255,0.20);
  background: rgba(255,255,255,0.38);
}
.add-bottom {
  margin-top: 14px;
  text-align: center;
}
.field-hint {
  font-size: 12px;
  color: #999;
  margin-left: 10px;
}
.current-xpath {
  margin-top: 6px;
  font-size: 12px;
}
.current-xpath code {
  background: rgba(162,210,255,0.12);
  padding: 3px 8px;
  border-radius: 4px;
  font-family: monospace;
  word-break: break-all;
  color: var(--ink);
}

/* Element picker — override el-select-dropdown item height */
.step-form :deep(.el-select-dropdown__item) {
  height: auto;
  line-height: 1.4;
  padding: 8px 12px;
}

/* Element picker options */
.el-opt {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  line-height: 1.4;
}
.el-opt-name {
  font-weight: 600;
  font-size: 13px;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}
.el-opt-page {
  font-size: 10px;
  color: #fff;
  background: var(--app-green-deep);
  padding: 1px 6px;
  border-radius: 10px;
  flex-shrink: 0;
  white-space: nowrap;
}

/* ── Child steps (nested) ── */
.child-steps {
  margin-top: 12px;
  padding: 10px 14px;
  background: rgba(162,210,255,0.06);
  border: 1px dashed rgba(162,210,255,0.3);
  border-radius: 10px;
}
.child-steps__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--app-green-deep);
  margin-bottom: 8px;
}
.child-steps__list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.child-step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: rgba(255,255,255,0.6);
  border-radius: 8px;
  border-left: 3px solid var(--app-green-deep);
}
.child-step-idx {
  font-size: 10px;
  font-weight: 700;
  color: var(--app-green-deep);
  min-width: 28px;
}
.child-step-type {
  font-size: 11px;
  font-weight: 600;
  color: #999;
  background: rgba(162,210,255,0.15);
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
}
.child-step-desc {
  flex: 1;
  font-size: 12px;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.child-step-del {
  flex-shrink: 0;
}
.child-steps__empty {
  text-align: center;
  font-size: 12px;
  color: #999;
  padding: 12px;
}
</style>
