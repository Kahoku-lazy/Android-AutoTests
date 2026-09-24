<template>
  <div class="tb-cat-head">
    <div>
      <h3 class="tb-cat-title">{{ source.name }}</h3>
      <p class="tb-cat-sub">{{ source.desc }} · 始终注入运行时 · Markdown 渲染</p>
    </div>
    <div v-if="canManage" class="tb-cat-actions">
      <button type="button" class="tb-btn" @click="openHistory">查看历史记录</button>
    </div>
  </div>

  <div v-loading="loading" class="tb-cat-body">
    <el-collapse v-model="expanded" class="tb-prompt-collapse">
      <el-collapse-item v-for="role in PROMPT_ROLES" :key="role.key" :name="role.key">
        <template #title>
          <div class="tb-prompt-head">
            <span class="tb-prompt-name">{{ role.label }}</span>
            <span class="tb-prompt-key">{{ role.key }}</span>
            <span v-if="canManage" class="tb-prompt-actions" @click.stop>
              <template v-if="isEditing(role.key)">
                <button
                  type="button"
                  class="tb-btn"
                  :disabled="saving"
                  @click="cancelEdit(role.key)"
                >
                  取消
                </button>
                <button
                  type="button"
                  class="tb-btn tb-btn-primary"
                  :disabled="saving"
                  @click="save(role.key)"
                >
                  {{ saving ? "保存中…" : "保存" }}
                </button>
              </template>
              <button v-else type="button" class="tb-btn tb-btn-primary" @click="onEdit(role.key)">
                编辑
              </button>
            </span>
          </div>
        </template>
        <div v-if="isEditing(role.key)" class="tb-prompt-edit">
          <textarea
            v-model="draft[role.key]"
            class="tb-prompt-textarea"
            rows="12"
            :placeholder="`${role.label} Markdown`"
          />
          <article class="tb-prompt-md tb-prompt-preview" v-html="renderMd(draft[role.key])" />
        </div>
        <article v-else class="tb-prompt-md" v-html="renderMd(prompts[role.key])" />
      </el-collapse-item>
    </el-collapse>
  </div>

  <DevicePromptHistoryDrawer
    v-model="historyVisible"
    :archives="archives"
    :loading="archivesLoading"
    :preview="preview"
    @preview="previewArchive"
    @restore="restoreArchive"
    @remove="removePermanentArchive"
  />
</template>

<script setup lang="ts">
/** DevicePromptPanel — 设备提示词来源区：三份提示词各自独立编辑 / 保存 + 历史存档抽屉 */
import { ref, onBeforeUnmount } from "vue"
import DevicePromptHistoryDrawer from "./DevicePromptHistoryDrawer.vue"
import { useDevicePrompts } from "../composables/useDevicePrompts"
import { renderSkillMarkdown } from "../helpers/skill-markdown"
import { sourceDef } from "../helpers/toolbox-assembly"
import { PROMPT_ROLES } from "../constants"
import type { PromptRole } from "../constants"

defineProps<{ canManage?: boolean }>()

const source = sourceDef("prompt")

const {
  prompts,
  draft,
  loading,
  saving,
  isEditing,
  startEdit,
  cancelEdit,
  save,
  autoSaveIfDirty,
  archives,
  archivesLoading,
  historyVisible,
  preview,
  openHistory,
  previewArchive,
  restoreArchive,
  removePermanentArchive,
} = useDevicePrompts()

/** 默认只展开规划；进入某份编辑只展开该份，不牵动其余份的展开状态 */
const expanded = ref<PromptRole[]>(["planner"])

function onEdit(role: PromptRole): void {
  startEdit(role)
  if (!expanded.value.includes(role)) expanded.value = [...expanded.value, role]
}

/** 卸载 = 离开设备提示词来源或离开页面：编辑中且有改动的份先自动落库 */
onBeforeUnmount(() => {
  void autoSaveIfDirty()
})

function renderMd(src: string): string {
  return renderSkillMarkdown(src || "_（空）_")
}
</script>

<style src="./DevicePromptPanel.style.css" scoped></style>
