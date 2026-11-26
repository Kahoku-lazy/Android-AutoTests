<script setup lang="ts">
import { reactive, watch } from "vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { KS_MODULE_DIALOG_TITLE } from "../constants"
import type { KnowledgeModuleRow, ModulePayload } from "../types"

const props = defineProps<{ editing: KnowledgeModuleRow | null }>()
const visible = defineModel<boolean>({ required: true })
const emit = defineEmits<{ save: [payload: ModulePayload, id?: number] }>()

const form = reactive<ModulePayload>({ name: "", description: "", data_dir: "", enabled: true })

watch(visible, (open) => {
  if (!open) return
  form.name = props.editing?.name ?? ""
  form.description = props.editing?.description ?? ""
  form.data_dir = props.editing?.data_dir ?? ""
  form.enabled = props.editing?.enabled ?? true
})

function onSubmit() {
  emit("save", { ...form }, props.editing?.id)
}
</script>

<template>
  <el-dialog v-model="visible" :title="KS_MODULE_DIALOG_TITLE" width="520px" append-to-body>
    <el-form label-width="88px" label-position="left">
      <el-form-item label="库名" required>
        <el-input
          v-model="form.name"
          placeholder="小写字母开头，如 product_manuals"
          maxlength="64"
        />
      </el-form-item>
      <el-form-item label="说明" required>
        <el-input v-model="form.description" placeholder="这个模块里是什么资料" maxlength="200" />
      </el-form-item>
      <el-form-item label="资料目录" required>
        <el-input
          v-model="form.data_dir"
          placeholder="服务器本地绝对路径，如 D:\docs\manuals"
          maxlength="500"
        />
      </el-form-item>
      <el-form-item label="启用">
        <el-switch v-model="form.enabled" />
      </el-form-item>
    </el-form>
    <p class="ks-form__hint">只索引目录下的 .md / .txt 文件；目录只读，平台不会改动其中文件。</p>
    <template #footer>
      <DoodleBtn @click="visible = false">取消</DoodleBtn>
      <DoodleBtn tone="teal" @click="onSubmit">保存</DoodleBtn>
    </template>
  </el-dialog>
</template>

<style scoped>
.ks-form__hint {
  margin: 0;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
</style>
