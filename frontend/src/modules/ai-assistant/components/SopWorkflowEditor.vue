<script setup lang="ts">
/**
 * 工作流配置表单：名称 + 执行助手 + 验收助手。
 *
 * 只出表单本体，弹窗外壳由 `SopWorkflowSection.vue` 的 el-dialog 提供。
 * 传入 `workflow` 即编辑：字段预填，保存走 PATCH 回写同一条记录，并可删除。
 */
import { computed, ref } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { formatApiError } from "@/shared/api-client"
import { createSopWorkflow, deleteSopWorkflow, updateSopWorkflow } from "../api/assistants"
import { sopCreateError } from "../helpers/sop-form"
import type { AssistantCard, SopWorkflow } from "../types"

const props = defineProps<{ workflow?: SopWorkflow | null; cards: AssistantCard[] }>()
const emit = defineEmits<{ close: []; saved: []; deleted: [] }>()

const name = ref(props.workflow?.name || "")
const executorId = ref(props.workflow?.executor_assistant_id || "")
const verifierId = ref(props.workflow?.verifier_assistant_id || "")
const saving = ref(false)
const deleting = ref(false)
const error = ref("")

const editing = computed(() => Boolean(props.workflow))
const noCards = computed(() => props.cards.length === 0)
const options = computed(() =>
  props.cards.map((card) => ({ id: card.assistant_id, label: card.display_name })),
)

/** 新建走 POST，编辑走 PATCH；两处共用同一份字段与校验。 */
async function save(): Promise<void> {
  error.value = sopCreateError({
    name: name.value,
    executorId: executorId.value,
    verifierId: verifierId.value,
  })
  if (error.value || noCards.value) return
  saving.value = true
  try {
    const payload = {
      name: name.value.trim(),
      executor_assistant_id: executorId.value,
      verifier_assistant_id: verifierId.value,
    }
    if (props.workflow) {
      await updateSopWorkflow(props.workflow.id, payload)
      ElMessage.success("工作流已保存")
    } else {
      await createSopWorkflow(payload)
      ElMessage.success("工作流已创建")
    }
    emit("saved")
  } catch (e) {
    error.value = formatApiError(e as never, "保存失败")
  } finally {
    saving.value = false
  }
}

/** 删除前二次确认：只说清影响面，历史任务不受影响。 */
async function remove(): Promise<void> {
  if (!props.workflow) return
  try {
    await ElMessageBox.confirm(
      "删除后这条工作流不再出现在卡片里，已提交的任务不受影响。",
      "删除工作流",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消",
      },
    )
  } catch {
    return
  }
  deleting.value = true
  try {
    await deleteSopWorkflow(props.workflow.id)
    ElMessage.success("工作流已删除")
    emit("deleted")
  } catch (e) {
    error.value = formatApiError(e as never, "删除失败")
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="sop-editor">
    <p v-if="noCards" class="sop-editor__hint">还没有助手，先新建助手再登记工作流。</p>

    <label class="assistant-field">
      <span class="assistant-field__label">名称</span>
      <input
        v-model="name"
        class="assistant-input"
        maxlength="200"
        placeholder="给这条工作流起个名字"
      />
    </label>

    <label class="assistant-field">
      <span class="assistant-field__label">执行助手</span>
      <span class="assistant-select">
        <select v-model="executorId" class="assistant-input">
          <option value="">请选择</option>
          <option v-for="item in options" :key="`executor-${item.id}`" :value="item.id">
            {{ item.label }}
          </option>
        </select>
      </span>
    </label>

    <label class="assistant-field">
      <span class="assistant-field__label">验收助手</span>
      <span class="assistant-select">
        <select v-model="verifierId" class="assistant-input">
          <option value="">请选择</option>
          <option v-for="item in options" :key="`verifier-${item.id}`" :value="item.id">
            {{ item.label }}
          </option>
        </select>
      </span>
    </label>

    <p v-if="error" class="sop-editor__error">{{ error }}</p>

    <div class="sop-editor__actions">
      <DoodleBtn v-if="editing" tone="danger" :disabled="deleting" @click="remove">删除</DoodleBtn>
      <span class="sop-editor__spacer" />
      <DoodleBtn tone="paper" @click="emit('close')">取消</DoodleBtn>
      <DoodleBtn tone="yellow" :disabled="saving || noCards" @click="save">{{
        editing ? "保存" : "创建"
      }}</DoodleBtn>
    </div>
  </div>
</template>

<style scoped>
.sop-editor {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}

.sop-editor__hint,
.sop-editor__error {
  margin: 0;
  font-size: var(--app-size-sm);
}

.sop-editor__hint {
  color: var(--app-text-secondary);
}

.sop-editor__error {
  color: var(--app-status-danger-text);
}

.sop-editor__actions {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  padding-top: var(--app-space-sm);
}

/* 删除靠左，取消与保存靠右：删除不与保存相邻，避免误点 */
.sop-editor__spacer {
  flex: 1;
}
</style>
