<script setup lang="ts">
/**
 * 系统提示词全文预览：长 Markdown 在弹窗里滚动阅读，可整段复制。
 *
 * 业务：
 * - 展示：名称 + 字数/行数摘要 + 保留换行的全文（等宽字体、限高滚动）
 * - 复制：整段写入剪贴板，失败时提示手动选中
 */
import { computed, ref } from "vue"
import { ElMessage } from "element-plus"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import { copyText } from "../helpers/clipboard"

const props = defineProps<{
  modelValue: boolean
  name: string
  prompt: string
}>()

const emit = defineEmits<{ "update:modelValue": [value: boolean] }>()

/** el-dialog 的 v-model：开合权归调用方，组件只把关闭动作抛回去 */
const open = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit("update:modelValue", value),
})

const copied = ref(false)

/** 摘要：字数 + 行数，让「这是不是完整的一份」一眼可判 */
const summary = computed(() => {
  const text = props.prompt
  if (!text) return "未填写"
  return `${text.length} 字符 · ${text.split("\n").length} 行`
})

/** 关闭即复位，下次打开不会残留「已复制」 */
function onClosed(): void {
  copied.value = false
}

async function copy(): Promise<void> {
  const ok = await copyText(props.prompt)
  if (ok) {
    copied.value = true
    ElMessage.success("已复制全文")
    return
  }
  ElMessage.warning("复制失败，可在正文里手动选中")
}
</script>

<template>
  <el-dialog
    v-model="open"
    title="系统提示词"
    width="min(760px, 92vw)"
    class="ops-prompt-dialog"
    @closed="onClosed"
  >
    <div class="ops-prompt-dialog__head">
      <span class="ops-prompt-dialog__name">{{ name || "未命名配置" }}</span>
      <span class="ops-prompt-dialog__summary">{{ summary }}</span>
    </div>
    <pre v-if="prompt" class="ops-prompt-dialog__body">{{ prompt }}</pre>
    <p v-else class="ops-prompt-dialog__empty">这条配置没有填写系统提示词。</p>
    <template #footer>
      <DoodleBtn tone="paper" :disabled="!prompt" @click="copy">
        {{ copied ? "已复制" : "复制全文" }}
      </DoodleBtn>
      <DoodleBtn tone="paper" @click="open = false">关闭</DoodleBtn>
    </template>
  </el-dialog>
</template>

<style scoped>
.ops-prompt-dialog__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--app-space-sm);
  margin-bottom: var(--app-space-sm);
}

.ops-prompt-dialog__name {
  font-family: var(--app-font-mono);
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text-primary);
}

.ops-prompt-dialog__summary {
  flex: 0 0 auto;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

/* 全文区：保留换行的等宽文本，限高滚动；正文可选中，直接框选即可复制 */
.ops-prompt-dialog__body {
  margin: 0;
  padding: var(--app-space-md);
  max-height: min(56vh, 460px);
  overflow: auto;
  border: 1px solid color-mix(in srgb, var(--ink) 10%, transparent);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-subtle);
  color: var(--app-text-primary);
  font-family: var(--app-font-mono);
  font-size: var(--app-size-xs);
  line-height: var(--app-line-height-relaxed);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  user-select: text;
}

.ops-prompt-dialog__empty {
  margin: 0;
  padding: var(--app-space-md);
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
}
</style>
