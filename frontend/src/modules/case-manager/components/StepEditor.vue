<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessageBox, ElMessage } from "element-plus";
import { IconPlus, IconRefresh, IconTrash, IconGripVertical } from "@/shared/icons/index";
import { STEP_FIELDS, FIELD_LABELS, DIRECTION_OPTIONS, FIELD_HINTS, APP_LIFECYCLE_TYPES } from "@/shared/constants/steps";
import { fetchStepTypes } from "../api";
import { useStepDragDrop } from "../composables/useStepDragDrop";
import { useStepFields } from "../composables/useStepFields";
import { useElementLibrary } from "../composables/useElementLibrary";
import { useStepRunner } from "../composables/useStepRunner";
import { stepSummary as buildStepSummary } from "../step-utils";

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  debugDevice: { type: String, default: "" },
  packageName: { type: String, default: "" },
  target: { type: String, default: "android" },
});
const emit = defineEmits(["update:modelValue"]);

// ── Step types from backend ──
const availableTypes = ref([]);
async function loadStepTypes() {
  try {
    const { data } = await fetchStepTypes(props.target);
    if (data?.status) availableTypes.value = data.data?.types || [];
  } catch { console.error("加载步骤类型失败") }
}
onMounted(loadStepTypes);

// ── Steps state (must be declared BEFORE composables that reference it) ──
const expanded = ref({});
const steps = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val),
});

// ── Composables ──
const { pages, allElements, elementSearchQuery, filteredElements, filteredPages,
        loadElementLibrary, getXPath, elementOptionLabel, onElementPicked, resolveElementName }
  = useElementLibrary();
const { runningStep, runningBatch, runningFromIdx, stepResults, runStep, runStepsRange, runAllSteps, runFromCurrent }
  = useStepRunner(() => props.debugDevice, steps);
const { defaultStep, visibleFields, isFieldRequired, isContainer, fieldLabel, fieldHint, useElementPicker }
  = useStepFields(() => props.packageName);
const { dragIndex, dropTargetIdx, onDragStart, onDragOver, onDragLeave, onDragEnd, onDrop }
  = useStepDragDrop(steps, expanded);

onMounted(() => loadElementLibrary());

function addStep() {
  if (steps.value.length >= 100) { ElMessage.warning("单用例最多 100 个步骤"); return; }
  const newSteps = [...steps.value, defaultStep()];
  steps.value = newSteps; expanded.value[newSteps.length - 1] = true;
}
function addChildStep(parentStep) {
  if (!parentStep.children) parentStep.children = [];
  if (parentStep.children.length >= 50) { ElMessage.warning("单个容器最多 50 个子步骤"); return; }
  parentStep.children.push(defaultStep("click"));
  steps.value = [...steps.value];
}
function removeChildStep(parentStep, childIdx) {
  parentStep.children = parentStep.children.filter((_, i) => i !== childIdx);
  steps.value = [...steps.value];
}
function removeStep(idx) { steps.value = steps.value.filter((_, i) => i !== idx); }
function duplicateStep(idx) {
  const copy = JSON.parse(JSON.stringify(steps.value[idx]));
  const newSteps = [...steps.value]; newSteps.splice(idx + 1, 0, copy);
  steps.value = newSteps; expanded.value[idx + 1] = true;
}

// ── Delete confirmation ──
const skipDeleteConfirm = ref(false);
const deleteDialog = ref({ visible: false, idx: null, skip: false });
function requestRemoveStep(idx) {
  if (skipDeleteConfirm.value) { removeStep(idx); return; }
  deleteDialog.value = { visible: true, idx, skip: false };
}
function confirmRemove() {
  removeStep(deleteDialog.value.idx);
  skipDeleteConfirm.value = deleteDialog.value.skip;
  deleteDialog.value.visible = false;
}

// ── Type change ──
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
  if (APP_LIFECYCLE_TYPES.includes(newType) && props.packageName) {
    newStep.xpath = newStep.xpath || props.packageName;
  }
  newSteps[idx] = newStep; steps.value = newSteps;
}

function stepSummary(step) { return buildStepSummary(step, resolveElementName); }
</script>

<template>
  <div class="step-editor">
    <div class="step-header">
      <span class="step-header__title">步骤列表 ({{ steps.length }})</span>
      <div class="step-header__actions">
        <template v-if="steps.length">
          <el-button size="small" type="primary" plain :loading="runningBatch && runningFromIdx === 0" @click="runAllSteps" :disabled="runningBatch">▶▶ 从头执行</el-button>
          <el-button size="small" @click="loadElementLibrary" text title="刷新元素库"><IconRefresh :size="14" /></el-button>
        </template>
        <el-button size="small" type="primary" @click="addStep"><IconPlus :size="14" style="margin-right:4px" />添加步骤</el-button>
      </div>
    </div>

    <div v-if="!steps.length" class="empty-state">暂无步骤，点击「添加步骤」开始编排</div>

    <div v-for="(step, idx) in steps" :key="idx" class="step-item"
      :class="{ expanded: expanded[idx], dragging: dragIndex === idx, 'drop-target': dropTargetIdx === idx && dragIndex !== idx }"
      draggable="true"
      @dragstart="onDragStart(idx, $event)" @dragover="onDragOver(idx, $event)" @dragleave="onDragLeave" @dragend="onDragEnd" @drop="onDrop($event, idx)">
      <div class="step-bar" role="button" tabindex="0" @click="expanded[idx] = !expanded[idx]" @keydown.enter.prevent="expanded[idx] = !expanded[idx]" @keydown.space.prevent="expanded[idx] = !expanded[idx]">
        <span class="drag-handle" title="拖动排序"><IconGripVertical :size="16" /></span>
        <span class="step-idx">
          <template v-if="stepResults[idx]">{{ stepResults[idx].status ? '✅' : '❌' }}</template>
          <template v-else>{{ idx + 1 }}</template>
        </span>
        <span class="step-summary">{{ stepSummary(step) }}<span v-if="stepResults[idx]" :class="['step-result-msg', stepResults[idx].status ? 'ok' : 'fail']">{{ stepResults[idx].message }}</span></span>
        <span class="step-actions" @click.stop>
          <el-button size="small" type="primary" plain :loading="runningStep === idx" @click="runStep(idx, step)" title="单步执行">▶</el-button>
          <el-button size="small" type="primary" plain :loading="runningFromIdx === idx" @click="runFromCurrent(idx)" title="从这步开始" :disabled="runningBatch && runningFromIdx !== idx">▶▶ ▸</el-button>
          <el-button size="small" plain @click="duplicateStep(idx)" title="复制">📋</el-button>
          <el-button type="primary" size="small" plain @click="requestRemoveStep(idx)" danger><IconTrash :size="14" style="margin-right:4px" />删除</el-button>
        </span>
      </div>

      <div v-show="expanded[idx]" class="step-form">
        <div class="step-desc">{{ availableTypes.find(t => t.value === step.type)?.desc }}</div>
        <el-form label-width="80px" size="small">
          <el-form-item label="类型">
            <el-select v-model="step.type" @change="(t) => onTypeChange(idx, t)" style="width:240px">
              <el-option-group v-for="grp in [...new Set(availableTypes.map(s => s.group))]" :key="grp" :label="grp">
                <el-option v-for="st in availableTypes.filter(s => s.group === grp)" :key="st.value" :label="st.icon + ' ' + st.label" :value="st.value" />
              </el-option-group>
            </el-select>
          </el-form-item>
          <template v-for="field in visibleFields(step)" :key="field">
            <el-form-item v-if="field === 'direction'" :label="FIELD_LABELS.direction" :required="isFieldRequired(step, field)">
              <el-select v-model="step.direction" style="width:140px"><el-option v-for="d in DIRECTION_OPTIONS" :key="d.value" :label="d.label" :value="d.value" /></el-select>
              <span class="field-hint">{{ fieldHint(step, field) }}</span>
            </el-form-item>
            <el-form-item v-else-if="field === 'distance'" :label="FIELD_LABELS.distance" :required="isFieldRequired(step, field)">
              <el-input-number v-model="step.distance" :min="50" :max="3000" :step="50" />
              <span class="field-hint">{{ fieldHint(step, field) }}</span>
            </el-form-item>
            <el-form-item v-else-if="(field === 'xpath' || field === 'xpath2') && useElementPicker(step)" :label="fieldLabel(step, field)" :required="isFieldRequired(step, field)">
              <el-select :model-value="step[field] ? step['_el_' + field]?.id || '' : ''" placeholder="搜索元素名称/ID..." filterable :filter-method="(q) => elementSearchQuery = q" clearable style="width:100%" @change="(val) => onElementPicked(step, field, val)">
                <el-option-group v-for="pg in filteredPages" :key="pg.id" :label="(pg.label || 'Page#'+pg.id) + ' (' + filteredElements.filter(e => e._pageId === pg.id).length + ')'">
                  <el-option v-for="el in filteredElements.filter(e => e._pageId === pg.id)" :key="el.id" :label="elementOptionLabel(el)" :value="el.id">
                    <div class="el-opt"><span class="el-opt-name">{{ el.alias || el.text_val || el.resource_id || '未命名' }}</span><span class="el-opt-page">{{ pg.label || 'Page#'+pg.id }}</span></div>
                  </el-option>
                </el-option-group>
              </el-select>
              <div v-if="step[field]" class="current-xpath"><code>{{ step[field] }}</code></div>
            </el-form-item>
            <el-form-item v-else-if="(field === 'xpath' || field === 'xpath2') && !useElementPicker(step)" :label="fieldLabel(step, field)" :required="isFieldRequired(step, field)">
              <el-input v-model="step[field]" placeholder="com.example.app" />
            </el-form-item>
            <el-form-item v-else-if="field === 'expected_text' || field === 'description'" :label="FIELD_LABELS[field]" :required="isFieldRequired(step, field)">
              <el-input v-model="step[field]" :placeholder="FIELD_HINTS[field] || ''" />
            </el-form-item>
            <el-form-item v-else-if="field === 'timeout' || field === 'index'" :label="fieldLabel(step, field)" :required="isFieldRequired(step, field)">
              <el-input-number v-model="step[field]" :min="0" :step="1" :precision="field === 'timeout' ? 1 : 0" />
              <span class="field-hint" v-if="fieldHint(step, field)">{{ fieldHint(step, field) }}</span>
            </el-form-item>
          </template>
          <el-form-item label="描述" v-if="!visibleFields(step).includes('description')"><el-input v-model="step.description" placeholder="步骤描述" /></el-form-item>
        </el-form>
        <div v-if="isContainer(step)" class="child-steps">
          <div class="child-steps__header">
            <span>子步骤 ({{ step.children?.length || 0 }})</span>
            <el-button size="small" @click="addChildStep(step)">+ 添加子步骤</el-button>
          </div>
          <div v-if="!step.children?.length" class="empty-state">暂无子步骤</div>
          <div v-for="(child, ci) in (step.children || [])" :key="ci" class="child-step-item">
            <span class="child-step-idx">{{ ci + 1 }}.</span>
            <span class="child-step-summary">[{{ child.type }}] {{ child.description || child.xpath || '未命名' }}</span>
            <el-button size="small" plain @click="removeChildStep(step, ci)" danger><IconTrash :size="12" /></el-button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="steps.length" style="padding: 8px 0; text-align: center">
      <el-button size="small" @click="addStep"><IconPlus :size="14" style="margin-right:4px" />添加步骤</el-button>
    </div>

    <el-dialog v-model="deleteDialog.visible" title="确认删除" width="360px">
      <p>确定删除此步骤？</p>
      <el-checkbox v-model="deleteDialog.skip">不再提示</el-checkbox>
      <template #footer><el-button @click="deleteDialog.visible = false">取消</el-button><el-button type="primary" @click="confirmRemove">确认</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.step-editor { display: flex; flex-direction: column; gap: 8px; }
.step-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 8px 0; border-bottom: 2px solid var(--case-border-subtle); }
.step-header__title { font-weight: 700; font-size: var(--app-size-sm); color: var(--ink); }
.step-header__actions { display: flex; gap: 6px; align-items: center; }
.step-item { border: 1px solid var(--case-border); border-radius: var(--app-radius-md); margin-bottom: 6px; overflow: hidden; transition: box-shadow var(--app-duration-slow), transform var(--app-duration); }
.step-item.expanded { box-shadow: var(--app-shadow-md); }
.step-item.dragging { opacity: 0.5; transform: scale(0.98); }
.step-item.drop-target { border-color: var(--c-workflow); background: var(--case-bg-drag); }
.step-bar { display: flex; align-items: center; gap: 6px; padding: var(--app-space-sm) 10px; cursor: pointer; user-select: none; transition: background var(--app-duration); }
.step-bar:hover { background: var(--case-bg-subtle); }
.drag-handle { cursor: grab; color: var(--app-text-secondary); flex-shrink: 0; }
.step-idx { font-weight: 700; font-size: var(--app-size-sm); color: var(--c-workflow); min-width: 24px; text-align: center; }
.step-summary { flex: 1; min-width: 0; font-size: var(--app-size-sm); color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.step-result-msg { font-size: var(--app-size-xs); margin-left: 6px; }
.step-result-msg.status { color: var(--case-step-success); } .step-result-msg.fail { color: var(--case-step-error); }
.step-actions { display: flex; gap: var(--app-space-xs); flex-shrink: 0; }
.step-form { padding: var(--app-space-sm) 12px 12px 36px; background: var(--case-bg-skeleton); border-top: 1px solid var(--case-bg-code); }
.step-desc { font-size: var(--app-size-xs); color: var(--app-text-secondary); margin-bottom: var(--app-space-sm); }
.field-hint { font-size: var(--app-size-xs); color: var(--app-text-secondary); margin-left: var(--app-space-sm); }
.current-xpath { margin-top: var(--app-space-xs); font-size: var(--app-size-xs); }
.current-xpath code { background: var(--case-bg-code); padding: 2px 6px; border-radius: var(--app-radius-sm); word-break: break-all; }
.el-opt { display: flex; flex-direction: column; }
.el-opt-name { font-size: var(--app-size-sm); }
.el-opt-page { font-size: var(--app-size-xs); color: var(--app-text-secondary); }
.child-steps { margin-top: var(--app-space-sm); padding: var(--app-space-sm); border: 1px dashed var(--case-border-dashed); border-radius: var(--app-radius-md); }
.child-steps__header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; font-size: var(--app-size-sm); font-weight: 600; }
.child-step-item { display: flex; align-items: center; gap: 6px; padding: 4px 0; }
.child-step-idx { font-weight: 600; color: var(--c-workflow); min-width: 24px; }
.child-step-summary { flex: 1; font-size: var(--app-size-sm); color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.empty-state { text-align: center; padding: var(--app-space-lg); color: var(--app-text-secondary); font-size: var(--app-size-sm); }
</style>
