<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { formatApiError } from "@/shared/api-client"
import {
  avatarUrl,
  createAssistant,
  deleteAssistant,
  listRoleOptions,
  listToolCatalog,
  updateAssistant,
} from "../api/assistants"
import { blankForm, formFromCard, toToolSelection, type EditorForm } from "../helpers/editor-form"
import { assistantInUseMessage, workflowsUsingAssistant } from "../helpers/assistant-usage"
import { markerVars } from "../helpers/marker"
import type { AssistantCard, RoleOption, SopWorkflow, ToolCatalogDomain } from "../types"

const props = defineProps<{ card?: AssistantCard | null; workflows?: SopWorkflow[] }>()
const emit = defineEmits<{ close: []; saved: []; deleted: [] }>()

const form = ref<EditorForm>(props.card ? formFromCard(props.card) : blankForm())
const roles = ref<RoleOption[]>([])
const catalog = ref<ToolCatalogDomain[]>([])
const avatar = ref<File | null>(null)
const clearAvatar = ref(false)
const existingAvatar = ref("")
const pickedUrl = ref("")
const saving = ref(false)
const deleting = ref(false)
const error = ref("")

const editing = computed(() => Boolean(props.card))
const preview = computed(() => pickedUrl.value || (clearAvatar.value ? "" : existingAvatar.value))
const swatchVars = computed(() => markerVars(props.card?.marker || "teal"))

const avatarHint = computed(() =>
  editing.value ? "不上传就显示该助手的笔色渐变圆" : "不上传就显示创建时分配的笔色渐变圆",
)

onMounted(async () => {
  const [roleList, toolCatalog] = await Promise.all([listRoleOptions(), listToolCatalog()])
  roles.value = roleList
  catalog.value = toolCatalog
  if (props.card?.has_avatar && !clearAvatar.value) {
    existingAvatar.value = await avatarUrl(props.card.assistant_id)
  }
})

onUnmounted(() => {
  if (pickedUrl.value) URL.revokeObjectURL(pickedUrl.value)
})

function onFile(event: Event): void {
  const file = (event.target as HTMLInputElement).files?.[0] || null
  if (pickedUrl.value) URL.revokeObjectURL(pickedUrl.value)
  avatar.value = file
  clearAvatar.value = false
  pickedUrl.value = file ? URL.createObjectURL(file) : ""
}

function removeAvatar(): void {
  if (pickedUrl.value) URL.revokeObjectURL(pickedUrl.value)
  pickedUrl.value = ""
  avatar.value = null
  clearAvatar.value = true
  existingAvatar.value = ""
}

async function remove(): Promise<void> {
  if (!props.card) return
  const usedBy = workflowsUsingAssistant(props.card.assistant_id, props.workflows || [])
  if (usedBy.length) {
    error.value = assistantInUseMessage(usedBy)
    ElMessage.warning(error.value)
    return
  }
  try {
    await ElMessageBox.confirm(
      `删除「${props.card.display_name}」？名片从列表消失，已有的对话记录与历史任务不受影响。`,
      "删除助手",
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
    await deleteAssistant(props.card.assistant_id)
    ElMessage.success("助手已删除")
    emit("deleted")
  } catch (e) {
    error.value = formatApiError(e as never, "删除失败")
  } finally {
    deleting.value = false
  }
}

async function save(): Promise<void> {
  error.value = ""
  const displayName = form.value.displayName.trim()
  if (!displayName) {
    error.value = "给助手起个名字"
    return
  }
  if (!form.value.roleId) {
    error.value = "先选一条 Agent 配置"
    return
  }
  saving.value = true
  const base = {
    display_name: displayName,
    role_id: form.value.roleId,
    tools: toToolSelection(form.value),
  }
  try {
    if (props.card) {
      await updateAssistant(props.card.assistant_id, {
        ...base,
        revision: props.card.revision,
        avatar: avatar.value,
        clearAvatar: clearAvatar.value,
      })
    } else {
      await createAssistant({ ...base, avatar: avatar.value })
    }
    emit("saved")
  } catch (e) {
    const raw = e as { message?: string }
    error.value = raw.message || formatApiError(e as never, "保存失败")
    ElMessage.error(error.value)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="assistant-editor">
    <div class="assistant-field">
      <span class="assistant-field__label">头像</span>
      <div class="assistant-avatar">
        <img v-if="preview" class="assistant-avatar__img" :src="preview" alt="" />
        <span v-else class="assistant-avatar__dot" :style="swatchVars" aria-hidden="true" />
        <div class="assistant-avatar__side">
          <div class="assistant-avatar__row">
            <label class="assistant-avatar__pick">
              <input class="assistant-avatar__file" type="file" accept="image/*" @change="onFile" />
              <span>{{ preview ? "换一张" : "选择图片" }}</span>
            </label>
            <button
              v-if="preview"
              type="button"
              class="assistant-avatar__remove"
              @click="removeAvatar"
            >
              移除
            </button>
          </div>
          <p class="assistant-avatar__hint">{{ avatarHint }}</p>
        </div>
      </div>
    </div>

    <label class="assistant-field">
      <span class="assistant-field__label">名称</span>
      <input v-model="form.displayName" class="assistant-input" placeholder="给这位助手起个名字" />
    </label>

    <label class="assistant-field">
      <span class="assistant-field__label">Agent 配置</span>
      <span class="assistant-select">
        <select v-model="form.roleId" class="assistant-input">
          <option value="">请选择</option>
          <option v-for="role in roles" :key="role.role_id" :value="role.role_id">
            {{ role.name }}
          </option>
        </select>
      </span>
    </label>

    <label class="assistant-field">
      <span class="assistant-field__label">工具域</span>
      <span class="assistant-select">
        <select v-model="form.domain" class="assistant-input">
          <option value="">不挂工具</option>
          <option v-for="item in catalog" :key="item.domain" :value="item.domain">
            {{ item.label }}
          </option>
        </select>
      </span>
    </label>

    <label v-if="form.domain" class="assistant-field">
      <span class="assistant-field__label">预设</span>
      <span class="assistant-select">
        <select v-model="form.preset" class="assistant-input">
          <option value="all">全部</option>
          <option value="readonly">只读</option>
        </select>
      </span>
    </label>

    <p v-if="error" class="assistant-editor__error">{{ error }}</p>

    <div class="assistant-editor__actions">
      <DoodleBtn v-if="editing" tone="danger" :disabled="deleting" @click="remove">删除</DoodleBtn>
      <span class="assistant-editor__spacer" />
      <DoodleBtn tone="paper" @click="emit('close')">取消</DoodleBtn>
      <DoodleBtn tone="yellow" :disabled="saving" @click="save">{{
        editing ? "保存" : "创建"
      }}</DoodleBtn>
    </div>
  </div>
</template>

<style scoped>
.assistant-editor {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}

.assistant-editor__error {
  margin: 0;
  color: var(--app-status-danger-text);
  font-size: var(--app-size-sm);
}

.assistant-editor__actions {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  padding-top: var(--app-space-sm);
}

.assistant-editor__spacer {
  flex: 1;
}

.assistant-avatar {
  display: flex;
  align-items: center;
  gap: var(--app-space-md);
}

.assistant-avatar__img,
.assistant-avatar__dot {
  flex: none;
  width: 64px;
  height: 64px;
  border: 2px solid var(--ink);
  border-radius: 50%;
}

.assistant-avatar__img {
  object-fit: cover;
}

.assistant-avatar__dot {
  background: linear-gradient(
    165deg,
    var(--assistant-marker) 0%,
    color-mix(in srgb, var(--assistant-marker) 34%, var(--paper)) 100%
  );
}

.assistant-avatar__side {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
  min-width: 0;
}

.assistant-avatar__row {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
}

.assistant-avatar__pick,
.assistant-avatar__remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 0 var(--app-space-md);
  border: 2px solid var(--ink);
  border-radius: 2px;
  background: var(--paper);
  color: var(--ink);
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-heavy);
  cursor: pointer;
}

.assistant-avatar__pick:hover,
.assistant-avatar__remove:hover {
  background: var(--app-highlight);
}

.assistant-avatar__pick:focus-within,
.assistant-avatar__remove:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 2px;
}

.assistant-avatar__file {
  display: none;
}

.assistant-avatar__hint {
  margin: 0;
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
}
</style>
