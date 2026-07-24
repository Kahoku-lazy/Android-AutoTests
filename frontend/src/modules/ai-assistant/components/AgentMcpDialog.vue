<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  mode: { type: String, default: 'add' },
  mcpForm: { type: Object, required: true },
  mcpJsonError: { type: String, default: '' },
  configPreview: { type: String, default: '' },
})

const emit = defineEmits(['close', 'save'])
</script>

<template>
  <el-dialog
    :model-value="visible"
    :title="mode === 'add' ? '添加 MCP 服务器' : '编辑 MCP 服务器'"
    width="560px"
    destroy-on-close
    append-to-body
    @update:model-value="emit('close')"
  >
    <el-form label-width="80px">
      <el-form-item label="名称" required>
        <el-input v-model="mcpForm.name" placeholder="如: github" />
      </el-form-item>
      <el-form-item label="JSON 配置" required>
        <div style="width:100%">
          <el-input v-model="mcpForm.config_json" type="textarea" :rows="10"
            placeholder="粘贴 MCP 服务器配置 (JSON)"
            style="font-family:var(--app-font-mono);font-size:var(--app-size-sm)" />
          <div v-if="mcpJsonError" style="color:#e85f5f;font-size:var(--app-size-sm);margin-top:4px">{{ mcpJsonError }}</div>
          <div v-if="configPreview" class="json-preview-live" style="margin-top:8px;max-height:200px;overflow:auto;background:#1e1e1e;border-radius:8px;padding:10px;font-size:var(--app-size-sm);font-family:var(--app-font-mono);line-height:1.5">
            <pre v-html="configPreview" style="margin:0;white-space:pre-wrap;word-break:break-all"></pre>
          </div>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('close')">取消</el-button>
      <el-button type="primary" @click="emit('save')">保存</el-button>
    </template>
  </el-dialog>
</template>
